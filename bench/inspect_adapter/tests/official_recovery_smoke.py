"""Mock the seven preselected recovery slots, never the real account."""
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from bench.inspect_adapter import pilot
from bench.inspect_adapter.official import recover


def execute():
    import httpx2
    requests = []
    original_client = httpx2.AsyncClient

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        messages = body['messages']
        if any('GRADE:' in str(m.get('content','')) for m in messages):
            message, reason = {'role': 'assistant', 'content': 'GRADE: I'}, 'stop'
        elif body.get('tools') and not any(m['role'] == 'tool' for m in messages):
            message, reason = {'role': 'assistant', 'content': None, 'tool_calls': [
                {'id': 'recovery-add', 'type': 'function', 'function': {'name': 'add', 'arguments': '{"x":1,"y":1}'}}]}, 'tool_calls'
        else:
            message, reason = {'role': 'assistant', 'content': '2' if body.get('tools') else 'RECOVERY FIXTURE'}, 'stop'
        return httpx2.Response(200, json={'id': 'offline-official-recovery', 'object': 'chat.completion',
            'created': 0, 'model': recover.live.plan()['model_id'],
            'choices': [{'index': 0, 'message': message, 'finish_reason': reason}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}})

    class OfflineClient(original_client):
        def __init__(self, **kwargs):
            kwargs['transport'] = httpx2.MockTransport(respond)
            super().__init__(**kwargs)

    work = pilot.ROOT / 'work/official_recovery_fixture'
    with tempfile.TemporaryDirectory(dir=pilot.ROOT / 'work') as directory:
        attempt = work / Path(directory).name
        with patch.object(recover, 'DIRECTORY', Path(directory)), patch.object(recover, 'WORK', attempt), \
             patch.object(httpx2, 'AsyncClient', OfflineClient), \
             patch.dict(os.environ, {'SILICONFLOW_API_KEY': 'unit-only-placeholder'}):
            recover.prepare()
            recover.execute()
    results = pilot.read_json(next(attempt.glob('*/RESULTS.json')))
    ledger = pilot.read_json(next(attempt.glob('*/REQUEST_BUDGET.json')))
    assert len(requests) == 14 and ledger['calls'] == 26 and ledger['previous_calls'] == 12
    assert len(results['retry_rows']) == 7 and len(results['effective_rows']) == 12
    assert all(r['status'] == 'scored' for r in results['retry_rows'])
    original = {(r['task'], r['index']): r for r in results['original_attempt_rows']}
    for row in results['effective_rows']:
        before = original[(row['task'], row['index'])]
        if before['status'] == 'scored':
            assert row == before
    assert [r['index'] for r in results['retry_rows'] if r['task'] == 'theory_of_mind'] == list(range(5, 11))
    pilot.write_json(work / 'RECEIPT.json', {'status': 'pass', 'fake_http_requests': 14,
        'cumulative_reservations': 26, 'original_real_calls_inherited': 12, 'provider_calls_in_this_fixture': 0,
        'network_requests': 0, 'model_quality_measured': False, 'completed_originals_not_recalled': True})
    print('PASS: seven fixed retry IDs; 14 fake HTTP; inherited total26/32; completed originals unchanged; 0 network calls')


if __name__ == '__main__':
    execute()
