"""Human scope correction: add Kimi and give each of six models one worker."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from collections import Counter
import json
import yaml
from bench.v2.runtime import V2, canonical, digest, read_json, write_json

QUOTE = '我说错了，我的意思是，再加上kimi-k2.6吧，6个一起跑'


def archive(root=V2):
    from bench.v2.revision_snapshot import capture
    receipt = capture(root, 'v2-run-6', 'four_worker_run6_rules_package')
    print('PASS: stopped four-worker cohort archived; ' + str(receipt['observations']) + ' observations retained')


def register(root=V2, accept_qwen_fp8=False, qwen_quote=None):
    from bench.v2.freeze import verify as frozen_verify
    from bench.v2.plan import models, verify
    frozen_verify(root)
    history = root / 'history/v2-run-6'
    parent_sha = digest((history / 'RUN_PLAN.json').read_bytes())
    if digest((root / 'RUN_PLAN.json').read_bytes()) != parent_sha: raise ValueError('unexpected six-model parent')
    old = read_json(history / 'RUN_PLAN.json')
    receipt = read_json(history / 'RESUME_RECEIPT.json')
    previous_names = [m['name'] for m in old['models']]
    configured = [dict(m) for m in old['models']]
    audit_only = []
    if accept_qwen_fp8:
        if not qwen_quote: raise ValueError('FP8 acceptance must come directly from the human')
        qwen = next(m for m in configured if m['name'] == 'Qwen3.8-27B')
        qwen.update(name='Qwen3.8-27B-FP8', provider_model_name='Qwen3.8-27B',
            accepted_response_ids=['qwen3.8-27b', 'Qwen3.8-27B', 'qwen3.8-27b-fp8'])
        audit_only = ['Qwen3.8-27B']
    kimi = {k: v for k, v in configured[1].items() if k not in ('accepted_response_ids', 'provider_model_name')}
    kimi.update(name='Kimi-K2.6', requested_model_id='kimi-k2.6')
    configured.append(kimi)
    names = [m['name'] for m in configured]
    source = [json.loads(line) for line in (history / 'resume_records.jsonl').read_text(encoding='utf-8').splitlines()]
    carried = [r for r in source if r['record_type'] == 'observation' and r['model'] not in audit_only]
    receipt.update(audit_only_models=audit_only, carried_observations=len(carried),
        carried_counts=dict(Counter(r['status'] for r in carried)),
        audit_only_observations=receipt['observations'] - len(carried))
    write_json(history / 'RESUME_RECEIPT.json', receipt)
    write_json(root / 'SIX_MODELS_REVISION.json', {'version': 'v2-model-roster-4', 'date': '2026-10-08',
        'user_authorized': True, 'user_quote': QUOTE, 'previous_model_names': previous_names, 'model_names': names,
        'parent_plan_sha256': parent_sha, 'frozen_md_sha256': old['frozen_md_sha256'],
        'preregistration_sha256': digest((root / 'preregistration.json').read_bytes()),
        'post_start': True, 'thresholds_changed': False, 'h1_min_models_same_direction': 2,
        'model_count': 6, 'max_workers': 6, 'per_model_limit': 1,
        'provider_metadata_file': 'PROVIDER_MODELS_SIX.json',
        'provider_metadata_sha256': digest((root / 'PROVIDER_MODELS_SIX.json').read_bytes()),
        'qwen_fp8_user_authorized': accept_qwen_fp8, 'qwen_fp8_user_quote': qwen_quote,
        'qwen_fp8_policy': 'fresh explicitly labelled FP8 cohort; old identity failures/pauses stay audit-only' if accept_qwen_fp8 else 'preserve identity pause until human accepts FP8',
        'expected_model_observations': 864, 'full_format_repair_scenario_calls': 1728,
        'cumulative_budget_increased': False, 'cumulative_reserved_calls': receipt['cumulative_reserved_calls'],
        'existing_observations': receipt['observations'], 'carried_observations': len(carried),
        'primary_new_observations_before_change': receipt['primary_new_observations'],
        'primary_new_called_attempts_before_change': sum(r['record_type'] == 'attempt' and r.get('called') is True and r['case_id'].startswith('new_') for r in source),
        'analysis': 'six-model roster disclosed as post-start; numeric thresholds unchanged; at least2 of6 models same direction; not claim original five-model preregistration'})
    (root / 'models.yaml').write_bytes(yaml.safe_dump({'models': configured}, sort_keys=False, allow_unicode=True).encode('utf-8'))
    if models(root) != configured: raise ValueError('six model registration differs')
    protected = sorted(set(old['resume'].get('protected_versions', []) + ['v2-run-6']))
    old.update(version='v2-run-7', parent_plan_sha256=parent_sha, models=configured,
        execution={'max_workers': 6, 'per_model_limit': 1, 'queue_policy': 'one serial B then C2 lane per model; all six lanes concurrently'},
        six_model_revision={'file': 'SIX_MODELS_REVISION.json', 'sha256': digest((root / 'SIX_MODELS_REVISION.json').read_bytes())},
        resume={'parent_version': 'v2-run-6', 'receipt': 'history/v2-run-6/RESUME_RECEIPT.json',
            'receipt_sha256': digest((history / 'RESUME_RECEIPT.json').read_bytes()),
            'records': 'history/v2-run-6/resume_records.jsonl',
            'records_sha256': digest((history / 'resume_records.jsonl').read_bytes()),
            'protected_versions': protected, 'audit_only_models': audit_only})
    for name in old['implementation']: old['implementation'][name] = digest((root / name).read_bytes())
    for name in ['revision_snapshot.py', 'register_six.py', 'SIX_MODELS_REVISION.json', 'PROVIDER_MODELS_SIX.json',
                 'PREREGISTRATION_AMENDMENT_SIX_20261007.md']:
        old['implementation'][name] = digest((root / name).read_bytes())
    write_json(root / 'RUN_PLAN.json', old)
    sha = digest((root / 'RUN_PLAN.json').read_bytes()); (root / 'RUN_PLAN.sha256').write_bytes((sha + '\n').encode())
    approved = read_json(history / 'API_APPROVAL.json')
    approved.update(plan_sha256=sha, mock_report_sha256=None, models=names,
        parent_approval_sha256=digest((history / 'API_APPROVAL.json').read_bytes()),
        user_six_model_authorization_quote=QUOTE, six_model_amendment='SIX_MODELS_REVISION.json',
        approval_context='Human added Kimi and requested six lanes; previous numeric caps and protocol acceptance inherited unchanged;864 observations, max1 format repair',
        transport_revision='v2-run-7; six models, six workers; retained prior outputs; original cumulative caps')
    write_json(root / 'API_APPROVAL.json', approved)
    verify(root)
    print('PASS: six models/six workers locked; inherited budget unchanged; new mock binding pending')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--archive', action='store_true')
    p.add_argument('--accept-qwen-fp8', action='store_true'); p.add_argument('--qwen-quote')
    args = p.parse_args(); archive() if args.archive else register(accept_qwen_fp8=args.accept_qwen_fp8, qwen_quote=args.qwen_quote)
