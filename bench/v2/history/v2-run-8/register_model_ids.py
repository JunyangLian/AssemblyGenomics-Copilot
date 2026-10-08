"""Archive a zero-response ID failure cohort and register official display-name mappings."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from collections import Counter
import json
import shutil
from bench.v2.runtime import V2, canonical, digest, read_json, write_json


def archive(root=V2):
    from bench.v2.plan import verify
    locked = verify(root)
    if locked['plan']['version'] != 'v2-run-2': raise ValueError('unexpected transport parent')
    out = root / 'history/v2-run-2'
    if out.exists(): raise ValueError('history already exists')
    observations, logs = {}, {}
    for p in sorted((root / 'runs').glob('*/records.jsonl')):
        rows = [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
        relevant = [r for r in rows if r.get('mode') == 'api' and r.get('plan_sha256') == locked['plan_sha256']]
        if not relevant: continue
        if len(rows) != len(relevant) or any(r.get('response') is not None or r.get('parsed') is not None
            or r.get('usage') is not None or r.get('status') != 'api_error' for r in relevant):
            raise ValueError('cannot select/rerun a cohort that contains model responses')
        logs[p.relative_to(root).as_posix()] = digest(p.read_bytes())
        for r in relevant:
            if r['record_type'] != 'observation': continue
            slot = (r['model'], r['group'], r['case_id'], r['repetition'])
            if slot in observations: raise ValueError('duplicate prior observation')
            observations[slot] = r
    ledger = read_json(root / 'runs/API_LEDGER.json')
    reservations = {}
    for r in ledger['slots']:
        version, model, group, case, repeat, attempt = r['slot'].split(':')
        if version != 'v2-run-2': continue
        if attempt != '0' or r['usage'] is not None: raise ValueError('unexpected retry/provider usage')
        reservations[(model, group, case, int(repeat))] = r
    wanted = {(m['name'], g, c['case_id'], i) for m in locked['plan']['models']
              for g in locked['plan']['groups'] for c in locked['plan']['cases'] for i in range(1, 4)}
    if not set(observations) <= set(reservations) or not set(reservations) <= wanted:
        raise ValueError('previous requests do not match planned slots')
    rows = []
    for slot in sorted(wanted):
        if slot in observations: rows.append(observations[slot]); continue
        m, g, c, rep = slot; sent = slot in reservations
        rows.append({'record_type': 'observation', 'mode': 'api', 'model': m, 'group': g,
            'case_id': c, 'repetition': rep, 'status': 'interrupted' if sent else 'not_executed',
            'response': None, 'parsed': None, 'usage': None, 'attempts': 1 if sent else 0,
            'error': 'interrupted after reservation; provider receipt unknown' if sent else 'cohort stopped before this slot',
            'plan_sha256': locked['plan_sha256'], 'frozen_md_sha256': locked['frozen_md_sha256']})
    out.mkdir(parents=True)
    names = set(locked['plan']['implementation']) | {
        'RUN_PLAN.json', 'RUN_PLAN.sha256', 'API_APPROVAL.json', 'MOCK_REPORT.json', 'MOCK_REPORT.md',
        'MOCK_RUNS.json', 'API_APPROVAL.template.json', 'A_REUSE_RECEIPT.json', 'RULES_PACKAGE.json'}
    for n in sorted(names):
        target = out / n; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((root / n).read_bytes())
    (out / 'API_LEDGER.json').write_bytes((root / 'runs/API_LEDGER.json').read_bytes())
    (out / 'transport_observations.jsonl').write_bytes(b''.join(canonical(r) for r in rows))
    write_json(out / 'TRANSPORT_FAILURE.json', {'status': 'model_id_failed', 'planned_observations': len(wanted),
        'counts': dict(Counter(r['status'] for r in rows)), 'valid_model_responses': 0,
        'reserved_calls_this_cohort': len(reservations), 'cumulative_reserved_calls': ledger['calls'],
        'original_log_sha256': logs, 'budgets_refunded': False, 'plan_sha256': locked['plan_sha256'],
        'reason': 'display names submitted as IDs returned HTTP404; official /v1/models provides distinct lowercase IDs',
        'analysis_policy': 'All previous failed/planned slots retained as separate infrastructure cohorts; no valid QC answer used to select a replacement.'})
    lock = root / 'runs/API_ACTIVE.lock'
    if lock.exists(): (out / 'API_ACTIVE.lock').write_bytes(lock.read_bytes()); lock.unlink()
    source = (root / 'rules_package').resolve(); work = (root / 'work').resolve()
    dest = (work / 'transport_run2_rules_package').resolve()
    if source.exists():
        if root.resolve() not in source.parents or work not in dest.parents or dest.exists():
            raise ValueError('archive move must stay in the v2 workspace and not overwrite')
        shutil.move(str(source), str(dest))
    (work / 'transport_run2_rules_package.zip').write_bytes((root / 'rules_package.zip').read_bytes())
    print('PASS: failed model-ID cohort archived; ledger unchanged')


def register(root=V2):
    from bench.v2.plan import models, verify
    from bench.v2.freeze import verify as freeze_verify
    freeze_verify(root)
    old = read_json(root / 'history/v2-run-2/RUN_PLAN.json')
    parent_sha = digest((root / 'history/v2-run-2/RUN_PLAN.json').read_bytes())
    if digest((root / 'RUN_PLAN.json').read_bytes()) != parent_sha: raise ValueError('parent plan changed unexpectedly')
    configured = models(root)
    for before, after in zip(old['models'], configured):
        if before != {k: v for k, v in after.items() if k != 'requested_model_id'}:
            raise ValueError('only official request IDs may change in this revision')
    old.update(version='v2-run-3', parent_plan_sha256=parent_sha, models=configured,
        model_id_revision={'source': 'PROVIDER_MODELS.json', 'source_sha256': digest((root / 'PROVIDER_MODELS.json').read_bytes()),
            'mapping': {m['name']: m['requested_model_id'] for m in configured},
            'returned_identity': 'only official ID or its exact official display name; other identities pause model',
            'failed_cohort': 'history/v2-run-2/TRANSPORT_FAILURE.json',
            'failed_cohort_sha256': digest((root / 'history/v2-run-2/TRANSPORT_FAILURE.json').read_bytes()),
            'scope': 'same five underlying requested model versions; full 720 slots; zero valid prior responses',
            'budget': 'fixed cumulative caps unchanged; failures remain reserved'})
    for name in old['implementation']:
        old['implementation'][name] = digest((root / name).read_bytes())
    old['implementation']['register_model_ids.py'] = digest((root / 'register_model_ids.py').read_bytes())
    old['implementation']['PROVIDER_MODELS.json'] = digest((root / 'PROVIDER_MODELS.json').read_bytes())
    old['provider_policy']['model_ids'] = 'official /v1/models id:name mapping verified; exact model weights remain unverified'
    write_json(root / 'RUN_PLAN.json', old)
    sha = digest((root / 'RUN_PLAN.json').read_bytes()); (root / 'RUN_PLAN.sha256').write_bytes((sha + '\n').encode())
    approved = read_json(root / 'history/v2-run-2/API_APPROVAL.json')
    approved.update(plan_sha256=sha, mock_report_sha256=None, transport_revision='v2-run-3; official ID mapping and domain-only NO_PROXY; all old reservations retained')
    write_json(root / 'API_APPROVAL.json', approved)
    verify(root)
    print('PASS: v2-run-3; exact official IDs registered; new mock binding pending')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--archive', action='store_true')
    args = p.parse_args(); archive() if args.archive else register()
