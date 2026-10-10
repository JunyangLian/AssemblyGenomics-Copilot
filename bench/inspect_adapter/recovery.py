"""Explicitly approved continuation after a transport failure; never reset budget."""
import argparse
import os
from pathlib import Path

from bench.inspect_adapter import pilot

ROOT = pilot.ROOT
PREVIOUS = ROOT / 'work/pilot/20261010T092934Z_deepseek-ai_DeepSeek-V4-Flash_c4e9b63551f4'
ORIGINAL_PLAN = pilot.draft_plan
ORIGINAL_IMPLEMENTATION = pilot.implementation_hashes


def remaining_plan(plan, budget, provenance):
    remaining = dict(plan)
    for limit, consumed in [('max_http_requests', 'calls'),
                             ('max_input_proxy_tokens', 'input_proxy'),
                             ('max_output_token_reservation', 'output_reserved')]:
        used = budget[consumed]
        if not isinstance(used, int) or used < 0 or used >= plan[limit]:
            raise ValueError('previous budget invalid or exhausted')
        remaining[limit] = plan[limit] - used
    remaining['version'] = 'inspect-development-pilot-1-siliconflow-recovery-1'
    remaining['previous_attempt'] = provenance
    remaining['transport'] = {'NO_PROXY': 'api.siliconflow.cn', 'tls_verification': True}
    return remaining


def recovery_plan():
    # No API keys, response bodies or environment secrets are read here.
    original = pilot.read_json(ROOT / 'pilot/plan.draft.json')
    if original != ORIGINAL_PLAN():
        raise ValueError('original proposal changed')
    frozen = ROOT / 'pilot/FROZEN.json'
    budget_path, results_path = PREVIOUS / 'REQUEST_BUDGET.json', PREVIOUS / 'RESULTS.json'
    budget, results = pilot.read_json(budget_path), pilot.read_json(results_path)
    if (results['frozen_sha256'] != pilot.sha(frozen.read_bytes()) or
        len(budget['records']) != budget['calls'] or
        any(record.get('status_code') is not None for record in budget['records']) or
        len(results['rows']) != 4 or any(row['status'] != 'execution_error' for row in results['rows'])):
        raise ValueError('recovery restricted to this preserved no-response transport failure')
    provenance = {'run_id': PREVIOUS.name, 'frozen_sha256': pilot.sha(frozen.read_bytes()),
                  'budget_sha256': pilot.sha(budget_path.read_bytes()),
                  'results_sha256': pilot.sha(results_path.read_bytes()),
                  'previous_reservations': {key: budget[key] for key in ('calls', 'input_proxy', 'output_reserved')}}
    return remaining_plan(original, budget, provenance)


def configure():
    # Reuse the frozen implementation; the recovery wrapper is also hashed.
    pilot.PILOT = ROOT / 'pilot_recovery'
    pilot.draft_plan = recovery_plan
    pilot.implementation_hashes = lambda: {
        **ORIGINAL_IMPLEMENTATION(), 'recovery.py': pilot.sha((ROOT / 'recovery.py').read_bytes())}


def prepare():
    configure()
    pilot.prepare()
    plan = recovery_plan()
    estimate = pilot.read_json(pilot.PILOT / 'ESTIMATE.json')
    estimate.update({'hard_request_count_cap': plan['max_http_requests'],
                     'input_proxy_reservation_cap': plan['max_input_proxy_tokens'],
                     'output_requested_token_ceiling': plan['max_output_token_reservation'],
                     'previous_attempt': plan['previous_attempt'],
                     'peak_reference_estimate_cny': (
                         plan['max_input_proxy_tokens'] * 3 + plan['max_output_token_reservation'] * 9) / 1000000})
    pilot.write_json(pilot.PILOT / 'ESTIMATE.json', estimate)


def execute():
    configure()
    plan, _ = pilot.approved()
    if plan != recovery_plan():
        raise ValueError('preserved previous attempt or recovery conditions changed')
    # Keep TLS verification; bypass only the failing proxy route for this host.
    os.environ['NO_PROXY'] = plan['transport']['NO_PROXY']
    pilot.execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--freeze', action='store_true')
    action.add_argument('--api', action='store_true')
    parser.add_argument('--approval-quote')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.freeze:
        configure()
        pilot.freeze(args.approval_quote or '')
    else:
        execute()
