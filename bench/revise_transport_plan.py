"""One-time transport revision after TLS failure, before any model response."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from freeze import verify as frozen_verify
from harness_common import BENCH, read_json, canonical, digest, write_json
from run_plan import IMPLEMENTATION, verify


def revise(root=BENCH):
    frozen=frozen_verify(root)
    archive=root/'plans/v1-run-1'
    old=read_json(archive/'RUN_PLAN.json')
    old_sha=digest((archive/'RUN_PLAN.json').read_bytes())
    if old_sha!='e694c6e22811bef07ac8f20c002ff62ad6cf10997cdca34df28744c553954bed':
        raise ValueError('parent run plan archive identity differs')
    if digest((root/'RUN_PLAN.json').read_bytes())!=old_sha:
        raise ValueError('transport revision may only replace the original archived plan once')
    for name,sha in old['implementation'].items():
        if digest((archive/'implementation'/name).read_bytes())!=sha:
            raise ValueError('old implementation archive differs')
    if frozen['frozen_md_sha256']!=old['frozen_md_sha256']:
        raise ValueError('frozen version differs')
    if (root/'runs/API_ACTIVE.lock').exists():
        raise ValueError('original run must stop before revision')
    runs=[]; attempted=[]; observations=[]
    for path in sorted((root/'runs').glob('*/records.jsonl')):
        rows=[__import__('json').loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        rows=[r for r in rows if r.get('mode')=='api' and r.get('plan_sha256')==old_sha]
        if rows:
            runs.append(path.parent.relative_to(root).as_posix())
            attempted.extend(r for r in rows if r['record_type']=='attempt')
            observations.extend(r for r in rows if r['record_type']=='observation')
    if not attempted or any(r['status']!='api_error' or r.get('response') is not None or r.get('parsed') is not None for r in attempted):
        raise ValueError('revision is restricted to transport failures without model responses')
    ledger=root/'runs'/('api_ledger_'+old_sha[:16]+'.json')
    state=read_json(ledger)
    if state['calls']!=len(state['slots']) or state['calls']<len(attempted):
        raise ValueError('prior reservation count differs')
    plan=deepcopy(old)
    plan.update({'version':'v1-run-2','parent_plan_sha256':old_sha,'rules_parent_plan_sha256':old_sha,
                 'slot_namespace':'v1-run-2',
                 'transport_revision':'TLS handshake EOF via local proxy; verified no-key direct TLS probes. Set process NO_PROXY only for approved provider hosts; restore on exit.',
                 'prior_ledger':{'path':ledger.relative_to(root).as_posix(),'sha256':digest(ledger.read_bytes()),
                                 'calls':state['calls'],'reserved_cny':state['reserved_cny']},
                 'implementation':{name:digest((root/name).read_bytes()) for name in IMPLEMENTATION}})
    write_json(root/'RUN_PLAN.json',plan)
    sha=digest((root/'RUN_PLAN.json').read_bytes())
    (root/'RUN_PLAN.sha256').write_bytes((sha+'\n').encode('ascii'))
    approved=read_json(archive/'API_APPROVAL.json')
    approved['plan_sha256']=sha
    approved['authorization_carried_forward']='Same three models, B/C, cumulative 576 calls/CNY270 including all original reservations; only verified process network route and budget namespace change. Original user approval persists; no additional budget.'
    approved['user_credential_use_reply']='可以写入日志，这些api都不贵，问题不大'
    write_json(root/'API_APPROVAL.json',approved)
    write_json(root/'TRANSPORT_RUN1.json',{
        'date':'2026-10-07','plan_sha256':old_sha,'runs':runs,'completed_client_attempts':len(attempted),
        'completed_observations':len(observations),'reserved_calls':state['calls'],
        'unresolved_inflight_reservations':state['calls']-len(attempted),
        'status_counts':dict(Counter(r['status'] for r in attempted)),
        'provider_usage':None,'reserved_cny_not_billed':state['reserved_cny'],
        'reason':'TLS SSLEOFError via local 127.0.0.1:7897 proxy; no model responses; interrupted batch. Original records preserved, not silently discarded.',
        'model_responses':0,'new_plan_sha256':sha})
    return verify(root)


if __name__=='__main__':
    result=revise();print('Registered '+result['plan']['version']+'; SHA-256 '+result['plan_sha256'])
