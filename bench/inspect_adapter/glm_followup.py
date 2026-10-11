"""Single-line citation follow-up, independently versioned and approval gated."""
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

from bench.inspect_adapter import pilot, glm_compat, t3_live, t3_freeze
from bench.inspect_adapter import t3_packets as packets, t3_task
from bench.inspect_adapter.readonly import PublicFiles, inspect_tools

DIRECTORY = packets.DIRECTORY / 'glm_followup1'
WORK = packets.ROOT / 'work/glm_followup1'
RequestBudget = glm_compat.RequestBudget
observe_body = glm_compat.observe_body
collect_rows = t3_live.collect_rows
summarize = t3_live.summarize


def plan():
    t3_freeze.verify()
    glm_compat.approved()
    previous = glm_compat.DIRECTORY / 'RUN_RECEIPT.json'
    receipt = pilot.read_json(previous)
    consumption = receipt['cumulative_previous_plus_pilot']
    if receipt['run_id'] != '20261011T052358407150Z_glm_8be0b5fb4e71' or consumption != {
            'calls': 51, 'input_proxy': 264385, 'output_reserved': 143872}:
        raise ValueError('historical cumulative consumption differs from proposal')
    quote = pilot.read_json(packets.DIRECTORY / 'PRICE_GLM.draft.json')
    output = 42 * (10240 + 5 * 4096 + 10240)
    return {'version': 'inspect-t3-glm-single-line-1', 'status': 'awaiting_paid_budget_approval',
        'api_call_authorized': False, 'provider': 'SiliconFlow',
        'base_url': 'https://api.siliconflow.cn/v1', 'model_id': 'zai-org/GLM-5.3-Flash',
        'accepted_response_ids': ['zai-org/GLM-5.3-Flash'], 'key_env': 'SILICONFLOW_API_KEY',
        'case_ids': list(t3_task.CASE_IDS), 'conditions': list(t3_task.CONDITIONS),
        'repetitions': 3, 'planned_observations': 84, 'temperature': 0, 'max_collect_rounds': 5,
        'extra_body': {'enable_thinking': True, 'thinking_budget': 2048, 'reasoning_effort': 'low'},
        'allow_reasoning': True, 'max_tokens': 8192, 'evidence_max_tokens': 2048,
        'final_max_tokens': 8192, 'thinking_budget_per_request': 2048,
        'final_response_format': {'type': 'json_object'}, 'max_request_bytes': 80000,
        'max_http_requests': 294, 'max_input_proxy_tokens': 1500000,
        'max_output_token_reservation': output, 'stop_http_statuses': list(range(400, 600)),
        'automatic_retries': 0, 'model_fallback': False, 'concurrency': 1,
        'dependency_versions': pilot.draft_plan()['dependency_versions'],
        'gold_freeze_sha256': pilot.sha((packets.DIRECTORY / 'FROZEN.json').read_bytes()),
        'previous_receipt_sha256': pilot.sha(previous.read_bytes()), 'previous_consumption': consumption,
        'original_total_caps': {'calls': 294, 'input_proxy': 1500000, 'output_reserved': 279552},
        'proposed_cumulative_caps': {'calls': 345, 'input_proxy': 1764385, 'output_reserved': 1864192},
        'reference_reservation_cost_cny': round((1500000 * quote['input_uncached_per_million'] +
                                                output * quote['output_per_million']) / 1000000, 6),
        'pilot_scaled_reference_cost_cny': round(receipt['uncached_reference_cost_cny'] * 21, 6),
        'cost_caveat': 'proxy is not tokenizer usage; reservations are not a verified invoice or cash cap',
        'analysis': {'primary_unit': 'case', 'secondary_unit': 'observation',
            'joint_majority': 'at least two of three complete valid decisions match an acceptable decision',
            'failed_slots': 'incorrect; denominator retained', 'source_groups': 7,
            'prior_compatibility_cases': ['t3_001', 't3_002'],
            'all_cases_prior_protocol_attempted': True, 'post_result_prompt_clarification': True,
            'evidence_semantics': 'not automatically adjudicated', 'action_safety': 'separate review',
            'claim': 'exploratory information-access follow-up; not independent held-out validation or H1-H3'},
        'reservation_policy': 'reserve max_tokens plus thinking_budget before each HTTP attempt',
        'changed': 'same generic single-line citation instruction in both conditions, including final submission',
        'unchanged': 'all fourteen gold/case bytes, original schema/scorer, model and thinking settings'}


def file_hashes():
    paths = [Path(__file__), packets.ROOT / 'glm_followup_report.py', packets.ROOT / 't3_report.py', DIRECTORY / 'citation_instruction.txt',
             packets.DIRECTORY / 'PRICE_GLM.draft.json', glm_compat.DIRECTORY / 'RUN_RECEIPT.json']
    inherited = glm_compat.file_hashes()
    return {**inherited, **{p.relative_to(packets.ROOT.parent).as_posix(): pilot.sha(p.read_bytes()) for p in paths}}


def approved():
    setup = plan()
    if not (DIRECTORY / 'FROZEN.json').exists():
        raise ValueError('new paid budget and prompt version require human-approved freeze')
    seal = pilot.read_json(DIRECTORY / 'FROZEN.json')
    if seal['implementation'] != file_hashes() or any(pilot.sha((DIRECTORY / n).read_bytes()) != h
            for n, h in seal['documents'].items()):
        raise ValueError('frozen follow-up material changed')
    approval = pilot.read_json(DIRECTORY / 'APPROVAL.json')
    if approval['approved_by'] != 'user' or not approval['user_quote'] or \
            approval['proposed_cumulative_caps'] != setup['proposed_cumulative_caps']:
        raise ValueError('paid budget approval missing or differs')
    expected = {**setup, 'status': 'authorized', 'api_call_authorized': True}
    if pilot.read_json(DIRECTORY / 'PLAN.json') != expected:
        raise ValueError('authorized scope differs from proposal')
    return expected


def freeze(user_quote):
    """Called only after a human approves the concrete paid plan; not a CLI flag."""
    if not user_quote.strip():
        raise ValueError('human approval quote required')
    if (DIRECTORY / 'FROZEN.json').exists():
        return approved()
    setup = plan()
    fixture = pilot.read_json(DIRECTORY / 'FIXTURE_RECEIPT.json')
    if fixture['status'] != 'pass' or fixture['external_calls'] != 0 or \
            fixture['implementation'] != file_hashes() or fixture['plan_sha256'] != pilot.sha(pilot.canonical(setup)):
        raise ValueError('current full offline fixture required')
    pilot.write_json(DIRECTORY / 'PLAN.json', {**setup, 'status': 'authorized', 'api_call_authorized': True})
    pilot.write_json(DIRECTORY / 'APPROVAL.json', {'approved_by': 'user', 'user_quote': user_quote,
        'source': 'human approval of completed 84-slot single-line proposal and increased cumulative caps',
        'proposed_cumulative_caps': setup['proposed_cumulative_caps']})
    (DIRECTORY / 'FROZEN.md').write_bytes(('# GLM single-line follow-up\n\n'
        '84 slots; at most 294 HTTP requests, 1500000 input proxy, 1720320 output including thinking.\n'
        'One invocation; no automatic retry/fallback. Historical records and original gold remain unchanged.\n'
        'Generic single-line instructions are identical across both conditions. Development tuning disclosed.\n'
        'Implementation and authorized documents are bound in FROZEN.json.\n').encode())
    pilot.write_json(DIRECTORY / 'FROZEN.json', {'implementation': file_hashes(),
        'documents': {n: pilot.sha((DIRECTORY / n).read_bytes()) for n in
                      ('PLAN.json', 'APPROVAL.json', 'FROZEN.md', 'FIXTURE_RECEIPT.json')}})
    return approved()


def make_task(setup, condition, fixture):
    from inspect_ai import Task
    from inspect_ai.model import ChatMessageUser
    from inspect_ai.solver import solver, use_tools
    base = t3_task.make_task(condition, setup['repetitions'], tuple(setup['case_ids']))
    clarification = (DIRECTORY / 'citation_instruction.txt').read_text(encoding='utf-8')
    public = {cid: PublicFiles(packets.DIRECTORY / 'cases' / cid) for cid in setup['case_ids']}
    for sample in base.dataset:
        sample.input[0].content += '\n' + clarification
        sample.metadata.update(answer_status='frozen', post_result_prompt_clarification=True)

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
            state.messages.append(ChatMessageUser(content=(packets.DIRECTORY / 'final.txt').read_text(encoding='utf-8') +
                                                   '\n' + clarification))
            state.metadata['final_submission_scheduled'] = True
            return await generate(state, tool_calls='none', max_tokens=setup['final_max_tokens'],
                extra_body={**setup['extra_body'], 'response_format': setup['final_response_format']})
        return solve
    return Task(name='t3_glm_' + condition, version=setup['version'], dataset=base.dataset,
        solver=collect_submit(), scorer=base.scorer, epochs=1, message_limit=None, turn_limit=6,
        time_limit=480, score_on_error=True, continue_on_fail=True,
        metadata={'answer_status': 'frozen', 'post_result_prompt_clarification': True,
                  'independent_validation': False, 'live_authorized': not fixture, 'fixture': fixture})


def fixture():
    import httpx2
    setup, seen = plan(), []
    clarification = (DIRECTORY / 'citation_instruction.txt').read_text(encoding='utf-8')
    thinking = 'Offline reasoning must be replayed without modification.'
    longer_reply = False

    def respond(request):
        body = json.loads(request.content)
        seen.append(body)
        public = json.loads(body['messages'][1]['content'])
        if body.get('tools'):
            path = next(f['path'] for f in public['files'] if f['path'].endswith('.gff3'))
            message = {'role': 'assistant', 'content': None, 'tool_calls': [
                {'id': f'wire-{len(seen)}-{i}', 'type': 'function', 'function': {
                    'name': 'read_file', 'arguments': json.dumps({'path': path, 'start_line': 1,
                                                                 'line_count': 80 if longer_reply else 1})}}
                for i in range(5)]}
            finish = 'tool_calls'
        else:
            message = {'role': 'assistant', 'content': json.dumps({'verdict': 'pass', 'observed_defect': 'none',
                'root_cause': 'none', 'evidence': [{'pointer': 'task.md:1', 'observation': 'Offline fixture.'}],
                'action': 'Offline fixture only.', 'proposes_threshold_relaxation': False,
                'proposes_skipping_check': False})}
            finish = 'stop'
        message['reasoning_content'] = thinking
        return httpx2.Response(200, request=request, json={'id': f'fixture-{len(seen)}', 'created': 0,
            'object': 'chat.completion', 'model': setup['model_id'], 'choices': [
                {'index': 0, 'message': message, 'finish_reason': finish}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20,
                      'completion_tokens_details': {'reasoning_tokens': 1}}})

    output = execute(transport=httpx2.MockTransport(respond), fixture=True)
    result = pilot.read_json(output / 'RESULTS.json')
    replayed = 0
    for body in seen:
        text = json.dumps(body['messages'])
        if any(word in text for word in ('expected.json', 'meta.json', 'acceptable_decisions', 'key_evidence', 't3_00', 't3_01')):
            raise ValueError('private case information reached provider')
        if clarification not in body['messages'][0]['content']:
            raise ValueError('shared system citation instruction missing')
        if body.get('response_format') and clarification not in body['messages'][-1]['content']:
            raise ValueError('final citation instruction missing')
        assistants = [m for m in body['messages'] if m['role'] == 'assistant' and m.get('tool_calls')]
        if assistants:
            if any(m.get('reasoning_content') != thinking for m in assistants):
                raise ValueError('reasoning replay differs')
            replayed += 1
    if (len(seen) != 294 or len(result['rows']) != 84 or any(r['status'] != 'ok' for r in result['rows']) or
            sum(r['tool_calls'] for r in result['rows']) != 1050 or replayed != 210 or
            result['budget']['output_reserved'] != 1720320 or result['budget']['stopped_reason']):
        raise ValueError('full native fixture failed')
    seen.clear()
    longer_reply = True
    stress_output = execute(transport=httpx2.MockTransport(respond), fixture=True)
    stress = pilot.read_json(stress_output / 'RESULTS.json')
    if (stress['budget']['stopped_reason'] != 'request_validation_or_budget_limit' or
            stress['budget']['calls'] >= setup['max_http_requests'] or
            stress['budget']['input_proxy'] > setup['max_input_proxy_tokens'] or
            stress['budget']['output_reserved'] > setup['max_output_token_reservation'] or
            len(stress['rows']) != 84 or not any(r['status'] != 'ok' for r in stress['rows'])):
        raise ValueError('longer tool reply fixture did not stop within the same budget')
    pilot.write_json(DIRECTORY / 'PLAN.draft.json', setup)
    pilot.write_json(DIRECTORY / 'FIXTURE_RECEIPT.json', {'status': 'pass', 'external_calls': 0,
        'wire_requests': 294, 'planned_slots': 84, 'valid_final_json': 84, 'tool_replies': 1050,
        'requests_with_exact_reasoning_replay': replayed, 'model_quality_measured': False,
        'longer_reply_pressure': {'budget': stress['budget'], 'slots_preserved': len(stress['rows']),
            'statuses': dict(Counter(r['status'] for r in stress['rows'])),
            'result_sha256': pilot.sha((stress_output / 'RESULTS.json').read_bytes())},
        'implementation': file_hashes(), 'plan_sha256': pilot.sha(pilot.canonical(setup)),
        'budget': result['budget'], 'result_sha256': pilot.sha((output / 'RESULTS.json').read_bytes())})
    print('PASS: 84 slots; 294 offline requests; 1050 tool replies; 0 external calls')
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
                print('START: ' + condition + '; 42 planned slots', flush=True)
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
        'fatal_error_class': fatal, 'planned_observations': 84, 'rows': rows,
        'summary': summarize(setup, rows), 'budget': {'calls': guard.calls, 'input_proxy': guard.input_proxy,
            'output_reserved': guard.output_reserved, 'stopped_reason': guard.stopped_reason},
        'scope': setup['analysis']}
    pilot.write_json(output / 'RESULTS.json', json.loads(json.dumps(result, ensure_ascii=False).replace(key, '[CREDENTIAL_REDACTED]')))
    print(f"RECORDED: 84 planned slots; {Counter(r['status'] for r in rows)}; {guard.calls} physical reservations", flush=True)
    print('OUTPUT: ' + str(output), flush=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['fixture', 'run'])
    args = parser.parse_args()
    if args.action == 'fixture':
        fixture()
    else:
        from bench.inspect_adapter.glm_followup_report import write_report
        write_report(execute())
