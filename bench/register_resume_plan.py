"""Register the user-approved scheduling revision; preserve responses and budget."""
from copy import deepcopy
import json
from harness_common import BENCH, read_json, digest, write_json
from freeze import verify as frozen_verify
from run_plan import IMPLEMENTATION, verify


def register(root=BENCH):
    archive=root/'plans/v1-run-2'
    old=read_json(archive/'RUN_PLAN.json'); sha=digest((archive/'RUN_PLAN.json').read_bytes())
    if sha!='69fd7e8374a2bbaf09e43e26c0b280b05fefbd6e4a7141bf76baa845761bb4fb' or digest((root/'RUN_PLAN.json').read_bytes())!=sha:
        raise ValueError('only the archived run-2 may be revised once')
    if (root/'runs/API_ACTIVE.lock').exists(): raise ValueError('stop API process before revision')
    if frozen_verify(root)['frozen_md_sha256']!=old['frozen_md_sha256']: raise ValueError('frozen data changed')
    for name,expected in old['implementation'].items():
        if digest((archive/'implementation'/name).read_bytes())!=expected: raise ValueError('parent implementation changed')
    ledger=root/'runs'/('api_ledger_'+sha[:16]+'.json'); state=read_json(ledger)
    if state['calls']!=len(state['slots']) or len(set(state['slots']))!=state['calls']: raise ValueError('ledger identity invalid')
    sources=[]
    for path in sorted((root/'runs').glob('*/records.jsonl')):
        rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
        if any(r.get('mode')=='api' and r.get('plan_sha256')==sha for r in rows):
            sources.append({'path':path.relative_to(root).as_posix(),'sha256':digest(path.read_bytes())})
    plan=deepcopy(old)
    plan.update({'version':'v1-run-3','parent_plan_sha256':sha,
        'api_schedule':[['deepseek-flash','C'],['qwen3.8-27b','C'],['kimi-k3','B'],['kimi-k3','C'],['deepseek-flash','B'],['qwen3.8-27b','B']],
        'resume_sources':sources,
        'scheduling_revision':'User approved DeepSeek/Qwen C priority after Kimi 300s timeouts. Same public requests/parameters; resume unique slots; reserved interruption retained as error, never resent.',
        'prior_ledger':{'path':ledger.relative_to(root).as_posix(),'sha256':digest(ledger.read_bytes()),'calls':state['calls'],'reserved_cny':state['reserved_cny']},
        'implementation':{n:digest((root/n).read_bytes()) for n in IMPLEMENTATION}})
    # Keep the run-2 slot namespace: inherited reservations cannot be bypassed.
    write_json(root/'RUN_PLAN.json',plan); newsha=digest((root/'RUN_PLAN.json').read_bytes())
    (root/'RUN_PLAN.sha256').write_bytes((newsha+'\n').encode('ascii'))
    approved=read_json(archive/'API_APPROVAL.json');approved['plan_sha256']=newsha
    approved['scheduling_approval_quote']='优先完成 DeepSeek/Qwen 的 C 组（推荐）'
    approved['authorization_carried_forward']='Same models, inputs, parameters, repetitions and cumulative 576 requests/CNY270 including all previous reservations. Preserve run-2 responses; only schedule and resumability changed.'
    write_json(root/'API_APPROVAL.json',approved)
    return verify(root)


if __name__=='__main__':
    result=register();print('Registered '+result['plan']['version']+'; SHA-256 '+result['plan_sha256'])
