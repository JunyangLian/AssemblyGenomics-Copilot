"""Read-only run progress and provider usage, never QC scoring or credential access."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from collections import Counter
import json
from bench.v2.runtime import V2, canonical, digest, read_json, write_json


def progress(root=V2):
    data = (root / 'RUN_PLAN.json').read_bytes(); plan_sha = digest(data)
    if plan_sha != (root / 'RUN_PLAN.sha256').read_text().strip(): raise ValueError('run plan hash differs')
    plan = json.loads(data)
    observations, attempts, incomplete_lines = [], [], 0
    for p in sorted((root / 'runs').glob('*/records.jsonl')):
        if 'mock-' in p.parent.name or p.parent.name.startswith('v2-reuse-'): continue
        for line in p.read_text(encoding='utf-8').splitlines():
            try: row = json.loads(line)
            except json.JSONDecodeError:
                incomplete_lines += 1; continue  # explicitly counted transient partial write
            if row.get('plan_sha256') != plan_sha or row.get('mode') != 'api': continue
            if row['record_type'] == 'attempt': attempts.append(row)
            elif row['record_type'] == 'observation': observations.append(row)
    slots = [(r['model'], r['group'], r['case_id'], r['repetition']) for r in observations]
    if len(slots) != len(set(slots)): raise ValueError('duplicate current API observation')
    ledger = read_json(root / 'runs/API_LEDGER.json')
    groups = []
    for m in plan['models']:
        for group in plan['groups']:
            selected = [r for r in observations if r['model'] == m['name'] and r['group'] == group]
            groups.append({'model': m['name'], 'requested_model_id': m['requested_model_id'], 'group': group,
                'planned': 72, 'completed': len(selected), 'counts': dict(Counter(r['status'] for r in selected))})
    used = [r for r in attempts if isinstance(r.get('usage'), dict)]
    wanted = 720
    active = (root / 'runs/API_ACTIVE.lock').exists()
    result = {'status': 'running' if active else ('complete' if len(observations) == wanted else 'incomplete'),
        'date': '2026-10-07', 'plan_version': plan['version'], 'plan_sha256': plan_sha,
        'key_env': 'INTERN_DISCOVERY_API_KEY', 'credential_setup': 'local user environment; hidden input',
        'planned_current_observations': wanted, 'completed_current_observations': len(observations),
        'current_status_counts': dict(Counter(r['status'] for r in observations)), 'groups': groups,
        'current_logged_called_attempts': sum(r.get('called') is True for r in attempts),
        'cumulative_reserved_calls': ledger['calls'], 'input_reserved': ledger['input_reserved'],
        'output_reserved': ledger['output_reserved'], 'max_calls': 1440,
        'max_input_tokens': 28706760, 'max_output_tokens': 11796480,
        'provider_usage_recorded_attempts': len(used),
        'provider_prompt_tokens_reported': sum(r['usage'].get('prompt_tokens') or 0 for r in used),
        'provider_completion_tokens_reported': sum(r['usage'].get('completion_tokens') or 0 for r in used),
        'provider_usage_exceeded_reservation': ledger.get('provider_usage_exceeded_reservation', False),
        'fee': None, 'fee_note': 'provider price unknown; reservations are not billed token usage',
        'transient_incomplete_jsonl_lines': incomplete_lines, 'hypotheses_scored': False,
        'prior_cohorts': ['history/v2-run-1/TRANSPORT_FAILURE.json', 'history/v2-run-2/TRANSPORT_FAILURE.json']}
    write_json(root / 'API_START_STATUS.json', result)
    print(json.dumps({k: result[k] for k in ('status','plan_version','completed_current_observations',
        'current_status_counts','current_logged_called_attempts','cumulative_reserved_calls',
        'provider_prompt_tokens_reported','provider_completion_tokens_reported')}, ensure_ascii=False))
    return result


if __name__ == '__main__': progress()
