"""Seal API-only provenance/usage receipt. No expected answers or QC scoring."""
from collections import Counter
import json

from harness_common import BENCH, read_json, digest, write_json
from run_plan import verify
from resume_api import collect


def api_paths(root, paths, allowed):
    return [p for p in paths if any(r.get('mode')=='api' and r.get('plan_sha256') in allowed
            for r in (json.loads(line) for line in (root/p).read_text(encoding='utf-8').splitlines()))]


def seal(root=BENCH):
    if (root/'runs/API_ACTIVE.lock').exists(): raise ValueError('API process still active; receipt cannot be sealed')
    locked=verify(root);plan=locked['plan'];attempts,observations,paths=collect(root,locked)
    wanted={(m['name'],g,c['case_id'],i) for m in plan['models'] for g in ('B','C') for c in plan['cases'] for i in range(1,4)}
    if not set(observations)<=wanted: raise ValueError('unplanned observations')
    sources=api_paths(root,paths,{locked['plan_sha256'],plan['parent_plan_sha256']})
    ledger=read_json(root/'runs'/('api_ledger_'+locked['plan_sha256'][:16]+'.json'))
    groups=[]
    for model in plan['models']:
        for group in ('B','C'):
            obs=[v for k,v in observations.items() if k[:2]==(model['name'],group)]
            calls=[v for k,v in attempts.items() if k[:2]==(model['name'],group)]
            usage=[r for r in calls if isinstance(r.get('usage'),dict)]
            initial=[r for r in calls if r['attempt']==0]
            known_initial=[r for r in initial if isinstance(r.get('usage'),dict) and 'prompt_tokens' in r['usage']]
            inp=sum(r['usage'].get('prompt_tokens',0) for r in usage);out=sum(r['usage'].get('completion_tokens',0) for r in usage)
            groups.append({'model':model['name'],'group':group,'planned_observations':48,'observations':len(obs),
                'status_counts':dict(Counter(r['status'] for r in obs)), 'reserved_attempt_records':len(calls),
                'interrupted_attempts':sum(r.get('completion_source')=='interrupted_reservation_reconciled' for r in calls),
                'format_repair_calls':sum(r['attempt']>0 for r in calls),'usage_available_calls':len(usage),
                'usage_missing_calls':len(calls)-len(usage),'known_input_tokens':inp,'known_output_tokens':out,
                'average_initial_input_tokens_known':sum(r['usage']['prompt_tokens'] for r in known_initial)/len(known_initial) if known_initial else None,
                'average_initial_input_proxy':sum(r['request_summary']['input_estimate']['proxy'] for r in initial)/len(initial) if initial else None,
                'uncached_peak_cost_estimate_cny':(inp*model['input_cny_per_million']+out*model['output_cny_per_million'])/1e6 if usage else None})
    receipt={'format':1,'result_version':'v1-api-receipt-1','receipt_implementation_sha256':digest((root/'seal_api.py').read_bytes()),'plan_sha256':locked['plan_sha256'],
        'frozen_md_sha256':locked['frozen_md_sha256'],'compatible_parent_plan_sha256':plan['parent_plan_sha256'],
        'complete':set(observations)==wanted,'planned_observations':len(wanted),'observations':len(observations),
        'missing_slots':[list(k) for k in sorted(wanted-set(observations))],
        'records':{p:digest((root/p).read_bytes()) for p in sources},'groups':groups,
        'global_reserved_calls':ledger['calls'],'global_reserved_cny_not_billing':ledger['reserved_cny'],
        'global_ledger_sha256':digest((root/'runs'/('api_ledger_'+locked['plan_sha256'][:16]+'.json')).read_bytes()),
        'infrastructure_only_prior_run':'TRANSPORT_RUN1.json','actual_account_deduction_cny':None,
        'note':'Protocol/usage only. Costs use approved uncached peak prices, not account deductions. Missing provider usage is unknown. No accuracy, root-cause, danger or H1-H3 scoring.'}
    write_json(root/'API_RECEIPT.json',receipt)
    original=root/'API_RUNS.json'
    if original.exists():
        archive=root/'runs/API_RUNS.unsealed.json'
        if not archive.exists(): archive.write_bytes(original.read_bytes())
    write_json(original,{'mode':'api','sealed':True,'plan_sha256':locked['plan_sha256'],
        'compatible_parent_plan_sha256':plan['parent_plan_sha256'],'runs':sorted({str(__import__('pathlib').Path(p).parent.as_posix()) for p in sources}),
        'observations':len(observations),'complete':receipt['complete'],'receipt':'API_RECEIPT.json'})
    return receipt


if __name__=='__main__':
    r=seal();print(f'SEALED: {r["observations"]}/{r["planned_observations"]}; global reserved {r["global_reserved_calls"]}')
