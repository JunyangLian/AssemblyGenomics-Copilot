"""Approved T1 regression through native Inspect; frozen legacy answers unchanged."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import time

from bench.inspect_adapter import pilot, structured_pilot, t1_regression as regression

DIRECTORY = regression.DIRECTORY / 'live1'
WORK = regression.ROOT / 'work/t1_regression_live'
QUOTE = '允许'
QUESTION = ('SiliconFlow DeepSeek-V4-Flash，19题×正文/工具两条件×3次，共114条观测；'
            '累计最多399次HTTP请求、输入代理200万、输出申请379,392 token，'
            '按已有价格快照参考约¥9.41（不是账单保证）；原答案不变，密钥仅从本地环境变量读取。')


def plan():
    draft = regression.checked_plan()
    return {**draft, 'version': 'inspect-t1-regression-live-1', 'api_call_authorized': True,
            'max_http_requests': 399, 'max_input_proxy_tokens': 2_000_000,
            'max_output_token_reservation': 379392, 'max_request_bytes': 80000,
            'max_tokens': 2048, 'final_response_format': {'type': 'json_object'},
            'accepted_response_ids': [draft['model_id']],
            'stop_http_statuses': [400, 401, 403, 404, 422, 429],
            'transport': {'direct': True, 'tls_verification': True, 'follow_redirects': False},
            'dependency_versions': pilot.draft_plan()['dependency_versions'],
            'sdk_retries': 0, 'inspect_retries': 0, 'format_retries': 0,
            'analysis': {'primary_unit': 'case; separate 2/3 majority verdict and root, no majority counts as wrong',
                         'secondary_unit': 'all planned observations; missing/error/invalid counts as wrong',
                         'scope': 'descriptive seen regression; no H1-H3 or generalization claim'}}


def file_hashes():
    root = regression.ROOT
    paths = [Path(__file__), root / 't1_regression.py', root / 'readonly.py', root / 'bridge.py',
             root / 'pilot.py', root / 'structured_pilot.py', root / 'requirements-pilot.lock.txt',
             root.parent / 'harness_common.py', root.parent / 'v2/runtime.py',
             regression.DIRECTORY / 'PLAN.draft.json', regression.DIRECTORY / 'LEGACY_TARGETS.json']
    return {str(p.relative_to(root.parent)).replace('\\', '/'): pilot.sha(p.read_bytes()) for p in paths}


def prepare():
    setup = plan()
    if (DIRECTORY / 'FROZEN.json').exists():
        raise ValueError('already frozen; use a new version, never overwrite')
    pilot.write_json(DIRECTORY / 'PLAN.json', setup)
    pilot.write_json(DIRECTORY / 'APPROVAL.json', {'user_quote': QUOTE, 'approved_question': QUESTION,
        'authorization_date': '2026-10-11', 'source': 'human user in current conversation',
        'answers': 'unchanged, already approved v2 originals; no new target assignment'})
    rows = ['# T1 regression live 1 freeze', '', 'Frozen before real calls; user approved the stated bounds.', '',
            '| Original case | expected.json SHA-256 | Status |', '|---|---|---|']
    rows += [f"| {r['case_id']} | {r['expected_sha256']} | {r['status']} |" for r in setup['inventory']]
    (DIRECTORY / 'FROZEN.md').write_text('\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
    pilot.write_json(DIRECTORY / 'FROZEN.json', {'implementation': file_hashes(),
        'documents': {name: pilot.sha((DIRECTORY / name).read_bytes())
                      for name in ('PLAN.json', 'APPROVAL.json', 'FROZEN.md')}})
    print('FROZEN: 19 legacy cases, 114 observations; 399 requests maximum; 0 API calls')


def approved():
    frozen = pilot.read_json(DIRECTORY / 'FROZEN.json')
    if frozen['implementation'] != file_hashes() or any(
            pilot.sha((DIRECTORY / name).read_bytes()) != expected
            for name, expected in frozen['documents'].items()):
        raise ValueError('frozen implementation, plan or approval changed')
    setup = pilot.read_json(DIRECTORY / 'PLAN.json')
    if setup != plan() or pilot.read_json(DIRECTORY / 'APPROVAL.json')['user_quote'] != QUOTE:
        raise ValueError('approval or legacy inputs changed')
    return setup


def observe_body(guard, record, status, data, key):
    """Redact before provider/native logs; stop future reservations on quota/identity drift."""
    data = data.replace(key.encode(), b'[CREDENTIAL_REDACTED]') if key else data
    record.update(status_code=status, response_body_sha256=pilot.sha(data))
    try:
        body = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        body = {}
    record.update(returned_model_id=body.get('model'), usage=body.get('usage'))
    if status in guard.plan['stop_http_statuses']:
        guard.stopped_reason = 'provider_stop_status_' + str(status)
    if 200 <= status < 300 and body.get('model') not in guard.plan['accepted_response_ids']:
        guard.stopped_reason = 'unapproved_returned_model_identity'
    if ((body.get('usage') or {}).get('completion_tokens_details') or {}).get('reasoning_tokens', 0):
        guard.stopped_reason = 'unexpected_reasoning_usage'
    return data


def summarize(setup, rows):
    """Invalid/missing planned slots stay in denominators. No score-based selection."""
    groups = {}
    expected = pilot.read_json(regression.DIRECTORY / 'LEGACY_TARGETS.json')
    for condition in setup['conditions']:
        selected = [r for r in rows if r['condition'] == condition]
        cases = []
        for cid in setup['case_ids']:
            repeats = [r for r in selected if r['case_id'] == cid]
            def majority(field):
                counts = Counter(r['parsed'][field] for r in repeats if r['status'] == 'ok')
                return next((value for value, n in counts.items() if n >= 2), None)
            verdict, root = majority('verdict'), majority('root_cause')
            vc = verdict in expected[cid]['acceptable_verdicts']
            rc = root == expected[cid]['root_cause']
            cases.append({'case_id': cid, 'majority_verdict': verdict, 'majority_root': root,
                          'verdict_correct': int(vc), 'root_correct': int(rc), 'joint_correct': int(vc and rc),
                          'verdict_inconsistent': len({r['parsed']['verdict'] for r in repeats
                                                     if r['status'] == 'ok'}) > 1,
                          'incomplete_repeats': sum(r['status'] != 'ok' for r in repeats)})
        groups[condition] = {'observations_planned': len(selected),
            'statuses': dict(Counter(r['status'] for r in selected)), 'cases': cases,
            'observation_counts': {label: sum(r['scores'].get(label, 0) for r in selected)
                                   for label in ('verdict_correct', 'root_correct', 'joint_correct', 'valid_output')},
            'case_counts': {label: sum(r[label] for r in cases)
                           for label in ('verdict_correct', 'root_correct', 'joint_correct', 'verdict_inconsistent')},
            'actual_tool_calls': sum(r['tool_calls'] for r in selected),
            'tool_errors': sum(r['tool_errors'] for r in selected)}
    return groups


def collect_rows(setup, logs):
    from inspect_ai.log import read_eval_log
    by_condition = {}
    for info in logs:
        log = read_eval_log(info.location)
        condition = log.eval.task.removeprefix('t1_regression_')
        if condition not in setup['conditions'] or condition in by_condition:
            raise ValueError('unexpected or duplicate task log')
        by_condition[condition] = {str(s.id): s for s in log.samples or []}
    rows = []
    for condition in setup['conditions']:
        samples = by_condition.get(condition, {})
        for cid in setup['case_ids']:
            for rep in range(1, setup['repetitions'] + 1):
                sample = samples.get(f'{cid}:r{rep}')
                completion = sample.output.completion if sample and sample.output else ''
                parsed, scores = None, dict.fromkeys(('verdict_correct', 'root_correct', 'joint_correct', 'valid_output'), 0)
                status = 'missing' if sample is None else 'execution_error' if sample.error else 'parse_error'
                if sample and not sample.error:
                    try:
                        parsed, scores = regression.bridge.evaluate_output('ok', completion, cid,
                            pilot.read_json(regression.DIRECTORY / 'LEGACY_TARGETS.json')[cid])
                        status = 'ok'
                    except ValueError:
                        pass
                replies = [m for m in sample.messages if m.role == 'tool'] if sample else []
                rows.append({'condition': condition, 'case_id': cid, 'repetition': rep, 'status': status,
                    'output': completion, 'parsed': parsed, 'scores': scores,
                    'execution_error': sample.error.message if sample and sample.error else None,
                    'tool_calls': len(replies), 'tool_errors': sum(bool(m.error) for m in replies),
                    'final_submission_scheduled': bool(sample and sample.metadata.get('final_submission_scheduled'))})
    return rows


def execute(*, transport=None, fixture=False):
    setup = approved()  # Before reading credential or creating provider/client.
    if any(version(package) != value for package, value in setup['dependency_versions'].items()):
        raise ValueError('locked dependencies differ')
    if fixture != (transport is not None):
        raise ValueError('fixture must use an injected offline transport')
    if not os.environ.get(setup['key_env']):
        raise ValueError('local credential environment variable is unset')
    from inspect_ai import eval_async
    from inspect_ai.model import get_model, GenerateConfig
    import httpx2
    key = os.environ[setup['key_env']]
    guard = structured_pilot.RequestBudget(setup)
    frozen_hash = pilot.sha((DIRECTORY / 'FROZEN.json').read_bytes())
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_t1_' + frozen_hash[:12]
    output = WORK / run_id
    if not fixture:
        pilot.claim_run(WORK, frozen_hash, run_id)
    output.mkdir(parents=True, exist_ok=False)
    current_condition = None
    def save():
        pilot.write_json(output / 'REQUEST_BUDGET.json', {'run_id': run_id, 'fixture': fixture,
            'calls': guard.calls, 'input_proxy': guard.input_proxy, 'output_reserved': guard.output_reserved,
            'records': guard.records, 'stopped_reason': guard.stopped_reason})

    async def reserve(request):
        try:
            guard.reserve(request.method, str(request.url), request.content)
        except ValueError:
            guard.stopped_reason = guard.stopped_reason or 'request_validation_or_budget_limit'
            save()
            raise
        index = len(guard.records) - 1
        request.extensions['t1_budget_index'] = index
        request.extensions['t1_started'] = time.monotonic()
        guard.records[index]['condition'] = current_condition
        save()

    async def observe(response):
        index = response.request.extensions['t1_budget_index']
        record = guard.records[index]
        data = observe_body(guard, record, response.status_code, await response.aread(), key)
        response._content = data
        record['elapsed_seconds'] = round(time.monotonic() - response.request.extensions['t1_started'], 3)
        (output / 'responses').mkdir(exist_ok=True)
        (output / 'responses' / f'{index+1:04d}.txt').write_bytes(data)
        save()
        if guard.stopped_reason and 200 <= response.status_code < 300:
            raise ValueError(guard.stopped_reason)

    async def evaluate():
        nonlocal current_condition
        logs = []
        async with httpx2.AsyncClient(event_hooks={'request': [reserve], 'response': [observe]},
                timeout=60, follow_redirects=False, trust_env=False, transport=transport) as client:
            config = GenerateConfig(temperature=0, max_tokens=2048, max_retries=0, timeout=60,
                attempt_timeout=60, max_connections=1, extra_body=setup['extra_body'])
            model = get_model('openai-api/siliconflow/' + setup['model_id'], base_url=setup['base_url'],
                api_key_var=setup['key_env'], http_client=client, config=config, max_retries=0,
                stream=False, strict_tools=False, emulate_tools=False, memoize=False)
            for condition in setup['conditions']:
                current_condition = condition
                if guard.stopped_reason:
                    break
                print(f'START: {condition}; 57 planned observations', flush=True)
                logs += await eval_async(regression.make_task(setup, condition), model=model,
                    log_dir=str(output / 'logs'), log_format='json', log_model_api=False,
                    max_samples=1, max_tasks=1, fail_on_error=False, retry_on_error=0, max_retries=0,
                    message_limit=16, log_level='warning')
                print(f'RECORDED: {condition}; cumulative requests {guard.calls}', flush=True)
        return logs
    logs, fatal = [], None
    try:
        logs = asyncio.run(evaluate())
    except Exception as exc:
        fatal = type(exc).__name__  # Never persist an exception that may include headers.
    finally:
        save()
    # Recover already-written native logs even if the next task raised.
    if fatal:
        from types import SimpleNamespace
        logs = [SimpleNamespace(location=str(p)) for p in sorted((output / 'logs').glob('*.json'))]
    rows = collect_rows(setup, logs)
    result = {'run_id': run_id, 'frozen_sha256': frozen_hash, 'fixture': fixture,
              'planned_observations': 114, 'fatal_error_class': fatal, 'rows': rows,
              'summary': summarize(setup, rows), 'budget': {'calls': guard.calls,
                  'input_proxy': guard.input_proxy, 'output_reserved': guard.output_reserved,
                  'stopped_reason': guard.stopped_reason},
              'scope': setup['analysis'], 'not_supported': 'regression_002 binary gzip; 19/20 candidate coverage'}
    pilot.write_json(output / 'RESULTS.json', json.loads(json.dumps(result, ensure_ascii=False).replace(key, '[CREDENTIAL_REDACTED]')))
    print(f"RECORDED: 114 planned slots; {Counter(r['status'] for r in rows)}; {guard.calls} HTTP reservations", flush=True)
    print('OUTPUT: ' + str(output), flush=True)
    return output


def fixture():
    """OpenAI wire fixture; native provider/solver/tools/scorer, no external calls."""
    import httpx2
    setup = approved()
    seen = []
    def respond(request):
        body = json.loads(request.content)
        seen.append(body)
        public = json.loads(body['messages'][1]['content'])
        if body.get('tools') and not any(m['role'] == 'tool' for m in body['messages']):
            path = next(f['path'] for f in public['files'] if f['path'].startswith('artifacts/'))
            message = {'role': 'assistant', 'content': None, 'tool_calls': [{'id': f'fixture-{len(seen)}',
                'type': 'function', 'function': {'name': 'read_file', 'arguments': json.dumps({'path': path})}}]}
            reason = 'tool_calls'
        else:
            content = 'Fixture collection done.' if body.get('tools') else json.dumps({
                'verdict': 'pass', 'root_cause': 'none', 'evidence': ['task.md:1'], 'action': 'Offline fixture.',
                'proposes_threshold_relaxation': False, 'proposes_skipping_check': False})
            message, reason = {'role': 'assistant', 'content': content}, 'stop'
        return httpx2.Response(200, json={'id': f'fixture-{len(seen)}', 'object': 'chat.completion',
            'created': 0, 'model': setup['model_id'], 'choices': [{'index': 0, 'message': message, 'finish_reason': reason}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20}}, request=request)
    previous_work, previous_key = globals()['WORK'], os.environ.get('SILICONFLOW_API_KEY')
    globals()['WORK'] = regression.ROOT / 'work/t1_live_fixture'
    os.environ['SILICONFLOW_API_KEY'] = 'offline-fixture-placeholder'
    try:
        output = execute(transport=httpx2.MockTransport(respond), fixture=True)
        result = pilot.read_json(output / 'RESULTS.json')
        assert len(seen) == 228 and all(r['status'] == 'ok' for r in result['rows'])
        assert sum(r['tool_calls'] for r in result['rows']) == 57
        assert all('acceptable_verdicts' not in json.dumps(b['messages']) and 'key_evidence' not in json.dumps(b['messages']) for b in seen)
        pilot.write_json(DIRECTORY / 'FIXTURE_RECEIPT.json', {'status': 'pass', 'external_calls': 0,
            'native_provider_fixture_requests': len(seen), 'planned_slots': 114, 'tool_calls': 57,
            'schema_filename_valid': 114, 'model_quality_measured': False,
            'frozen_sha256': result['frozen_sha256']})
    finally:
        globals()['WORK'] = previous_work
        if previous_key is None:
            os.environ.pop('SILICONFLOW_API_KEY', None)
        else:
            os.environ['SILICONFLOW_API_KEY'] = previous_key


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'fixture', 'api'))
    args = parser.parse_args()
    {'prepare': prepare, 'fixture': fixture, 'api': execute}[args.action]()
