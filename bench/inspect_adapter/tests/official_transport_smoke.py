"""Real official tasks over a native fake HTTP transport; not model evidence."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from bench.inspect_adapter.official import live
from bench.inspect_adapter import pilot


def execute():
    import httpx2
    client = httpx2.AsyncClient
    requests = []

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        messages = body['messages']
        if any('GRADE:' in str(m.get('content', '')) for m in messages):
            message = {'role': 'assistant', 'content': 'GRADE: I'}
            reason = 'stop'
        elif body.get('tools') and not any(m['role'] == 'tool' for m in messages):
            parallel = '2+2' in str(messages)
            calls = [{'id': 'add-1', 'type': 'function', 'function': {'name': 'add', 'arguments': '{"x":1,"y":1}'}}]
            if parallel:
                calls.append({'id': 'add-2', 'type': 'function', 'function': {'name': 'add', 'arguments': '{"x":2,"y":2}'}})
            message = {'role': 'assistant', 'content': None, 'tool_calls': calls}
            reason = 'tool_calls'
        else:
            tools = [m for m in messages if m['role'] == 'tool']
            message = {'role': 'assistant', 'content': ' '.join(m['content'] for m in tools) if tools else 'OFFLINE FIXTURE, not a real answer'}
            reason = 'stop'
        return httpx2.Response(200, json={'id': 'offline-official', 'object': 'chat.completion',
            'created': 0, 'model': live.plan()['model_id'],
            'choices': [{'index': 0, 'message': message, 'finish_reason': reason}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}})

    output = pilot.ROOT / 'work/official_transport'
    class OfflineClient(client):
        def __init__(self, **kwargs):
            kwargs['transport'] = httpx2.MockTransport(respond)
            super().__init__(**kwargs)
    with tempfile.TemporaryDirectory(dir=pilot.ROOT / 'work') as directory:
        attempt = output / Path(directory).name
        with patch.object(live, 'DIRECTORY', Path(directory)), patch.object(live, 'WORK', attempt), \
             patch.object(httpx2, 'AsyncClient', OfflineClient), \
             patch.dict(os.environ, {'SILICONFLOW_API_KEY': 'unit-only-placeholder'}):
            live.prepare()
            live.execute()
    results_path = next(attempt.glob('*/RESULTS.json'))
    results = pilot.read_json(results_path)
    assert len(results['rows']) == 12 and all(r['status'] == 'scored' for r in results['rows'])
    assert len(requests) == 24 and sum(r['tool_calls'] for r in results['rows']) == 3
    assert all(r['score'] == 'I' for r in results['rows'] if r['task'] == 'theory_of_mind')
    assert all(r['score'] == 'C' for r in results['rows'] if r['task'] != 'theory_of_mind')
    receipt = {'status': 'pass', 'official_samples': 12, 'fake_http_requests': len(requests),
               'actual_python_tools': 3, 'provider_calls': 0, 'network_requests': 0,
               'fixture_usage_not_real_tokens': True, 'model_quality_measured': False}
    pilot.write_json(output / 'RECEIPT.json', receipt)
    print('PASS: 12 official fixture samples; 24 fake HTTP; 3 real add calls; 0 network/provider requests')


if __name__ == '__main__':
    execute()
