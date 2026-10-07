"""Record a no-response TLS failure cohort before starting an explicit transport revision."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from collections import Counter
import json
import shutil
from bench.v2.runtime import V2, canonical, digest, read_json, write_json, request, summary
from bench.v2.plan import verify


def register(root=V2):
    old = verify(root)
    if old['plan']['version'] != 'v2-run-1':
        raise ValueError('only the explicitly identified first transport failure cohort may be revised')
    archive = root / 'history/v2-run-1'
    if archive.exists():
        raise ValueError('transport revision archive already exists; do not overwrite history')
    ledger = read_json(root / 'runs/API_LEDGER.json')
    rows, source_files, directories = [], {}, []
    for p in sorted((root / 'runs').glob('*/records.jsonl')):
        data = p.read_bytes()
        content = [json.loads(s) for s in data.decode('utf-8').splitlines()]
        relevant = [r for r in content if r.get('mode') == 'api' and r.get('plan_sha256') == old['plan_sha256']]
        if not relevant:
            continue
        if len(relevant) != len(content):
            raise ValueError('mixed identities in transport log')
        if any(r.get('response') is not None or r.get('usage') is not None or r.get('parsed') is not None
               or r.get('status') != 'api_error' for r in relevant):
            raise ValueError('this transport revision requires zero model responses, not selected QC results')
        rows.extend(relevant)
        source_files[p.relative_to(root).as_posix()] = digest(data)
        directories.append(p.parent.relative_to(root).as_posix())
    attempts = [r for r in rows if r['record_type'] == 'attempt']
    observations = [r for r in rows if r['record_type'] == 'observation']
    def slot(row): return (row['model'], row['group'], row['case_id'], row['repetition'])
    observed = {slot(r): r for r in observations}
    if len(observed) != len(observations) or len(attempts) != len(observations):
        raise ValueError('unexpected previous format retries or duplicate observations')
    wanted = {(m['name'], group, c['case_id'], rep) for m in old['plan']['models']
              for group in old['plan']['groups'] for c in old['plan']['cases'] for rep in range(1, 4)}
    if not set(observed) <= wanted:
        raise ValueError('unplanned prior observations')
    reservations = {}
    for r in ledger['slots']:
        version, model, group, case, repeat, attempt = r['slot'].split(':')
        if version != 'v2-run-1' or int(attempt) != 0 or r['usage'] is not None:
            raise ValueError('unexpected ledger identity/usage')
        reservations[(model, group, case, int(repeat))] = r
    if len(reservations) != ledger['calls'] or not set(reservations) <= wanted or not set(observed) <= set(reservations):
        raise ValueError('ledger does not account for all prior requests')
    audit = []
    for model, group, case, repeat in sorted(wanted):
        key = (model, group, case, repeat)
        if key in observed:
            audit.append(observed[key]); continue
        reserved = key in reservations
        m = next(m for m in old['plan']['models'] if m['name'] == model)
        audit.append({'record_type': 'observation', 'mode': 'api', 'case_id': case,
            'group': group, 'model': model, 'repetition': repeat, 'attempts': 1 if reserved else 0,
            'status': 'interrupted' if reserved else 'not_executed', 'parsed': None, 'response': None,
            'usage': None, 'called': None if reserved else False,
            'error': 'interrupted after reservation; whether provider received request unknown' if reserved else 'transport cohort stopped before this planned slot',
            'request_summary': summary(root / 'cases' / case, request(root / 'cases' / case, group, m, root), root),
            'plan_sha256': old['plan_sha256'], 'frozen_md_sha256': old['frozen_md_sha256'],
            'run_id': 'v2-run-1-transport-audit'})
    archive.mkdir(parents=True)
    for name in ('RUN_PLAN.json', 'RUN_PLAN.sha256', 'API_APPROVAL.json', 'MOCK_REPORT.json',
                 'MOCK_REPORT.md', 'MOCK_RUNS.json', 'API_APPROVAL.template.json', 'A_REUSE_RECEIPT.json', 'RULES_PACKAGE.json'):
        (archive / name).write_bytes((root / name).read_bytes())
    (archive / 'API_LEDGER.json').write_bytes((root / 'runs/API_LEDGER.json').read_bytes())
    (archive / 'transport_observations.jsonl').write_bytes(b''.join(canonical(r) for r in audit))
    diagnostic = {'status': 'transport_failed', 'plan_sha256': old['plan_sha256'], 'planned_observations': len(audit),
        'recorded_observations': len(observations), 'reserved_calls': ledger['calls'],
        'counts': dict(Counter(r['status'] for r in audit)), 'valid_model_responses': 0,
        'input_reserved': ledger['input_reserved'], 'output_reserved': ledger['output_reserved'],
        'original_log_sha256': source_files, 'original_runs': directories,
        'diagnostic': 'unauthenticated HTTPS: default local proxy TLS EOF; direct and domain-only NO_PROXY both HTTP404 at /v1',
        'credentials_sent_by_diagnostic': False, 'budgets_refunded': False,
        'analysis_policy': 'Retain/report all 720 original planned slots as a failed transport cohort. New full cohort is separate; no valid QC output was used to select it.'}
    write_json(archive / 'TRANSPORT_FAILURE.json', diagnostic)
    # The owner was verified exited before this command. Archive the orphan lock rather than discard it.
    lock = root / 'runs/API_ACTIVE.lock'
    if lock.exists():
        (archive / 'API_ACTIVE.lock').write_bytes(lock.read_bytes()); lock.unlink()
    work = (root / 'work').resolve(); work.mkdir(exist_ok=True)
    source = (root / 'rules_package').resolve(); dest = (work / 'transport_run1_rules_package').resolve()
    if source.exists():
        if root.resolve() not in source.parents or work not in dest.parents or dest.exists():
            raise ValueError('package archive move must stay inside the v2 workspace and not overwrite')
        shutil.move(str(source), str(dest))
    old_zip = root / 'rules_package.zip'
    if old_zip.exists(): (work / 'transport_run1_rules_package.zip').write_bytes(old_zip.read_bytes())
    plan = dict(old['plan'])
    plan.update(version='v2-run-2', parent_plan_sha256=old['plan_sha256'],
        transport_revision={'reason': 'local proxy TLS EOF, verified no-key HTTPS direct path',
            'process_no_proxy_addition': 'discovery-api.intern-ai.org.cn', 'tls_verification': 'unchanged/on',
            'failed_cohort': 'history/v2-run-1/TRANSPORT_FAILURE.json',
            'failed_cohort_sha256': digest((archive / 'TRANSPORT_FAILURE.json').read_bytes()),
            'scope': 'full 720 new planned observations, all five models/groups; same public requests',
            'prior_reservations_retained': ledger['calls'], 'approval': 'current user explicitly requested direct setup and startup; no additional budget'})
    plan['implementation'] = dict(plan['implementation'])
    for name in ('register_transport.py', 'start_api.ps1'):
        plan['implementation'][name] = digest((root / name).read_bytes())
    write_json(root / 'RUN_PLAN.json', plan)
    new_sha = digest((root / 'RUN_PLAN.json').read_bytes())
    (root / 'RUN_PLAN.sha256').write_bytes((new_sha + '\n').encode('ascii'))
    approved = read_json(archive / 'API_APPROVAL.json')
    approved.update(plan_sha256=new_sha, parent_approval_sha256=digest((archive / 'API_APPROVAL.json').read_bytes()),
        transport_revision='v2-run-2; domain-only NO_PROXY; previous calls retained cumulatively',
        user_setup_and_start_authorized=True, mock_report_sha256=None)
    # Remains unusable until new mock report is produced and its exact hash attached.
    write_json(root / 'API_APPROVAL.json', approved)
    verify(root)
    print('PASS: v2-run-2 registered; ' + str(ledger['calls']) + ' prior reservations retained; 0 valid prior model responses')
    return diagnostic


if __name__ == '__main__':
    register()
