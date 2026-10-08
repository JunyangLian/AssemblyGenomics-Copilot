"""Explicit human model replacement; retain old Flash audit, resume other models."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from collections import Counter
import json
import os
import shutil
from bench.v2.runtime import V2, canonical, digest, read_json, write_json

OLD = 'DeepSeek-V4-Flash-0731'
NEW = 'DeepSeek-V4-Flash-Vision'
QUOTE = '那就用deepseek-v4-flash-vision吧，其他继续跑'


def archive(root=V2):
    from bench.v2.plan import verify
    locked = verify(root)
    if locked['plan']['version'] != 'v2-run-4': raise ValueError('unexpected Vision parent')
    out = root / 'history/v2-run-4'
    if out.exists(): raise ValueError('history already exists')
    lock = root / 'runs/API_ACTIVE.lock'
    if lock.exists():
        pid = int(lock.read_text())
        if os.name == 'nt':
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                raise ValueError('previous API process is still alive')
        else:
            try: os.kill(pid, 0)
            except ProcessLookupError: pass
            else: raise ValueError('previous API process is still alive')
    observations, records, logs = {}, [], {}
    for p in sorted((root / 'runs').glob('*/records.jsonl')):
        rows = [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]
        selected = [r for r in rows if r.get('mode') == 'api' and r.get('plan_sha256') == locked['plan_sha256']]
        if not selected: continue
        if len(selected) != len(rows): raise ValueError('mixed source log')
        logs[p.relative_to(root).as_posix()] = digest(p.read_bytes())
        for row in selected:
            records.append({**row, 'source_log': p.relative_to(root).as_posix()})
            if row['record_type'] == 'observation':
                key = (row['model'], row['group'], row['case_id'], row['repetition'])
                if key in observations: raise ValueError('duplicate prior observation')
                observations[key] = row
    ledger = read_json(root / 'runs/API_LEDGER.json')
    reservations = {}
    for row in ledger['slots']:
        version, model, group, case, rep, attempt = row['slot'].split(':')
        if version != locked['plan']['version']: continue
        reservations.setdefault((model, group, case, int(rep)), []).append(row)
    for key, entries in reservations.items():
        if key in observations: continue
        model, group, case, rep = key
        row = {'record_type': 'observation', 'mode': 'api', 'model': model, 'group': group,
            'case_id': case, 'repetition': rep, 'plan_sha256': locked['plan_sha256'],
            'frozen_md_sha256': locked['frozen_md_sha256'], 'status': 'interrupted', 'parsed': None,
            'response': None, 'usage': None, 'attempts': len(entries),
            'error': 'stopped after reservation; provider receipt unknown; never resend',
            'source_reservations': [r['slot'] for r in entries]}
        records.append(row); observations[key] = row
    out.mkdir(parents=True)
    names = set(locked['plan']['implementation']) | {
        'RUN_PLAN.json', 'RUN_PLAN.sha256', 'API_APPROVAL.json', 'MOCK_REPORT.json', 'MOCK_REPORT.md',
        'MOCK_RUNS.json', 'API_APPROVAL.template.json', 'A_REUSE_RECEIPT.json', 'RULES_PACKAGE.json', 'API_RUNS.json'}
    for name in sorted(names):
        target = out / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes())
    (out / 'API_LEDGER.json').write_bytes((root / 'runs/API_LEDGER.json').read_bytes())
    (out / 'resume_records.jsonl').write_bytes(b''.join(canonical(r) for r in records))
    carried = [r for r in observations.values() if r['model'] != OLD]
    write_json(out / 'RESUME_RECEIPT.json', {'status': 'pass', 'parent_version': locked['plan']['version'],
        'parent_plan_sha256': locked['plan_sha256'], 'original_log_sha256': logs,
        'records_sha256': digest((out / 'resume_records.jsonl').read_bytes()),
        'observations': len(observations), 'counts': dict(Counter(r['status'] for r in observations.values())),
        'carried_observations': len(carried), 'carried_counts': dict(Counter(r['status'] for r in carried)),
        'audit_only_models': [OLD], 'audit_only_observations': len(observations) - len(carried),
        'cumulative_reserved_calls': ledger['calls'], 'budgets_refunded': False,
        'policy': 'old Flash remains audit-only; replacement Vision starts all144 slots; all other results/failures carried'})
    if lock.exists(): (out / 'API_ACTIVE.lock').write_bytes(lock.read_bytes()); lock.unlink()
    # Preserve old directory index before starting the new plan's durable index.
    (root / 'API_RUNS.json').unlink()
    source = (root / 'rules_package').resolve(); work = (root / 'work').resolve()
    dest = (work / 'roster2_rules_package').resolve()
    if source.exists():
        if root.resolve() not in source.parents or work not in dest.parents or dest.exists():
            raise ValueError('archive move must stay inside v2 and not overwrite')
        shutil.move(str(source), str(dest))
    (work / 'roster2_rules_package.zip').write_bytes((root / 'rules_package.zip').read_bytes())
    print('PASS: full prior audit preserved; other models carried; ledger unchanged')


def register(root=V2):
    from bench.v2.plan import models, verify
    from bench.v2.freeze import verify as frozen_verify
    frozen_verify(root)
    history = root / 'history/v2-run-4'
    parent_sha = digest((history / 'RUN_PLAN.json').read_bytes())
    if digest((root / 'RUN_PLAN.json').read_bytes()) != parent_sha: raise ValueError('unexpected parent plan')
    old = read_json(history / 'RUN_PLAN.json')
    receipt = read_json(history / 'RESUME_RECEIPT.json')
    names = [NEW if m['name'] == OLD else m['name'] for m in old['models']]
    write_json(root / 'VISION_MODEL_REVISION.json', {'version': 'v2-model-roster-3', 'date': '2026-10-07',
        'user_authorized': True, 'user_quote': QUOTE, 'previous_model_names': [m['name'] for m in old['models']],
        'model_names': names, 'parent_plan_sha256': parent_sha, 'frozen_md_sha256': old['frozen_md_sha256'],
        'preregistration_sha256': digest((root / 'preregistration.json').read_bytes()),
        'post_start': True, 'thresholds_changed': False, 'provider_metadata_file': 'PROVIDER_MODELS_VISION.json',
        'provider_metadata_sha256': digest((root / 'PROVIDER_MODELS_VISION.json').read_bytes()),
        'request_model_id': 'deepseek-v4-flash-vision',
        'accepted_response_ids': ['deepseek-v4-flash-vision', 'DeepSeek-V4-Flash-Vision', 'dsv4-flash-vision'],
        'response_alias_authority': 'human chose Vision after seeing dsv4-flash-vision identity error; this is explicit Vision-family acceptance, not proof of 0731 weights',
        'exact_weights_or_snapshot': 'provider unverified; Vision family only; never claim0731',
        'valid_prior_observations': receipt['carried_counts'].get('ok', 0),
        'cumulative_reserved_calls_before_amendment': receipt['cumulative_reserved_calls'],
        'old_flash_policy': 'retain all old0731 responses/errors/pauses audit-only; do not reclassify or reuse for Vision',
        'analysis_model_names': names, 'h1_min_models_same_direction': 2,
        'retention': 'all other model outputs/failures retained; fresh144 slots for new model; cumulative caps unchanged'})
    configured = models(root)
    previous = {m['name']: m for m in old['models']}
    for model in configured:
        if model['name'] != NEW and model != previous[model['name']]: raise ValueError('other models changed')
    old.update(version='v2-run-5', parent_plan_sha256=parent_sha, models=configured,
        vision_revision={'file': 'VISION_MODEL_REVISION.json', 'sha256': digest((root / 'VISION_MODEL_REVISION.json').read_bytes()),
            'post_start': True, 'frozen_preregistration_unchanged': True},
        resume={'parent_version': 'v2-run-4', 'receipt': 'history/v2-run-4/RESUME_RECEIPT.json',
            'receipt_sha256': digest((history / 'RESUME_RECEIPT.json').read_bytes()),
            'records': 'history/v2-run-4/resume_records.jsonl',
            'records_sha256': digest((history / 'resume_records.jsonl').read_bytes()),
            'audit_only_models': [OLD], 'protected_versions': ['v2-run-3', 'v2-run-4']})
    for name in old['implementation']: old['implementation'][name] = digest((root / name).read_bytes())
    for name in ['register_vision.py', 'VISION_MODEL_REVISION.json', 'PROVIDER_MODELS_VISION.json',
                 'PREREGISTRATION_AMENDMENT_VISION_20261007.md']:
        old['implementation'][name] = digest((root / name).read_bytes())
    write_json(root / 'RUN_PLAN.json', old)
    sha = digest((root / 'RUN_PLAN.json').read_bytes()); (root / 'RUN_PLAN.sha256').write_bytes((sha + '\n').encode())
    approved = read_json(history / 'API_APPROVAL.json')
    approved.update(plan_sha256=sha, mock_report_sha256=None, models=names,
        parent_approval_sha256=digest((history / 'API_APPROVAL.json').read_bytes()),
        vision_amendment='VISION_MODEL_REVISION.json', user_vision_authorization_quote=QUOTE,
        transport_revision='v2-run-5; explicitly replace0731 by Vision; retain old audit and other model results; same cumulative caps')
    write_json(root / 'API_APPROVAL.json', approved)
    verify(root)
    print('PASS: Vision replacement locked; new mock binding pending')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--archive', action='store_true')
    args = p.parse_args(); archive() if args.archive else register()
