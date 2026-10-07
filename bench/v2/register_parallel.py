"""Register a scheduling-only revision after graceful stop, preserving every slot."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from collections import Counter
import json
import shutil
from bench.v2.runtime import V2, canonical, digest, read_json, write_json

QUOTE = '不能四个同时跑吗'


def archive(root=V2):
    from bench.v2.plan import verify
    locked = verify(root)
    if locked['plan']['version'] != 'v2-run-5': raise ValueError('unexpected concurrency parent')
    if (root / 'runs/API_ACTIVE.lock').exists(): raise ValueError('wait for graceful stop before archive')
    out = root / 'history/v2-run-5'
    if out.exists(): raise ValueError('history already exists')
    observations, records, logs = {}, [], {}
    index = read_json(root / 'API_RUNS.json')
    if index['plan_sha256'] != locked['plan_sha256']: raise ValueError('old index differs')
    for name in index['runs']:
        p = (root / name / 'records.jsonl').resolve(strict=True)
        if (root / 'runs').resolve() not in p.parents: raise ValueError('indexed source outside runs')
        logs[p.relative_to(root).as_posix()] = digest(p.read_bytes())
        for row in [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]:
            if row.get('mode') != 'api' or row['plan_sha256'] != locked['plan_sha256']:
                raise ValueError('mixed source log')
            records.append({**row, 'source_log': p.relative_to(root).as_posix()})
            if row['record_type'] == 'observation':
                key = (row['model'], row['group'], row['case_id'], row['repetition'])
                if key in observations: raise ValueError('duplicate old observation')
                observations[key] = row
    ledger = read_json(root / 'runs/API_LEDGER.json')
    for row in ledger['slots']:
        version, model, group, case, rep, attempt = row['slot'].split(':')
        if version == locked['plan']['version'] and (model, group, case, int(rep)) not in observations:
            raise ValueError('graceful stop still has unfinished reservation; inspect before proceeding')
    out.mkdir(parents=True)
    names = set(locked['plan']['implementation']) | {
        'RUN_PLAN.json', 'RUN_PLAN.sha256', 'API_APPROVAL.json', 'MOCK_REPORT.json', 'MOCK_REPORT.md',
        'MOCK_RUNS.json', 'API_APPROVAL.template.json', 'A_REUSE_RECEIPT.json', 'RULES_PACKAGE.json', 'API_RUNS.json'}
    for name in sorted(names):
        target = out / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes())
    (out / 'API_LEDGER.json').write_bytes((root / 'runs/API_LEDGER.json').read_bytes())
    (out / 'resume_records.jsonl').write_bytes(b''.join(canonical(r) for r in records))
    write_json(out / 'RESUME_RECEIPT.json', {'status': 'pass', 'parent_version': locked['plan']['version'],
        'parent_plan_sha256': locked['plan_sha256'], 'original_log_sha256': logs,
        'records_sha256': digest((out / 'resume_records.jsonl').read_bytes()),
        'observations': len(observations), 'counts': dict(Counter(r['status'] for r in observations.values())),
        'cumulative_reserved_calls': ledger['calls'], 'budgets_refunded': False,
        'gracefully_stopped': True, 'new_interruptions': 0,
        'primary_new_observations': sum(r['case_id'].startswith('new_') for r in observations.values()),
        'policy': 'scheduling only; all outputs/errors/unknowns resume; no model/case/parameter/budget changes'})
    marker = root / 'runs/STOP_AFTER_CURRENT_REQUEST'
    if marker.exists(): (out / 'STOP_AFTER_CURRENT_REQUEST').write_bytes(marker.read_bytes())
    (root / 'API_RUNS.json').unlink()
    source = (root / 'rules_package').resolve(); work = (root / 'work').resolve()
    destination = (work / 'serial_run5_rules_package').resolve()
    if source.exists():
        if root.resolve() not in source.parents or work not in destination.parents or destination.exists():
            raise ValueError('archive move must stay inside v2 and not overwrite')
        shutil.move(str(source), str(destination))
    (work / 'serial_run5_rules_package.zip').write_bytes((root / 'rules_package.zip').read_bytes())
    print('PASS: graceful serial stop archived; all results and cumulative budget retained')


def register(root=V2, refresh_before_api=False):
    from bench.v2.plan import models, public_cases, verify
    from bench.v2.freeze import verify as frozen_verify
    frozen_verify(root)
    history = root / 'history/v2-run-5'
    parent_sha = digest((history / 'RUN_PLAN.json').read_bytes())
    if digest((root / 'RUN_PLAN.json').read_bytes()) != parent_sha:
        current = read_json(root / 'RUN_PLAN.json')
        ledger = read_json(root / 'runs/API_LEDGER.json')
        if (not refresh_before_api or current['version'] != 'v2-run-6'
            or current['parent_plan_sha256'] != parent_sha or (root / 'API_RUNS.json').exists()
            or (root / 'runs/API_ACTIVE.lock').exists()
            or any(r['slot'].startswith('v2-run-6:') for r in ledger['slots'])):
            raise ValueError('unexpected parent plan or live calls prevent pre-live implementation repair')
    old = read_json(history / 'RUN_PLAN.json')
    if models(root) != old['models'] or public_cases(root) != old['cases']:
        raise ValueError('concurrency revision must not change model protocols or cases')
    receipt = read_json(history / 'RESUME_RECEIPT.json')
    write_json(root / 'SCHEDULING_REVISION.json', {'version': 'v2-schedule-1', 'date': '2026-10-07',
        'user_authorized': True, 'user_quote': QUOTE, 'parent_plan_sha256': parent_sha,
        'frozen_md_sha256': old['frozen_md_sha256'], 'preregistration_sha256': digest((root / 'preregistration.json').read_bytes()),
        'post_start': True, 'thresholds_changed': False, 'models_or_parameters_changed': False,
        'max_workers': 4, 'per_model_limit': 1, 'queue_policy': 'round_robin_one_observation_per_model; B then C2 within each model',
        'shared_budget': 'one mutex per ledger path; reread, reserve, atomically replace before POST; no refunds',
        'existing_observations': receipt['observations'], 'existing_counts': receipt['counts'],
        'primary_new_observations_before_change': receipt['primary_new_observations'],
        'cumulative_reserved_calls': receipt['cumulative_reserved_calls'],
        'retention': 'carry ALL old results/failures; primary new cases not yet observed; no selective QC reruns'})
    if refresh_before_api:
        data = read_json(root / 'SCHEDULING_REVISION.json')
        data['prelive_validation_repair'] = {
            'audit': 'history/v2-run-6-prelive', 'model_calls': 0,
            'reason': 'Windows atomic rename can temporarily deny progress readers; retry sharing errors without masking corrupt JSON'}
        write_json(root / 'SCHEDULING_REVISION.json', data)
    protected = sorted(set(old['resume'].get('protected_versions', []) + ['v2-run-3', 'v2-run-4', 'v2-run-5']))
    old.update(version='v2-run-6', parent_plan_sha256=parent_sha,
        execution={'max_workers': 4, 'per_model_limit': 1,
            'queue_policy': 'round_robin_one_observation_per_model; B then C2 within each model'},
        scheduling_revision={'file': 'SCHEDULING_REVISION.json', 'sha256': digest((root / 'SCHEDULING_REVISION.json').read_bytes())},
        resume={'parent_version': 'v2-run-5', 'receipt': 'history/v2-run-5/RESUME_RECEIPT.json',
            'receipt_sha256': digest((history / 'RESUME_RECEIPT.json').read_bytes()),
            'records': 'history/v2-run-5/resume_records.jsonl',
            'records_sha256': digest((history / 'resume_records.jsonl').read_bytes()),
            'protected_versions': protected})
    for name in old['implementation']: old['implementation'][name] = digest((root / name).read_bytes())
    for name in ['parallel.py', 'concurrent_budget.py', 'register_parallel.py', 'SCHEDULING_REVISION.json']:
        old['implementation'][name] = digest((root / name).read_bytes())
    write_json(root / 'RUN_PLAN.json', old)
    sha = digest((root / 'RUN_PLAN.json').read_bytes()); (root / 'RUN_PLAN.sha256').write_bytes((sha + '\n').encode())
    approved = read_json(history / 'API_APPROVAL.json')
    approved.update(plan_sha256=sha, mock_report_sha256=None,
        parent_approval_sha256=digest((history / 'API_APPROVAL.json').read_bytes()),
        user_concurrency_authorization_quote=QUOTE, scheduling_amendment='SCHEDULING_REVISION.json',
        transport_revision='v2-run-6; four shared-budget request workers; all prior observations carried; caps unchanged')
    write_json(root / 'API_APPROVAL.json', approved)
    verify(root)
    print('PASS: four-worker scheduling locked; new mock binding pending')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--archive', action='store_true')
    p.add_argument('--refresh-before-api', action='store_true')
    args = p.parse_args(); archive() if args.archive else register(refresh_before_api=args.refresh_before_api)
