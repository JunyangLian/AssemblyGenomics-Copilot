"""Resume compatible public requests without repeating completed/reserved slots."""
from __future__ import annotations

import json

from harness_common import BENCH, canonical, digest, read_json, request, summary, write_json
from model_adapter import Budget, OpenAICompatible, approval, exclusive_api_run
from run_plan import verify
from run import observe, run_id


def identity(row):
    return row['model'], row['group'], row['case_id'], row['repetition']


def collect(root, locked):
    """Validate inherited bytes and public request identities; never read answers."""
    spec=locked['plan']; inherited=spec['resume_sources']
    for item in inherited:
        path=root/item['path']
        if digest(path.read_bytes())!=item['sha256']:
            raise ValueError('inherited API records changed: '+item['path'])
    allowed={locked['plan_sha256'],spec['parent_plan_sha256']}
    paths={item['path'] for item in inherited}
    for path in (root/'runs').glob('*/records.jsonl'):
        if any(json.loads(line).get('plan_sha256')==locked['plan_sha256'] for line in path.read_text(encoding='utf-8').splitlines()):
            paths.add(path.relative_to(root).as_posix())
    models={m['name']:m for m in spec['models']}
    attempts={}; observations={}
    for name in sorted(paths):
        for line in (root/name).read_text(encoding='utf-8').splitlines():
            row=json.loads(line)
            if row.get('mode')!='api' or row.get('plan_sha256') not in allowed: continue
            key=identity(row)
            if key[0] not in models or key[1] not in ('B','C') or key[2] not in {c['case_id'] for c in spec['cases']} or key[3] not in range(1,4):
                raise ValueError('API record outside planned slots')
            body=request(root/'cases'/key[2],key[1],models[key[0]],root,retry=row['attempt']>0)
            if row['request_summary']!=summary(root/'cases'/key[2],body,root):
                raise ValueError('inherited public request differs')
            mapping=attempts if row['record_type']=='attempt' else observations
            index=key+(row['attempt'],) if row['record_type']=='attempt' else key
            if index in mapping: raise ValueError('duplicate API slot')
            mapping[index]=row
    return attempts,observations,sorted(paths)


def decision(key, attempts, observations, budget):
    """Return next permitted attempt or reconciliation; no HTTP/network retries."""
    if key in observations: return 'done',None
    previous=[attempts[key+(i,)] for i in (0,1) if key+(i,) in attempts]
    if previous and (previous[-1]['status']!='parse_error' or previous[-1]['attempt']==1):
        return 'finalize',previous[-1]
    next_attempt=previous[-1]['attempt']+1 if previous else 0
    slot=':'.join(map(str,key+(next_attempt,)))
    ns=budget.locked['plan'].get('slot_namespace')
    if (ns+':'+slot if ns else slot) in budget.state['slots']:
        return 'interrupted',next_attempt
    return 'send',next_attempt


def execute(root=BENCH):
    locked=verify(root); approval(root,locked)
    with exclusive_api_run(root):
        budget=Budget(root,locked)
        attempts,observations,paths=collect(root,locked)
        models={m['name']:m for m in locked['plan']['models']}
        for name,group in locked['plan']['api_schedule']:
            model=models[name]; client=None
            rid=run_id(name,group,locked['frozen_md_sha256'])
            directory=root/'runs'/rid; directory.mkdir(parents=True)
            emitted=0
            with (directory/'records.jsonl').open('xb') as stream:
                def emit(row):
                    nonlocal emitted
                    row['run_id']=rid
                    stream.write(canonical(row)); stream.flush(); emitted+=1
                    key=identity(row)
                    if row['record_type']=='attempt': attempts[key+(row['attempt'],)]=row
                    else: observations[key]=row
                for case_info in locked['plan']['cases']:
                    case=root/'cases'/case_info['case_id']
                    for repeat in range(1,4):
                        key=(name,group,case.name,repeat)
                        choice,value=decision(key,attempts,observations,budget)
                        if choice=='done': continue
                        if choice=='send':
                            if client is None: client=OpenAICompatible(model,budget)
                            observe(case,group,model,client,repeat,locked,emit,root,start_attempt=value)
                        else:
                            if choice=='interrupted':
                                body=request(case,group,model,root,retry=value>0)
                                row={'record_type':'attempt','case_id':case.name,'repetition':repeat,'attempt':value,
                                    'group':group,'model':name,'mode':'api','plan_sha256':locked['plan_sha256'],
                                    'frozen_md_sha256':locked['frozen_md_sha256'],'request_summary':summary(case,body,root),
                                    'response':None,'parsed':None,'status':'api_error',
                                    'error':'interrupted reserved request; provider completion/usage unknown; not resent',
                                    'usage':None,'usage_source':'unavailable','elapsed_seconds':None,'retry':value>0,
                                    'completion_source':'interrupted_reservation_reconciled','effective_parameters':None}
                                emit(row)
                            else: row=value
                            emit({**row,'record_type':'observation','attempts':row['attempt']+1,
                                  'plan_sha256':locked['plan_sha256'],'reconciled':True})
            if emitted: paths.append((directory/'records.jsonl').relative_to(root).as_posix())
            write_json(directory/'summary.json',{'group':group,'model':name,'logical_observations':sum(k[:2]==(name,group) for k in observations),'new_records':emitted})
            print(f'api {group} {name}: {sum(k[:2]==(name,group) for k in observations)}/48 observations',flush=True)
            write_json(root/'API_RUNS.json',{'mode':'api','plan_sha256':locked['plan_sha256'],
                'compatible_parent_plan_sha256':locked['plan']['parent_plan_sha256'],
                'runs':sorted({str(__import__('pathlib').Path(p).parent.as_posix()) for p in paths}),
                'complete':len(observations)==288,'observations':len(observations)})
    return paths


if __name__=='__main__': execute()
