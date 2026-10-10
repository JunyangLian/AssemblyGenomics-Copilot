"""Complete preselected unscored official samples within the original ledger.

Inspect's native sample_id selection and eval_async do the execution. Completed
samples are not called again. Original errors and unscheduled slots stay saved.
"""
import argparse
import asyncio
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path

from bench.inspect_adapter import pilot
from bench.inspect_adapter.official import live, run

DIRECTORY = run.ROOT / 'live1_recovery'
PREVIOUS = pilot.ROOT / 'work/official_live/20261010T141416Z_official_543309a81bef'
WORK = pilot.ROOT / 'work/official_recovery'


def originals():
    return {str(path.relative_to(PREVIOUS)).replace('\\', '/'): pilot.sha(path.read_bytes())
            for path in [PREVIOUS / 'RESULTS.json', PREVIOUS / 'REQUEST_BUDGET.json', *sorted((PREVIOUS / 'logs').glob('*.json'))]}


def selection():
    rows = pilot.read_json(PREVIOUS / 'RESULTS.json')['rows']
    return {name: [r['index'] for r in rows if r['task'] == name and r['status'] != 'scored']
            for name in live.plan()['task_factories'] if any(r['task'] == name and r['status'] != 'scored' for r in rows)}


def prepare():
    live.approved()
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    if (DIRECTORY / 'FROZEN.json').exists():
        raise ValueError('recovery already frozen; no overwrite')
    ledger = pilot.read_json(PREVIOUS / 'REQUEST_BUDGET.json')
    if ledger['stopped_reason']:
        raise ValueError('authentication/quota stop cannot be resumed automatically')
    pilot.write_json(DIRECTORY / 'PLAN.json', {'selection': selection(), 'previous': PREVIOUS.name,
        'original_approval': live.QUOTE, 'budget_policy': 'inherit original ledger; cumulative limits unchanged',
        'calls_already_reserved': ledger['calls'], 'calls_remaining': live.plan()['max_http_requests'] - ledger['calls'],
        'parameter_changes': {'fail_on_error': False},
        'scheduling_reason': 'finish originally approved small subset despite individual errors',
        'sdk_and_sample_auto_retries': 0, 'effective_policy': 'retain completed originals; latest outcome for fixed retry IDs even if failed',
        'full_run': False, 'sources': originals()})
    pilot.write_json(DIRECTORY / 'FROZEN.json', {'implementation_sha256': pilot.sha(Path(__file__).read_bytes()),
        'original_frozen_sha256': pilot.sha((live.DIRECTORY / 'FROZEN.json').read_bytes()),
        'plan_sha256': pilot.sha((DIRECTORY / 'PLAN.json').read_bytes())})
    print('FROZEN: seven incomplete original slots only; cumulative 32 calls unchanged')


def approved():
    setup = live.approved()
    frozen = pilot.read_json(DIRECTORY / 'FROZEN.json')
    plan = pilot.read_json(DIRECTORY / 'PLAN.json')
    if (frozen['implementation_sha256'] != pilot.sha(Path(__file__).read_bytes()) or
        frozen['original_frozen_sha256'] != pilot.sha((live.DIRECTORY / 'FROZEN.json').read_bytes()) or
        frozen['plan_sha256'] != pilot.sha((DIRECTORY / 'PLAN.json').read_bytes()) or
        plan['sources'] != originals() or plan['selection'] != selection()):
        raise ValueError('recovery or original records changed')
    return setup, plan


def execute():
    setup, retry = approved()
    if any(version(package) != expected for package, expected in setup['dependency_versions'].items()):
        raise ValueError('dependency versions differ from original run')
    if not os.environ.get(setup['key_env']):
        raise ValueError('local credential environment variable is unset')
    from inspect_ai import eval_async
    from inspect_ai.log import read_eval_log
    from inspect_ai.model import get_model, GenerateConfig
    import httpx2

    key = os.environ[setup['key_env']]
    before = pilot.read_json(PREVIOUS / 'REQUEST_BUDGET.json')
    guard = pilot.RequestBudget(setup)
    guard.calls, guard.input_proxy, guard.output_reserved = before['calls'], before['input_proxy'], before['output_reserved']
    guard.records = before['records']
    frozen_hash = pilot.sha((DIRECTORY / 'FROZEN.json').read_bytes())
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_official_recovery_' + frozen_hash[:12]
    output = WORK / run_id
    pilot.claim_run(WORK, frozen_hash, run_id)
    output.mkdir(parents=True, exist_ok=False)

    def save():
        pilot.write_json(output / 'REQUEST_BUDGET.json', {'calls': guard.calls, 'input_proxy': guard.input_proxy,
            'output_reserved': guard.output_reserved, 'records': guard.records, 'stopped_reason': guard.stopped_reason,
            'previous_calls': before['calls']})

    async def reserve(request):
        guard.reserve(request.method, str(request.url), request.content)
        request.extensions['official_budget_index'] = len(guard.records) - 1
        save()

    async def observe(response):
        data = await response.aread()
        if key.encode() in data:
            data = data.replace(key.encode(), b'[CREDENTIAL_REDACTED]')
            response._content = data
        record = guard.records[response.request.extensions['official_budget_index']]
        record.update(status_code=response.status_code, response_body_sha256=pilot.sha(data))
        try:
            body = json.loads(data)
        except (ValueError, UnicodeDecodeError):
            body = {}
        record.update(returned_model_id=body.get('model'), usage=body.get('usage'))
        if response.status_code in setup['stop_http_statuses']:
            guard.stopped_reason = 'provider_auth_or_quota_status_' + str(response.status_code)
        if 200 <= response.status_code < 300 and body.get('model') not in setup['accepted_response_ids']:
            guard.stopped_reason = 'unapproved_returned_model_identity'
            raise ValueError('unapproved returned model identity')
        if ((body.get('usage') or {}).get('completion_tokens_details') or {}).get('reasoning_tokens', 0):
            guard.stopped_reason = 'unexpected_reasoning_usage'
            raise ValueError('unexpected provider reasoning mode')
        save()

    async def evaluate():
        async with httpx2.AsyncClient(event_hooks={'request': [reserve], 'response': [observe]},
                                     timeout=60, follow_redirects=False) as client:
            config = GenerateConfig(temperature=0, max_tokens=2048, max_retries=0, timeout=60,
                                    attempt_timeout=60, max_connections=1, extra_body=setup['extra_body'])
            model = get_model('openai-api/siliconflow/' + setup['model_id'], base_url=setup['base_url'],
                api_key_var=setup['key_env'], http_client=client, config=config, max_retries=0,
                stream=False, strict_tools=False, emulate_tools=False, memoize=False)
            generated = []
            factories = dict(zip(setup['task_factories'], live.tasks()))
            for name, ids in retry['selection'].items():
                generated += await eval_async(factories[name], model=model, sample_id=ids,
                    log_dir=str(output / 'logs'), log_format='json', log_model_api=False,
                    max_samples=1, max_tasks=1, fail_on_error=False, retry_on_error=0, max_retries=0,
                    message_limit=10, log_level='warning')
            return generated

    try:
        logs = asyncio.run(evaluate())
        by_task = {read_eval_log(info.location).eval.task: read_eval_log(info.location) for info in logs}
        if set(by_task) != set(retry['selection']) or len(logs) != len(retry['selection']):
            raise ValueError('recovery task logs missing or duplicated')
        retried = []
        for name, ids in retry['selection'].items():
            samples = {int(s.id): s for s in by_task[name].samples or []}
            for index in ids:
                sample = samples.get(index)
                score = next(iter(sample.scores.values()), None) if sample and sample.scores else None
                retried.append({'task': name, 'index': index,
                    'status': 'missing' if sample is None else 'execution_error' if sample.error else 'unscored' if score is None else 'scored',
                    'score': score.value if score else None, 'output': sample.output.completion if sample and sample.output else '',
                    'explanation': score.explanation if score else None,
                    'tool_calls': sum(m.role == 'tool' for m in sample.messages) if sample else 0})
        original = pilot.read_json(PREVIOUS / 'RESULTS.json')['rows']
        updates = {(r['task'], r['index']): r for r in retried}
        effective = [updates.get((r['task'], r['index']), r) for r in original]
        pilot.write_json(output / 'RESULTS.json', {'run_id': run_id, 'original_run_id': PREVIOUS.name,
            'recovery_frozen_sha256': frozen_hash, 'original_attempt_rows': original,
            'retry_rows': retried, 'effective_rows': effective, 'planned_unique_samples': 12,
            'cumulative_calls': guard.calls, 'same_model_grading': True,
            'policy': retry['effective_policy']})
        print('RECORDED: seven fixed retry slots; 12 effective outcomes; original failures preserved')
    finally:
        save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--api', action='store_true')
    args = parser.parse_args()
    prepare() if args.prepare else execute()
