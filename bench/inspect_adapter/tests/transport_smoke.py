"""Offline transport fixture, not a supplier request or model-quality test."""
import json
import httpx2
from inspect_ai import eval as inspect_eval
from inspect_ai.log import read_eval_log
from inspect_ai.model import get_model, GenerateConfig
from bench.inspect_adapter import pilot


def main():
    plan = {**pilot.draft_plan(), 'base_url': 'https://unit.invalid/v1'}
    budget = pilot.RequestBudget(plan)

    def respond(request):
        budget.reserve(request.method, str(request.url), request.content)
        body = json.loads(request.content)
        if any(message['role'] == 'tool' for message in body['messages']):
            message = {'role': 'assistant', 'content': '{"mock_complete":true,"qc_verdict":null}'}
            reason = 'stop'
        else:
            assert len(body['tools']) == 5
            message = {'role': 'assistant', 'content': None, 'tool_calls': [
                {'id': 'fixture-list', 'type': 'function',
                 'function': {'name': 'list_files', 'arguments': '{}'}}]}
            reason = 'tool_calls'
        return httpx2.Response(200, json={
            'id': 'offline-fixture', 'object': 'chat.completion', 'created': 0,
            'model': plan['model_id'],
            'choices': [{'index': 0, 'message': message, 'finish_reason': reason}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}})

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond), follow_redirects=False)
    model = get_model('openai-api/unit/' + plan['model_id'], base_url=plan['base_url'],
                      api_key='unit-only-placeholder', http_client=client,
                      config=GenerateConfig(temperature=0, max_tokens=2048, max_retries=0,
                                            timeout=60, attempt_timeout=60, max_connections=1),
                      max_retries=0, stream=False, strict_tools=False, emulate_tools=False, memoize=False)
    answers, _ = pilot.candidates()
    logs = inspect_eval(pilot.make_task(plan, answers['cases']), model=model, display='none',
                        log_dir=str(pilot.ROOT / 'work/pilot_transport/logs'), log_format='json',
                        max_samples=1, retry_on_error=0, max_retries=0, log_model_api=False)
    log = read_eval_log(logs[0].location)
    assert log.status == 'success' and len(log.samples) == 4
    assert all(sample.error is None and not any(next(iter(sample.scores.values())).value.values()) for sample in log.samples)
    assert budget.calls == 8
    pilot.write_json(pilot.ROOT / 'work/pilot_transport/RECEIPT.json', {
        'status': 'pass', 'network_requests': 0, 'provider_calls': 0,
        'fake_transport_requests': budget.calls, 'actual_tool_calls': 4,
        'synthetic_usage_not_real_tokens': True,
        'input_proxy_reservations': budget.input_proxy,
        'records': budget.records})
    print('PASS: native SDK payload and budget hooks; 8 fake transport requests; 4 real tools; 0 network/provider calls')


if __name__ == '__main__':
    main()
