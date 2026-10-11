"""Authorized four-slot thinking protocol pilot; historical runs stay frozen."""
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

from bench.inspect_adapter import pilot, structured_pilot, t3_live, response_policy
from bench.inspect_adapter import t3_freeze, t3_packets as packets, t3_task
from bench.inspect_adapter.readonly import PublicFiles, inspect_tools

DIRECTORY = packets.DIRECTORY / 'glm_compat1'
WORK = packets.ROOT / 'work/glm_compat1'
QUOTE = '好'


def plan():
    t3_freeze.verify()
    draft = pilot.read_json(DIRECTORY / 'PLAN.draft.json')
    prior = packets.ROOT / 'work/t3_glm_live' / draft['previous_run_id'] / 'REQUEST_BUDGET.json'
    record = pilot.read_json(prior)
    if any(record[k] != v for k, v in draft['previous_consumption'].items()):
        raise ValueError('prior consumption changed')
    if (draft['case_ids'] != ['t3_001', 't3_002'] or draft['conditions'] != ['inline', 'tools'] or
            draft['repetitions'] != 1 or draft['max_http_requests'] != 14 or
            draft['max_input_proxy_tokens'] != 100000 or draft['max_output_token_reservation'] != 81920 or
            draft['collect_max_tokens'] != 2048 or draft['final_max_tokens'] != 8192 or
            draft['thinking_budget_per_request'] != 2048 or draft['temperature'] != 0 or
            draft['extra_body_proposed'] != {'enable_thinking': True, 'thinking_budget': 2048, 'reasoning_effort': 'low'} or
            draft['model_id'] != 'zai-org/GLM-5.3-Flash' or draft['base_url'] != 'https://api.siliconflow.cn/v1' or
            draft['max_collect_rounds'] != 5 or draft['automatic_retries'] != 0 or
            draft['gold_freeze_sha256'] != pilot.sha((packets.DIRECTORY / 'FROZEN.json').read_bytes())):
        raise ValueError('pilot scope differs from human-approved proposal')
    for used, cap, original in [('calls', 'max_http_requests', 'requests'),
                              ('input_proxy', 'max_input_proxy_tokens', 'input_proxy'),
                              ('output_reserved', 'max_output_token_reservation', 'output_reservation')]:
        if record[used] + draft[cap] > draft['original_total_caps'][original]:
            raise ValueError('cumulative original budget exceeded')
    return {**draft, 'version': 'inspect-t3-glm-thinking-compat-1',
        'accepted_response_ids': [draft['model_id']], 'allow_reasoning': True,
        'extra_body': draft['extra_body_proposed'], 'max_tokens': 8192,
        'evidence_max_tokens': 2048, 'final_response_format': {'type': 'json_object'},
        'max_request_bytes': 80000, 'stop_http_statuses': list(range(400, 600)),
        'dependency_versions': pilot.draft_plan()['dependency_versions'],
        'previous_budget_sha256': pilot.sha(prior.read_bytes())}


def file_hashes():
    names = ['glm_compat.py', 'response_policy.py', 't3_live.py', 't3_task.py', 't3_packets.py',
             't3_freeze.py', 'readonly.py', 'pilot.py', 'structured_pilot.py', 't1_live.py',
             'requirements-pilot.lock.txt']
    paths = [packets.ROOT / name for name in names]
    paths += [DIRECTORY / 'PLAN.draft.json', packets.DIRECTORY / 'FROZEN.json',
              packets.ROOT.parent / 'harness_common.py', packets.ROOT.parent / 'v2/runtime.py']
    return {p.relative_to(packets.ROOT.parent).as_posix(): pilot.sha(p.read_bytes()) for p in paths}


def freeze():
    if (DIRECTORY / 'FROZEN.json').exists():
        return approved()
    setup = plan()
    receipt = pilot.read_json(DIRECTORY / 'FIXTURE_RECEIPT.json')
    if (receipt['status'] != 'pass' or receipt['external_calls'] != 0 or
            receipt['implementation'] != file_hashes() or receipt['plan_sha256'] != pilot.sha(pilot.canonical(setup))):
        raise ValueError('offline receipt does not bind current implementation')
    pilot.write_json(DIRECTORY / 'PLAN.json', {**setup, 'api_call_authorized': True})
    pilot.write_json(DIRECTORY / 'APPROVAL.json', {'user_quote': QUOTE, 'date': '2026-10-11',
        'source': 'human reply to concrete four-observation thinking compatibility proposal',
        'scope': '4 slots; 14 HTTP requests; 100000 input proxy; 81920 output including thinking; no retries; original cumulative caps unchanged'})
    (DIRECTORY / 'FROZEN.md').write_bytes(('# GLM thinking compatibility 1\n\n'
        '2026-10-11 用户批准4条协议兼容性观测。金标准、公用提示与历史84条失败记录不变。\n'
        '最多14请求、100000输入代理、81920输出预留（含思考）；原累计上限不增加。\n'
        '思考开启，low effort；采集2048、最终8192、思考预留2048；无重试、无型号或参数回退。\n'
        '实现、计划、授权和离线检查哈希见FROZEN.json。只允许一次启动。\n').encode('utf-8'))
    pilot.write_json(DIRECTORY / 'FROZEN.json', {'implementation': file_hashes(),
        'documents': {n: pilot.sha((DIRECTORY / n).read_bytes()) for n in
                      ('PLAN.json', 'APPROVAL.json', 'FROZEN.md', 'FIXTURE_RECEIPT.json')}})
    return approved()


def approved():
    setup = plan()
    if not (DIRECTORY / 'FROZEN.json').exists():
        raise ValueError('approved freeze required before credentials or HTTP client')
    seal = pilot.read_json(DIRECTORY / 'FROZEN.json')
    if seal['implementation'] != file_hashes() or any(pilot.sha((DIRECTORY / n).read_bytes()) != h
            for n, h in seal['documents'].items()):
        raise ValueError('frozen implementation changed')
    if pilot.read_json(DIRECTORY / 'PLAN.json') != {**setup, 'api_call_authorized': True} or \
            pilot.read_json(DIRECTORY / 'APPROVAL.json')['user_quote'] != QUOTE:
        raise ValueError('authorization changed')
    return {**setup, 'api_call_authorized': True}


class RequestBudget(structured_pilot.RequestBudget):
    def reserve(self, method, url, data):
        body = pilot.strict_object(data.decode('utf-8'))
        if any(type(body.get(k)) is not type(v) or body.get(k) != v for k, v in self.plan['extra_body'].items()):
            raise ValueError('thinking parameters differ from approval')
        thinking = self.plan['thinking_budget_per_request']
        original = self.plan
        try:
            self.plan = {**original, 'extra_body': {'enable_thinking': True},
                         'max_output_token_reservation': original['max_output_token_reservation'] - thinking}
            super().reserve(method, url, data)
        finally:
            self.plan = original
        self.output_reserved += thinking
        self.records[-1].update(requested_max_tokens=body['max_tokens'], thinking_budget=thinking,
                               output_reserved=body['max_tokens'] + thinking)


def make_task(setup, condition, fixture):
    from inspect_ai import Task
    from inspect_ai.model import ChatMessageUser
    from inspect_ai.solver import solver, use_tools
    base = t3_task.make_task(condition, 1, tuple(setup['case_ids']))
    public = {cid: PublicFiles(packets.DIRECTORY / 'cases' / cid) for cid in setup['case_ids']}
    for sample in base.dataset:
        sample.metadata['answer_status'] = 'frozen'

    @solver
    def collect_submit():
        async def solve(state, generate):
            if condition == 'tools':
                state = await use_tools(inspect_tools(public[state.metadata['case_id']]))(state, generate)
                for _ in range(setup['max_collect_rounds']):
                    state = await generate(state, tool_calls='single', max_tokens=setup['evidence_max_tokens'],
                                           extra_body=setup['extra_body'])
                    if state.completed:
                        return state
                    if not state.output.message.tool_calls:
                        break
            state.tools = []
            state.tool_choice = 'none'
            state.messages.append(ChatMessageUser(content=(packets.DIRECTORY / 'final.txt').read_text(encoding='utf-8')))
            state.metadata['final_submission_scheduled'] = True
            return await generate(state, tool_calls='none', max_tokens=setup['final_max_tokens'],
                extra_body={**setup['extra_body'], 'response_format': setup['final_response_format']})
        return solve
    return Task(name='t3_glm_' + condition, version=setup['version'], dataset=base.dataset,
        solver=collect_submit(), scorer=base.scorer, epochs=1, message_limit=None, turn_limit=6,
        time_limit=480, score_on_error=True, continue_on_fail=True,
        metadata={'answer_status': 'frozen', 'protocol_compatibility_only': True,
                  'live_authorized': not fixture, 'fixture': fixture})


def summarize(setup, rows):
    return {condition: {'planned_observations': 2, 'statuses': dict(Counter(r['status'] for r in rows if r['condition'] == condition)),
                       'tool_calls': sum(r['tool_calls'] for r in rows if r['condition'] == condition),
                       'tool_errors': sum(r['tool_errors'] for r in rows if r['condition'] == condition)}
            for condition in setup['conditions']}


collect_rows = t3_live.collect_rows


def observe_body(guard, record, status, data, key):
    data = response_policy.observe_body(guard, record, status, data, key)
    usage = record.get('usage') or {}
    if 200 <= status < 300 and (usage.get('completion_tokens') or 0) > record['output_reserved']:
        guard.stopped_reason = 'reported_output_exceeds_reservation'
    return data


def fixture():
    import httpx2
    setup, seen = plan(), []
    thinking = 'Offline original reasoning; preserve exactly.'

    def respond(request):
        body = json.loads(request.content)
        seen.append(body)
        public = json.loads(body['messages'][1]['content'])
        if body.get('tools'):
            path = next(f['path'] for f in public['files'] if f['path'].endswith('.gff3'))
            message = {'role': 'assistant', 'content': None, 'tool_calls': [
                {'id': f'wire-{len(seen)}-{i}', 'type': 'function', 'function': {
                    'name': 'read_file', 'arguments': json.dumps({'path': path, 'start_line': 1, 'line_count': 1})}}
                for i in range(5)]}
            reason = 'tool_calls'
        else:
            message = {'role': 'assistant', 'content': json.dumps({'verdict': 'pass', 'observed_defect': 'none',
                'root_cause': 'none', 'evidence': [{'pointer': 'task.md:1', 'observation': 'Offline fixture.'}],
                'action': 'Offline protocol fixture only.', 'proposes_threshold_relaxation': False,
                'proposes_skipping_check': False})}
            reason = 'stop'
        message['reasoning_content'] = thinking
        return httpx2.Response(200, request=request, json={'id': f'wire-{len(seen)}', 'created': 0,
            'object': 'chat.completion', 'model': setup['model_id'], 'choices': [
                {'index': 0, 'message': message, 'finish_reason': reason}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20,
                      'completion_tokens_details': {'reasoning_tokens': 1}}})

    output = execute(transport=httpx2.MockTransport(respond), fixture=True)
    result = pilot.read_json(output / 'RESULTS.json')
    replayed = 0
    for body in seen:
        text = json.dumps(body['messages'])
        if any(word in text for word in ('expected.json', 'meta.json', 'acceptable_decisions', 'key_evidence', 't3_00')):
            raise ValueError('private data reached wire fixture')
        assistants = [m for m in body['messages'] if m['role'] == 'assistant' and m.get('tool_calls')]
        if assistants:
            if any(m.get('reasoning_content') != thinking for m in assistants):
                raise ValueError('original interleaved reasoning was not preserved')
            replayed += 1
    if (len(seen) != 14 or len(result['rows']) != 4 or any(r['status'] != 'ok' for r in result['rows']) or
            sum(r['tool_calls'] for r in result['rows']) != 50 or replayed != 10 or
            result['budget']['output_reserved'] != 81920 or result['budget']['stopped_reason']):
        raise ValueError('native worst-case compatibility fixture failed')
    pilot.write_json(DIRECTORY / 'FIXTURE_RECEIPT.json', {'status': 'pass', 'external_calls': 0,
        'wire_requests': 14, 'planned_slots': 4, 'valid_final_json': 4, 'tool_replies': 50,
        'requests_with_exact_reasoning_replay': replayed, 'model_quality_measured': False,
        'implementation': file_hashes(), 'plan_sha256': pilot.sha(pilot.canonical(setup)),
        'budget': result['budget'], 'result_sha256': pilot.sha((output / 'RESULTS.json').read_bytes())})
    print('PASS: 4 slots; 14 offline requests; 50 tool replies; exact reasoning replay; 0 external calls')
    return output


def execute(*, transport=None, fixture=False):
    if fixture != (transport is not None):
        raise ValueError('offline fixture requires injected transport; live mode cannot inject transport')
    setup = plan() if fixture else approved()  # Before credential access or provider initialization.
    if any(version(name) != expected for name, expected in setup['dependency_versions'].items()):
        raise ValueError('locked dependency versions differ')
    from inspect_ai import eval_async
    from inspect_ai.model import GenerateConfig, get_model
    import httpx2
    key = 'offline-fixture-placeholder' if fixture else os.environ.get(setup['key_env'])
    if not key:
        raise ValueError('local credential environment variable unset')
    guard = RequestBudget(setup)
    seal_hash = pilot.sha(pilot.canonical(setup)) if fixture else pilot.sha((DIRECTORY / 'FROZEN.json').read_bytes())
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '_glm_' + seal_hash[:12]
    output = WORK / run_id
    if not fixture:
        pilot.claim_run(WORK, seal_hash, run_id)
    output.mkdir(parents=True, exist_ok=False)
    current_condition = None

    def save():
        pilot.write_json(output / 'REQUEST_BUDGET.json', {'fixture': fixture, 'run_id': run_id,
            'calls': guard.calls, 'input_proxy': guard.input_proxy, 'output_reserved': guard.output_reserved,
            'records': guard.records, 'stopped_reason': guard.stopped_reason})

    async def reserve(request):
        try:
            guard.reserve(request.method, str(request.url), request.content)
        except ValueError:
            guard.stopped_reason = guard.stopped_reason or 'request_validation_or_budget_limit'
            save()
            raise
        request.extensions['budget_index'] = len(guard.records) - 1
        request.extensions['started'] = time.monotonic()
        guard.records[-1]['condition'] = current_condition
        body = json.loads(request.content)
        reasoning = [m['reasoning_content'] for m in body['messages']
                     if m.get('role') == 'assistant' and m.get('reasoning_content')]
        guard.records[-1]['replayed_reasoning_blocks'] = len(reasoning)
        guard.records[-1]['replayed_reasoning_sha256'] = [pilot.sha(r.encode('utf-8')) for r in reasoning]
        save()

    async def observe(response):
        index = response.request.extensions['budget_index']
        record = guard.records[index]
        data = observe_body(guard, record, response.status_code, await response.aread(), key)
        response._content = data  # Redacted before native provider/error handling.
        record['elapsed_seconds'] = round(time.monotonic() - response.request.extensions['started'], 3)
        (output / 'responses').mkdir(exist_ok=True)
        (output / 'responses' / f'{index+1:04d}.txt').write_bytes(data)
        save()
        if guard.stopped_reason and 200 <= response.status_code < 300:
            raise ValueError(guard.stopped_reason)

    class SafeTransport(httpx2.AsyncBaseTransport):
        def __init__(self, inner):
            self.inner = inner

        async def handle_async_request(self, request):
            try:
                return await self.inner.handle_async_request(request)
            except Exception as exc:
                record = guard.records[request.extensions['budget_index']]
                record.update(transport_error_class=type(exc).__name__,
                    elapsed_seconds=round(time.monotonic() - request.extensions['started'], 3))
                guard.stopped_reason = 'transport_failure'
                save()
                raise ValueError('Transport failure: ' + type(exc).__name__) from None

        async def aclose(self):
            await self.inner.aclose()

    async def evaluate():
        nonlocal current_condition
        logs = []
        inner = transport if fixture else httpx2.AsyncHTTPTransport(verify=True, retries=0)
        async with httpx2.AsyncClient(transport=SafeTransport(inner),
                event_hooks={'request': [reserve], 'response': [observe]}, timeout=120,
                verify=True, trust_env=False, follow_redirects=False) as client:
            config = GenerateConfig(temperature=0, max_tokens=8192, max_retries=0,
                timeout=120, attempt_timeout=120, max_connections=1, extra_body=setup['extra_body'])
            model = get_model('openai-api/siliconflow/' + setup['model_id'], base_url=setup['base_url'],
                api_key=key, http_client=client, config=config, max_retries=0, stream=False,
                strict_tools=False, emulate_tools=False, memoize=False)
            for condition in setup['conditions']:
                if guard.stopped_reason:
                    break
                current_condition = condition
                print('START: ' + condition + '; 2 planned slots', flush=True)
                logs += await eval_async(make_task(setup, condition, fixture), model=model,
                    log_dir=str(output / 'logs'), log_format='json', log_model_api=False,
                    max_samples=1, max_tasks=1, fail_on_error=False, retry_on_error=0,
                    max_retries=0, message_limit=None, log_level='warning')
                print(f'RECORDED: {condition}; cumulative requests {guard.calls}', flush=True)
        return logs

    fatal, logs = None, []
    try:
        logs = asyncio.run(evaluate())
    except Exception as exc:
        fatal = type(exc).__name__
        if fixture:
            import traceback
            traceback.print_exc()
    finally:
        save()
    if fatal:
        from types import SimpleNamespace
        logs = [SimpleNamespace(location=str(p)) for p in sorted((output / 'logs').glob('*.json'))]
    rows = collect_rows(setup, logs)
    result = {'run_id': run_id, 'fixture': fixture, 'plan_sha256': pilot.sha(pilot.canonical(setup)),
        'seal_sha256': seal_hash, 'gold_freeze_sha256': setup['gold_freeze_sha256'],
        'fatal_error_class': fatal, 'planned_observations': 4, 'rows': rows,
        'summary': summarize(setup, rows), 'budget': {'calls': guard.calls, 'input_proxy': guard.input_proxy,
            'output_reserved': guard.output_reserved, 'stopped_reason': guard.stopped_reason},
        'scope': setup['analysis']}
    pilot.write_json(output / 'RESULTS.json', json.loads(json.dumps(result, ensure_ascii=False).replace(key, '[CREDENTIAL_REDACTED]')))
    print(f"RECORDED: 4 planned slots; {Counter(r['status'] for r in rows)}; {guard.calls} physical reservations", flush=True)
    print('OUTPUT: ' + str(output), flush=True)
    return output


def report(output):
    setup = approved()
    result = pilot.read_json(output / 'RESULTS.json')
    budget = pilot.read_json(output / 'REQUEST_BUDGET.json')
    if result['fixture'] or result['seal_sha256'] != pilot.sha((DIRECTORY / 'FROZEN.json').read_bytes()):
        raise ValueError('report requires the authorized real run')
    expected = {(c, cid, 1) for c in setup['conditions'] for cid in setup['case_ids']}
    rows = result['rows']
    if len(rows) != 4 or {(r['condition'], r['case_id'], r['repetition']) for r in rows} != expected:
        raise ValueError('all four planned slots must be preserved')
    usage = {key: sum((r.get('usage') or {}).get(key, 0) or 0 for r in budget['records'])
             for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
    cost = (usage['prompt_tokens'] * .8 + usage['completion_tokens'] * 2.8) / 1000000
    combined = {key: setup['previous_consumption'][key] + budget[key]
                for key in ('calls', 'input_proxy', 'output_reserved')}
    counts = dict(Counter(r['status'] for r in rows))
    receipt = {'run_id': result['run_id'], 'protocol_compatibility_only': True,
               'observations': 4, 'statuses': counts, 'budget': result['budget'],
               'cumulative_previous_plus_pilot': combined, 'actual_provider_usage': usage,
               'uncached_reference_cost_cny': round(cost, 6), 'invoice_verified': False,
               'reasoning_response_requests': sum(bool(r.get('reasoning_content_present')) for r in budget['records']),
               'requests_with_replayed_reasoning': sum(bool(r.get('replayed_reasoning_blocks')) for r in budget['records']),
               'model_quality_comparison_valid': False,
               'native_log_scope': 'private work directory; targets never sent to model',
               'rows': rows, 'summary': result['summary']}
    # Scan all private run artifacts for credentials; report only match counts.
    import re
    paths = sorted(p for p in output.rglob('*') if p.is_file())
    matches = sum(bool(re.search(rb'sk-[A-Za-z0-9_.-]{12,}', p.read_bytes())) for p in paths)
    if matches:
        raise ValueError('credential-like text in run artifacts; do not publish')
    receipt['credential_scan'] = {'files': len(paths), 'matches': matches}
    receipt['private_artifacts'] = {p.relative_to(output).as_posix(): pilot.sha(p.read_bytes()) for p in paths}
    pilot.write_json(DIRECTORY / 'RUN_RECEIPT.json', receipt)
    lines = ['# GLM 思考协议兼容性试跑', '',
        '这4条是已尝试来源上的开发协议检查，不能用于模型排名、工具增益或独立测试结论。原84条失败记录保留。', '',
        f"运行 `{result['run_id']}`；状态 {counts}；实际请求 {budget['calls']}/14；停止原因 `{budget['stopped_reason']}`。", '',
        f"平台报告输入 {usage['prompt_tokens']}、输出 {usage['completion_tokens']}、总计 {usage['total_tokens']} token。",
        f'按未缓存单价参考费用 ¥{cost:.6f}，实际以账单为准。', '',
        f'与前次累计：{combined}；原上限294请求、1500000输入代理、279552输出预留保持不变。', '',
        f"含思考的响应 {receipt['reasoning_response_requests']} 次；请求中回传思考 {receipt['requests_with_replayed_reasoning']} 次。",
        '只有平台明确报告的用量可用于检查；不能仅凭请求参数证明供应商遵守思考预算。', '',
        '| 题 | 条件 | 状态 | 工具调用 | 判定 / 根因 |', '|---|---|---|---:|---|']
    for row in rows:
        parsed = row['parsed'] or {}
        lines.append(f"| {row['case_id']} | {row['condition']} | {row['status']} | {row['tool_calls']} | {parsed.get('verdict', '—')} / {parsed.get('root_cause', '—')} |")
    lines += ['', '原始响应、最终答案、异常及原生Inspect日志保存在本地work目录；RUN_RECEIPT.json包含逐槽位结果、用量和哈希。', '',
              '## 边界', '', '单人确认标准答案，AI审核不等于真人盲审；两道开发题、每条件一次。协议参数已改变，不能与旧失败运行合并计算准确率。证据语义与行动安全未自动判定。']
    (DIRECTORY / 'REPORT.md').write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
    print('REPORT: ' + str(DIRECTORY / 'REPORT.md'))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['fixture', 'freeze', 'run', 'report'])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'fixture':
        fixture()
    elif args.action == 'freeze':
        freeze()
    elif args.action == 'run':
        report(execute())
    elif args.output:
        report(args.output)
    else:
        parser.error('report requires --output')
