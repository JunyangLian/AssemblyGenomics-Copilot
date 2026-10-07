"""Record a human roster correction without repeating any existing model slot."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from collections import Counter
import json
import os
import shutil
from bench.v2.runtime import V2, canonical, digest, read_json, write_json

QUOTE = '模型id我重新确认了一次，是deepseek-v4-flash-0731，deepseek-v4-pro-0813，minimax-m3，glm-5.3，qwen3.8-27b'
NAMES = ['DeepSeek-V4-Flash-0731', 'DeepSeek-V4-Pro-0813', 'MiniMax-M3', 'GLM-5.3', 'Qwen3.8-27B']


def slot(row):
    return row['model'], row['group'], row['case_id'], row['repetition']


def archive(root=V2):
    from bench.v2.plan import verify
    locked = verify(root)
    if locked['plan']['version'] != 'v2-run-3':
        raise ValueError('unexpected roster parent')
    out = root / 'history/v2-run-3'
    if out.exists():
        raise ValueError('history already exists')
    lock = root / 'runs/API_ACTIVE.lock'
    if lock.exists():
        pid = int(lock.read_text())
        if os.name == 'nt':
            import ctypes
            process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if process:
                ctypes.windll.kernel32.CloseHandle(process)
                raise ValueError('prior process is still alive; stop it before archive')
        else:
            try: os.kill(pid, 0)
            except ProcessLookupError: pass
            else: raise ValueError('prior process is still alive')
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
                key = slot(row)
                if key in observations: raise ValueError('duplicate prior observation')
                observations[key] = row
    ledger = read_json(root / 'runs/API_LEDGER.json')
    reservations = {}
    for row in ledger['slots']:
        version, model, group, case, rep, attempt = row['slot'].split(':')
        if version != locked['plan']['version']: continue
        reservations.setdefault((model, group, case, int(rep)), []).append(row)
    if any(key[0] == 'Kimi-K2.6' for key in reservations):
        raise ValueError('Kimi has already been attempted; amendment needs different scope')
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
    paused = sorted({r['model'] for r in observations.values() if r['status'] == 'identity_error'})
    out.mkdir(parents=True)
    names = set(locked['plan']['implementation']) | {
        'RUN_PLAN.json', 'RUN_PLAN.sha256', 'API_APPROVAL.json', 'MOCK_REPORT.json', 'MOCK_REPORT.md',
        'MOCK_RUNS.json', 'API_APPROVAL.template.json', 'A_REUSE_RECEIPT.json', 'RULES_PACKAGE.json'}
    for name in sorted(names):
        target = out / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes())
    (out / 'API_LEDGER.json').write_bytes((root / 'runs/API_LEDGER.json').read_bytes())
    (out / 'resume_records.jsonl').write_bytes(b''.join(canonical(r) for r in records))
    write_json(out / 'RESUME_RECEIPT.json', {'status': 'pass', 'parent_version': locked['plan']['version'],
        'parent_plan_sha256': locked['plan_sha256'], 'original_log_sha256': logs,
        'records_sha256': digest((out / 'resume_records.jsonl').read_bytes()),
        'observations': len(observations), 'counts': dict(Counter(r['status'] for r in observations.values())),
        'reserved_calls_this_cohort': sum(map(len, reservations.values())), 'cumulative_reserved_calls': ledger['calls'],
        'paused_models': paused, 'kimi_calls': 0, 'budgets_refunded': False,
        'policy': 'carry ALL completed answers and failures; reserved but unfinished calls become interrupted; only unattempted slots continue'})
    if lock.exists(): (out / 'API_ACTIVE.lock').write_bytes(lock.read_bytes()); lock.unlink()
    source = (root / 'rules_package').resolve(); work = (root / 'work').resolve()
    dest = (work / 'roster1_rules_package').resolve()
    work.mkdir(exist_ok=True)
    if source.exists():
        if root.resolve() not in source.parents or work not in dest.parents or dest.exists():
            raise ValueError('archive move must stay inside v2 and not overwrite')
        shutil.move(str(source), str(dest))
    (work / 'roster1_rules_package.zip').write_bytes((root / 'rules_package.zip').read_bytes())
    print('PASS: parent answers/failures archived; cumulative ledger unchanged')


def register(root=V2):
    from bench.v2.plan import models, verify
    from bench.v2.freeze import verify as frozen_verify
    frozen_verify(root)
    history = root / 'history/v2-run-3'
    parent_sha = digest((history / 'RUN_PLAN.json').read_bytes())
    if digest((root / 'RUN_PLAN.json').read_bytes()) != parent_sha:
        raise ValueError('unexpected parent plan')
    old = read_json(history / 'RUN_PLAN.json')
    receipt = read_json(history / 'RESUME_RECEIPT.json')
    write_json(root / 'MODEL_ROSTER_REVISION.json', {
        'version': 'v2-model-roster-2', 'date': '2026-10-07', 'user_authorized': True, 'user_quote': QUOTE,
        'previous_model_names': [m['name'] for m in old['models']], 'model_names': NAMES,
        'parent_plan_sha256': parent_sha, 'frozen_md_sha256': old['frozen_md_sha256'],
        'preregistration_sha256': digest((root / 'preregistration.json').read_bytes()),
        'post_start': True, 'thresholds_changed': False, 'provider_metadata_file': 'PROVIDER_MODELS_ROSTER2.json',
        'provider_metadata_sha256': digest((root / 'PROVIDER_MODELS_ROSTER2.json').read_bytes()),
        'valid_prior_observations': receipt['counts'].get('ok', 0), 'kimi_calls_before_replacement': receipt['kimi_calls'],
        'cumulative_reserved_calls_before_amendment': receipt['cumulative_reserved_calls'],
        'analysis_model_names': NAMES, 'h1_min_models_same_direction': 2,
        'reason': 'human corrected five request IDs and replaced Kimi-K2.6 with GLM-5.3; no scoring performed',
        'preregistration_status': 'original five-model preregistration remains frozen; amended roster must be disclosed as post-start',
        'retention': 'all completed answers, errors, pauses and unknown interrupted calls retained; no result-based reruns'})
    configured = models(root)
    if [m['name'] for m in configured] != NAMES: raise ValueError('unexpected corrected roster')
    previous = {m['name']: m for m in old['models']}
    for model in configured:
        if model['name'] in previous and model != previous[model['name']]:
            raise ValueError('unchanged models must retain the exact protocol')
    amendment = read_json(root / 'MODEL_ROSTER_REVISION.json')
    if amendment['parent_plan_sha256'] != parent_sha:
        raise ValueError('amendment parent differs')
    old.update(version='v2-run-4', parent_plan_sha256=parent_sha, models=configured,
        roster_revision={'file': 'MODEL_ROSTER_REVISION.json', 'sha256': digest((root / 'MODEL_ROSTER_REVISION.json').read_bytes()),
            'post_start': True, 'frozen_preregistration_unchanged': True},
        resume={'parent_version': 'v2-run-3', 'receipt': 'history/v2-run-3/RESUME_RECEIPT.json',
            'receipt_sha256': digest((history / 'RESUME_RECEIPT.json').read_bytes()),
            'records': 'history/v2-run-3/resume_records.jsonl',
            'records_sha256': digest((history / 'resume_records.jsonl').read_bytes())})
    old['analysis'] = 'frozen preregistration.json thresholds/cases; explicit post-start model roster amendment; majority case primary; failures retained'
    for name in old['implementation']:
        old['implementation'][name] = digest((root / name).read_bytes())
    for name in ['resume.py', 'register_roster.py', 'MODEL_ROSTER_REVISION.json',
                 'PREREGISTRATION_AMENDMENT_20261007.md', 'PROVIDER_MODELS_ROSTER2.json']:
        old['implementation'][name] = digest((root / name).read_bytes())
    write_json(root / 'RUN_PLAN.json', old)
    sha = digest((root / 'RUN_PLAN.json').read_bytes()); (root / 'RUN_PLAN.sha256').write_bytes((sha + '\n').encode())
    approved = read_json(history / 'API_APPROVAL.json')
    approved.update(plan_sha256=sha, mock_report_sha256=None, models=NAMES,
        parent_approval_sha256=digest((history / 'API_APPROVAL.json').read_bytes()),
        roster_amendment='MODEL_ROSTER_REVISION.json', user_roster_correction_quote=QUOTE,
        transport_revision='v2-run-4; Kimi replaced by GLM before any Kimi call; resume ALL prior slots; cumulative caps unchanged')
    write_json(root / 'API_APPROVAL.json', approved)
    verify(root)
    print('PASS: corrected roster and resume locked; new mock binding pending')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--archive', action='store_true')
    args = p.parse_args(); archive() if args.archive else register()
