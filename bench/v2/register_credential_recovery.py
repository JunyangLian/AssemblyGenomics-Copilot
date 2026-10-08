"""Register a user-authorized second-credential recovery, retaining the old cohort."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from collections import Counter
import json
from bench.v2.runtime import V2, canonical, digest, read_json, write_json, request, token_estimate
from bench.v2.credential_recovery import eligible, slot

QUOTE = '补跑全部623条429，并增加所需累计预算'


def register(root=V2):
    from bench.v2.freeze import verify as frozen_verify
    from bench.v2.plan import verify
    frozen_verify(root)
    history = root / 'history/v2-run-7'
    parent_sha = digest((history / 'RUN_PLAN.json').read_bytes())
    if digest((root / 'RUN_PLAN.json').read_bytes()) != parent_sha:
        raise ValueError('unexpected credential-recovery parent')
    old = read_json(history / 'RUN_PLAN.json')
    source = [json.loads(line) for line in (history / 'resume_records.jsonl').read_text(encoding='utf-8').splitlines()]
    selected = eligible(source)
    if len(selected) != 623: raise ValueError('reviewed HTTP429 recovery count changed')
    models = {m['name']: m for m in old['models']}
    rank = {m['name']: i for i, m in enumerate(old['models'])}
    cases = {c['case_id']: i for i, c in enumerate(old['cases'])}
    ordered = sorted(selected, key=lambda s: (rank[s[0]],old['groups'].index(s[1]),cases[s[2]],s[3]))
    slots = []
    for model, group, case, rep in ordered:
        initial = token_estimate(request(root/'cases'/case, group, models[model], root))
        repair = token_estimate(request(root/'cases'/case, group, models[model], root, True))
        slots.append({'model': model, 'group': group, 'case_id': case, 'repetition': rep,
            'old_observation_sha256': digest(canonical(selected[model,group,case,rep])),
            'initial_input_reservation': initial['upper'], 'repair_input_reservation': repair['upper']})
    ledger = read_json(root/'runs/API_LEDGER.json')
    if ledger['calls'] != 1390 or (root/'runs/API_ACTIVE.lock').exists():
        raise ValueError('reviewed stopped ledger changed')
    caps = {'max_calls': ledger['calls']+2*len(slots),
            'max_input_tokens': ledger['input_reserved']+sum(s['initial_input_reservation']+s['repair_input_reservation'] for s in slots),
            'max_output_tokens': ledger['output_reserved']+2*len(slots)*8192}
    if caps != {'max_calls':2636,'max_input_tokens':52724811,'max_output_tokens':21594112}:
        raise ValueError('derived caps differ from human-reviewed proposal')
    doc = {'version':'v2-credential-recovery-1','date':'2026-10-08','user_authorized':True,
        'budget_authorization_quote':QUOTE,'parent_version':'v2-run-7','parent_plan_sha256':parent_sha,
        'frozen_md_sha256':old['frozen_md_sha256'],'reason_filter':'HTTP 429 only; no QC-answer selection',
        'automatic_network_retries':0,'credential_location':'local environment only; no value recorded',
        'recovery_observations':len(slots),'carried_observations':241,'slots':slots,
        'previous_reservations':{k:ledger[k] for k in ('calls','input_reserved','output_reserved')},
        'approved_cumulative_caps':caps,'initial_recovery_calls':623,'full_repair_recovery_calls':1246,
        'analysis':'post-start credential recovery; retain/report original864 cohort separately; recovered864 denominator; no additional independent biological repeats'}
    write_json(root/'CREDENTIAL_RECOVERY.json',doc)
    carried = [r for r in source if r['record_type']=='observation' and slot(r) not in selected]
    receipt = read_json(history/'RESUME_RECEIPT.json')
    receipt.update(carried_observations=len(carried),carried_counts=dict(Counter(r['status'] for r in carried)),
        recovery_audit_only_observations=len(selected),audit_only_models=[],
        policy='all source records immutable; only user-authorized HTTP429 recovery deferred; no QC selection')
    write_json(history/'RESUME_RECEIPT.json',receipt)
    old.update(version='v2-run-8',parent_plan_sha256=parent_sha,
        credential_recovery={'file':'CREDENTIAL_RECOVERY.json','sha256':digest((root/'CREDENTIAL_RECOVERY.json').read_bytes())},
        resume={'parent_version':'v2-run-7','receipt':'history/v2-run-7/RESUME_RECEIPT.json',
            'receipt_sha256':digest((history/'RESUME_RECEIPT.json').read_bytes()),
            'records':'history/v2-run-7/resume_records.jsonl',
            'records_sha256':digest((history/'resume_records.jsonl').read_bytes()),
            'protected_versions':sorted(set(old['resume']['protected_versions']+['v2-run-7'])),
            'audit_only_models':[]})
    for name in old['implementation']: old['implementation'][name]=digest((root/name).read_bytes())
    for name in ['credential_recovery.py','register_credential_recovery.py','CREDENTIAL_RECOVERY.json',
                 'PREREGISTRATION_AMENDMENT_CREDENTIAL_20261008.md']:
        old['implementation'][name]=digest((root/name).read_bytes())
    write_json(root/'RUN_PLAN.json',old)
    sha=digest((root/'RUN_PLAN.json').read_bytes()); (root/'RUN_PLAN.sha256').write_bytes((sha+'\n').encode())
    approval=read_json(history/'API_APPROVAL.json')
    approval.update(**caps,plan_sha256=sha,mock_report_sha256=None,
        user_credential_recovery_authorization_quote=QUOTE,
        parent_approval_sha256=digest((history/'API_APPROVAL.json').read_bytes()),
        credential_recovery_amendment='CREDENTIAL_RECOVERY.json',
        approval_context='Human approved all623 HTTP429 recovery and required derived caps; same6 models/protocol; cumulative1390 old reservations retained',
        transport_revision='v2-run-8; second local credential; only623 HTTP429 recovery; new mock binding pending')
    write_json(root/'API_APPROVAL.json',approval)
    verify(root)
    print('PASS:623 recovery/241 retained observations registered; new mock binding pending; caps',caps)


if __name__=='__main__': register()
