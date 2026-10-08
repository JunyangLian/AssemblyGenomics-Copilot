"""Third credential, four active models, two deferred with every record retained."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from collections import Counter
import json
from bench.v2.runtime import V2,read_json,write_json,digest,canonical,request,token_estimate
from bench.v2.credential_recovery import eligible,slot

QUOTE='先不跑kimi和glm了，先把剩下的4个先跑完，kimi和glm先保存着记录'


def register(root=V2,parent_version='v2-run-8',credential_ordinal=3):
    from bench.v2.freeze import verify as frozen_verify
    from bench.v2.plan import verify
    frozen_verify(root)
    configurations={3:('v2-run-8','v2-run-9',271,376,1578,'THIRD','PRIORITY_FOUR_REVISION.json','PREREGISTRATION_AMENDMENT_PRIORITY_20261008.md'),
        4:('v2-run-9','v2-run-10',38,609,1911,'FOURTH','PRIORITY_FOUR_CREDENTIAL4.json','PREREGISTRATION_AMENDMENT_FOURTH_20261008.md')}
    if credential_ordinal not in configurations or parent_version!=configurations[credential_ordinal][0]:
        raise ValueError('unregistered human credential continuation')
    parent_version,new_version,expected_recovery,expected_observed,expected_calls,label,priority_file,appendix=configurations[credential_ordinal]
    history=root/'history'/parent_version
    parent_sha=digest((history/'RUN_PLAN.json').read_bytes())
    if digest((root/'RUN_PLAN.json').read_bytes()) != parent_sha:
        raise ValueError('unexpected third credential parent')
    old=read_json(history/'RUN_PLAN.json')
    source=[json.loads(line) for line in (history/'resume_records.jsonl').read_text(encoding='utf-8').splitlines()]
    original_path=root/'history/v2-run-7/resume_records.jsonl'
    original=[json.loads(line) for line in original_path.read_text(encoding='utf-8').splitlines()]
    observed={slot(r) for r in source if r['record_type']=='observation'}
    previous429=eligible(original); latest429=eligible(source)
    deferred=['GLM-5.3','Kimi-K2.6']
    active=[m['name'] for m in old['models'] if m['name'] not in deferred]
    selected={k:r for k,r in previous429.items() if k not in observed and k[0] in active}
    selected.update({k:r for k,r in latest429.items() if k[0] in active})
    if len(selected)!=expected_recovery or len(observed)!=expected_observed:raise ValueError('reviewed priority scope changed')
    rank={m['name']:i for i,m in enumerate(old['models'])};cases={c['case_id']:i for i,c in enumerate(old['cases'])}
    models={m['name']:m for m in old['models']};slots=[]
    for key in sorted(selected,key=lambda s:(rank[s[0]],old['groups'].index(s[1]),cases[s[2]],s[3])):
        model,group,case,rep=key
        versions=(['v2-run-7',parent_version] if key in latest429 and key in previous429
                  else [parent_version] if key in latest429 else ['v2-run-7'])
        initial=token_estimate(request(root/'cases'/case,group,models[model],root))
        repair=token_estimate(request(root/'cases'/case,group,models[model],root,True))
        slots.append({'model':model,'group':group,'case_id':case,'repetition':rep,
            'old_observation_sha256':digest(canonical(selected[key])),'reservation_versions':versions,
            'initial_input_reservation':initial['upper'],'repair_input_reservation':repair['upper']})
    inherited=read_json(history/'API_APPROVAL.json')
    caps={k:inherited[k] for k in ('max_calls','max_input_tokens','max_output_tokens')}
    ledger=read_json(root/'runs/API_LEDGER.json')
    if ledger['calls']!=expected_calls or (root/'runs/API_ACTIVE.lock').exists():raise ValueError('stopped ledger changed')
    worst={'max_calls':ledger['calls']+2*len(slots),
        'max_input_tokens':ledger['input_reserved']+sum(s['initial_input_reservation']+s['repair_input_reservation'] for s in slots),
        'max_output_tokens':ledger['output_reserved']+2*len(slots)*8192}
    if any(worst[k]>caps[k] for k in caps):raise ValueError('inherited budget insufficient; do not expand silently')
    doc={'version':'v2-credential-recovery-2','date':'2026-10-08','user_authorized':True,
        'user_priority_quote':QUOTE,'budget_authorization_quote':inherited['user_credential_recovery_authorization_quote'],
        'parent_version':parent_version,'parent_plan_sha256':parent_sha,'frozen_md_sha256':old['frozen_md_sha256'],
        'reason_filter':'HTTP 429 only; no QC-answer selection','automatic_network_retries':0,
        'credential_location':'local environment only; value not recorded','credential_ordinal':credential_ordinal,
        'user_continue_quote':'继续跑' if credential_ordinal==4 else QUOTE,
        'recovery_observations':len(slots),'carried_observations':expected_observed-len(latest429),'active_model_names':active,
        'deferred_model_names':deferred,'slots':slots,'approved_cumulative_caps':caps,
        'inherited_approval':{'file':f'history/{parent_version}/API_APPROVAL.json','sha256':digest((history/'API_APPROVAL.json').read_bytes())},
        'original_429_source':{'file':'history/v2-run-7/resume_records.jsonl','sha256':digest(original_path.read_bytes()),'version':'v2-run-7'},
        'previous_reservations':{k:ledger[k] for k in ('calls','input_reserved','output_reserved')},
        'priority_worst_case_cumulative_reservation':worst,'budget_increased':False,
        'analysis':'retain six-model roster and864 denominator; four-model576 priority; two models deferred, not complete; original failures immutable'}
    recovery_file=f'CREDENTIAL_RECOVERY_{label}.json'
    write_json(root/recovery_file,doc)
    write_json(root/priority_file,{'date':'2026-10-08','user_authorized':True,'user_quote':QUOTE,
        'credential_continue_quote':doc['user_continue_quote'],
        'parent_plan_sha256':parent_sha,'frozen_md_sha256':old['frozen_md_sha256'],
        'active_model_names':active,'deferred_model_names':deferred,'max_workers':4,
        'roster_changed':False,'thresholds_changed':False,'post_start':True,
        'active_planned_observations':576,'deferred_planned_observations':288,'deferred_saved_observations':70,
        'active_remaining_recovery_observations':len(slots),'deferred_unexecuted_observations':218})
    carried=[r for r in source if r['record_type']=='observation' and slot(r) not in selected]
    receipt=read_json(history/'RESUME_RECEIPT.json')
    receipt.update(carried_observations=len(carried),carried_counts=dict(Counter(r['status'] for r in carried)),
        recovery_audit_only_observations=1,audit_only_models=[],policy='only latest429 deferred for new credential; all other results retained;GLM/Kimi records stay active archive')
    write_json(history/'RESUME_RECEIPT.json',receipt)
    old.update(version=new_version,parent_plan_sha256=parent_sha,
        execution={'max_workers':4,'per_model_limit':1,'active_model_names':active,
            'deferred_model_names':deferred,'queue_policy':'four lanes B then C2; GLM/Kimi no dispatch, retain records'},
        priority_revision={'file':priority_file,'sha256':digest((root/priority_file).read_bytes())},
        credential_recovery={'file':recovery_file,'sha256':digest((root/recovery_file).read_bytes())},
        resume={'parent_version':parent_version,'receipt':f'history/{parent_version}/RESUME_RECEIPT.json',
            'receipt_sha256':digest((history/'RESUME_RECEIPT.json').read_bytes()),
            'records':f'history/{parent_version}/resume_records.jsonl','records_sha256':digest((history/'resume_records.jsonl').read_bytes()),
            'protected_versions':sorted(set(old['resume']['protected_versions']+[parent_version])),'audit_only_models':[]})
    for name in old['implementation']:old['implementation'][name]=digest((root/name).read_bytes())
    for name in ['register_priority.py',recovery_file,priority_file,appendix]:
        old['implementation'][name]=digest((root/name).read_bytes())
    write_json(root/'RUN_PLAN.json',old);sha=digest((root/'RUN_PLAN.json').read_bytes())
    (root/'RUN_PLAN.sha256').write_bytes((sha+'\n').encode())
    inherited.update(plan_sha256=sha,mock_report_sha256=None,
        priority_authorization_quote=QUOTE,credential_recovery_amendment=recovery_file,
        user_credential_continue_quote=doc['user_continue_quote'],
        parent_approval_sha256=digest((history/'API_APPROVAL.json').read_bytes()),
        approval_context=f'Local credential{credential_ordinal}; four models active, GLM/Kimi retained/deferred; inherited numeric budget unchanged',
        transport_revision=f'{new_version};{len(slots)} active recovery slots,{len(carried)} carried;new mock binding pending')
    write_json(root/'API_APPROVAL.json',inherited);verify(root)
    print(f'PASS:four active/two deferred;{len(slots)} recovery/{len(carried)} carried;inherited caps unchanged;worst case',worst)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--parent-version',default='v2-run-8');p.add_argument('--credential-ordinal',type=int,default=3)
    args=p.parse_args();register(parent_version=args.parent_version,credential_ordinal=args.credential_ordinal)
