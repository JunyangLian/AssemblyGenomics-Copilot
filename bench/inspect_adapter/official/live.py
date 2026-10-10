"""Bounded real run of pinned, unmodified official tasks; Inspect owns grading.

The small subset is for framework reproduction, not independent model ranking.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
from importlib.metadata import version
import json
import os
from pathlib import Path

from bench.inspect_adapter import pilot
from bench.inspect_adapter.official import run

DIRECTORY = run.ROOT / 'live1'
WORK = pilot.ROOT / 'work/official_live'
QUOTE = '可以，小规模跑完，看看够不够写简历，如果不够就跑全量'


def tasks():
    addition, source = run.upstream_task()
    loaded = {}
    for name in ('tool_use', 'theory_of_mind'):
        spec = importlib.util.spec_from_file_location('official_live_' + name, run.ROOT / 'upstream' / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded[name] = module
    theory = loaded['theory_of_mind'].theory_of_mind(critique=False)
    data_path = Path(__import__('inspect_ai').__file__).parent / 'dataset/_examples/theory_of_mind.jsonl'
    if pilot.sha(data_path.read_bytes()) != source['files']['theory_of_mind.jsonl']['sha256']:
        raise ValueError('installed official dataset differs from pinned source')
    return [addition, loaded['tool_use'].parallel_add(), theory]


def candidates():
    selected = []
    for task, name, count in zip(tasks(), ('addition_problem', 'parallel_add', 'theory_of_mind'), (1, 1, 10)):
        for index, sample in enumerate(list(task.dataset)[:count], 1):
            serialized = sample.model_dump(mode='json')
            public_input = serialized['input']
            if isinstance(public_input, list):
                # Inspect assigns random transport IDs; freeze only source message content.
                public_input = [{'role': message['role'], 'content': message['content']} for message in public_input]
            selected.append({'task': name, 'index': index,
                             'input_sha256': pilot.sha(pilot.canonical(public_input)),
                             'target': serialized['target'],
                             'target_sha256': pilot.sha(pilot.canonical(serialized['target']))})
    return selected


def plan():
    original = pilot.draft_plan()
    for name in ('case_ids', 'evidence_support_scoring', 'action_safety_scoring', 'review_kind'):
        original.pop(name, None)
    return {**original, 'version': 'inspect-official-small-1',
            'purpose': 'official framework reproduction and internship demonstration; not QC/H1-H3 or independent model ranking',
            'task_factories': ['addition_problem', 'parallel_add', 'theory_of_mind'],
            'sample_counts': [1, 1, 10], 'official_theory_total': 100, 'critique': False,
            'limit_per_task': 10, 'grading': 'unchanged model_graded_fact; same evaluated model grades theory answers',
            'max_http_requests': 32, 'max_input_proxy_tokens': 100000,
            'max_output_token_reservation': 65536, 'max_request_bytes': 80000,
            'max_tokens': 2048, 'timeout_seconds': 60, 'stop_http_statuses': [400, 401, 403, 404, 422, 429],
            'transport': {'NO_PROXY': 'api.siliconflow.cn', 'tls_verification': True},
            'reference_cost_cap_cny_uncached': 0.889824,
            'estimate_not_billing_guarantee': True,
            'expected_calls': '20 solve/grade requests plus typically 4 tool-loop requests; tool loops can vary',
            'full_run_policy': 'not started by this entry; first assess trace completeness and contribution, not only score',
            'resume_assessment': ['official sources pinned', '12 planned outcomes retained including errors',
                                  'native solve/grade/tool traces recorded', 'domain real pilot and offline parity already available']}


def file_hashes():
    files = {'live.py': Path(__file__), 'run.py': run.ROOT / 'run.py',
             'SOURCE.json': run.ROOT / 'SOURCE.json', 'pilot.py': pilot.ROOT / 'pilot.py',
             'requirements-pilot.lock.txt': pilot.ROOT / 'requirements-pilot.lock.txt'}
    files.update({'upstream/' + name: run.ROOT / 'upstream' / name
                  for name in pilot.read_json(run.ROOT / 'SOURCE.json')['files']})
    return {name: pilot.sha(path.read_bytes()) for name, path in files.items()}


def prepare():
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    if (DIRECTORY / 'FROZEN.json').exists():
        raise ValueError('official small run already frozen; no overwrite')
    pilot.write_json(DIRECTORY / 'PLAN.json', plan())
    pilot.write_json(DIRECTORY / 'TARGETS.json', candidates())
    pilot.write_json(DIRECTORY / 'APPROVAL.json', {'user_quote': QUOTE, 'scope': 'small official live run first',
                       'model_policy': 'continue previously specified SiliconFlow DeepSeek-V4-Flash',
                       'budget_policy': 'bounded small run within reference one CNY; no automatic full run'})
    frozen = {'source_files': file_hashes(), 'documents': {name: pilot.sha((DIRECTORY / name).read_bytes())
              for name in ('PLAN.json', 'TARGETS.json', 'APPROVAL.json')}}
    pilot.write_json(DIRECTORY / 'FROZEN.json', frozen)
    rows = ['# Official small run frozen before calls', '',
            'User authorized small real run first; original official targets retained. No provider calls at freeze.', '',
            '| Task | Index | Target SHA-256 |', '|---|---:|---|']
    rows += [f"| {r['task']} | {r['index']} | {r['target_sha256']} |" for r in candidates()]
    (DIRECTORY / 'FROZEN.md').write_text('\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
    print('FROZEN: 12 official targets; no model calls; small run only')


def approved():
    frozen = pilot.read_json(DIRECTORY / 'FROZEN.json')
    if frozen['source_files'] != file_hashes() or any(
        pilot.sha((DIRECTORY / name).read_bytes()) != expected for name, expected in frozen['documents'].items()):
        raise ValueError('official frozen sources or plan changed')
    if (pilot.read_json(DIRECTORY / 'PLAN.json') != plan() or
        pilot.read_json(DIRECTORY / 'TARGETS.json') != candidates() or
        pilot.read_json(DIRECTORY / 'APPROVAL.json')['user_quote'] != QUOTE):
        raise ValueError('official selection or approval differs from freeze')
    return pilot.read_json(DIRECTORY / 'PLAN.json')


def execute():
    setup = approved()  # Before reading credentials or importing providers.
    if any(version(package) != expected for package, expected in setup['dependency_versions'].items()):
        raise ValueError('installed dependencies differ from frozen plan')
    if not os.environ.get(setup['key_env']):
        raise ValueError('local credential environment variable is unset')
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log
    from inspect_ai.model import get_model, GenerateConfig
    import httpx2

    key = os.environ[setup['key_env']]
    frozen_hash = pilot.sha((DIRECTORY / 'FROZEN.json').read_bytes())
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_official_' + frozen_hash[:12]
    output = WORK / run_id
    pilot.claim_run(output.parent, frozen_hash, run_id)
    output.mkdir(parents=True, exist_ok=False)
    guard = pilot.RequestBudget(setup)

    def budget_record():
        pilot.write_json(output / 'REQUEST_BUDGET.json', {'calls': guard.calls, 'input_proxy': guard.input_proxy,
            'output_reserved': guard.output_reserved, 'records': guard.records, 'stopped_reason': guard.stopped_reason})

    async def reserve(request):
        guard.reserve(request.method, str(request.url), request.content)
        request.extensions['official_budget_index'] = len(guard.records) - 1
        budget_record()

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
            raise ValueError('provider used reasoning mode despite nonthinking configuration')
        budget_record()

    client = httpx2.AsyncClient(event_hooks={'request': [reserve], 'response': [observe]},
                              timeout=setup['timeout_seconds'], follow_redirects=False)
    config = GenerateConfig(temperature=0, max_tokens=2048, max_retries=0, timeout=60,
                            attempt_timeout=60, max_connections=1, extra_body=setup['extra_body'])
    try:
        model = get_model('openai-api/siliconflow/' + setup['model_id'], base_url=setup['base_url'],
                          api_key_var=setup['key_env'], http_client=client, config=config,
                          max_retries=0, stream=False, strict_tools=False, emulate_tools=False, memoize=False)
        logs = inspect_eval(tasks(), model=model, limit=10, display='none',
                            log_dir=str(output / 'logs'), log_format='json', log_model_api=False,
                            max_samples=1, max_tasks=1, retry_on_error=0, max_retries=0,
                            message_limit=10, log_level='warning')
        rows = []
        by_task = {read_eval_log(info.location).eval.task: info for info in logs}
        if len(logs) != 3 or set(by_task) != set(setup['task_factories']):
            raise ValueError('official task logs missing, duplicated or replaced')
        for task_name, count in zip(setup['task_factories'], setup['sample_counts']):
            info = by_task[task_name]
            log = read_eval_log(info.location)
            samples = {str(s.id): s for s in log.samples or []}
            for index in range(1, count + 1):
                sample = samples.get(str(index))
                score = next(iter(sample.scores.values()), None) if sample and sample.scores else None
                rows.append({'task': task_name, 'index': index,
                    'status': 'missing' if sample is None else 'execution_error' if sample.error else
                              'unscored' if score is None else 'scored',
                    'score': score.value if score else None,
                    'output': sample.output.completion if sample and sample.output else '',
                    'explanation': score.explanation if score else None,
                    'tool_calls': sum(m.role == 'tool' for m in sample.messages) if sample else 0})
        pilot.write_json(output / 'RESULTS.json', {'run_id': run_id, 'frozen_sha256': frozen_hash,
            'planned_observations': 12, 'rows': rows, 'calls': guard.calls,
            'purpose': setup['purpose'], 'same_model_grading': True})
        print('RECORDED: 12 planned official samples; original Inspect scoring; inspect RESULTS before assessment')
    finally:
        budget_record()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--api', action='store_true')
    args = parser.parse_args()
    prepare() if args.prepare else execute()
