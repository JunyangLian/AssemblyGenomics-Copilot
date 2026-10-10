"""Native Inspect/OpenAI SDK over MockTransport. No network or real token usage."""
import json

import httpx2
from inspect_ai import eval as inspect_eval
from inspect_ai.log import read_eval_log
from inspect_ai.model import GenerateConfig, get_model

from bench.inspect_adapter import pilot, structured_pilot as revised


def run_fixture(mode):
    plan = {**revised.draft_plan(), 'base_url': 'https://unit.invalid/v1'}
    guard = revised.RequestBudget(plan)
    seen = []

    def respond(request):
        guard.reserve(request.method, str(request.url), request.content)
        body = json.loads(request.content)
        seen.append(body)
        public = json.loads(body['messages'][1]['content'])
        names = [f['path'] for f in public['files']]
        is_final = body.get('response_format') == {'type': 'json_object'}
        if is_final:
            assert not body.get('tools') and 'tool_choice' not in body
            if mode == 'malformed':
                content = 'Explanation\n```json\n{}\n```'
            else:
                # Deliberately generic synthetic output, never a source-derived model answer.
                content = json.dumps({'verdict': 'pass', 'observed_defect': 'none', 'root_cause': 'none',
                    'evidence': [{'pointer': names[0] + ':bytes', 'observation': 'Offline fixture only; not biological evidence.'}],
                    'action': 'Offline fixture only.', 'proposes_threshold_relaxation': False,
                    'proposes_skipping_check': False})
            message, reason = {'role': 'assistant', 'content': content}, 'stop'
        elif any(m['role'] == 'tool' for m in body['messages']) and mode != 'round_cap':
            message, reason = {'role': 'assistant', 'content': 'Evidence fixture finished.'}, 'stop'
        else:
            if mode == 'round_cap':
                name, args = 'list_files', {}
            elif 'artifacts/sequence.fa' in names:
                name, args = 'interval_counts', {'sequence_path': 'artifacts/sequence.fa',
                                                  'regions_path': 'artifacts/regions.tsv'}
            elif 'artifacts/query.faa' in names:
                name, args = 'annotation_counts', {'query_path': 'artifacts/query.faa',
                                                    'table_path': 'artifacts/annotation.tsv'}
            else:
                name, args = 'file_stats', {'path': 'artifacts/hints.gff'}
            message = {'role': 'assistant', 'content': None, 'tool_calls': [
                {'id': 'offline-' + str(guard.calls), 'type': 'function',
                 'function': {'name': name, 'arguments': json.dumps(args)}}]}
            reason = 'tool_calls'
        return httpx2.Response(200, json={'id': 'offline-fixture', 'object': 'chat.completion',
            'created': 0, 'model': plan['model_id'],
            'choices': [{'index': 0, 'message': message, 'finish_reason': reason}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}})

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond), follow_redirects=False)
    model = get_model('openai-api/unit/' + plan['model_id'], base_url=plan['base_url'],
                      api_key='unit-only-placeholder', http_client=client,
                      config=GenerateConfig(temperature=0, max_tokens=2048, max_retries=0,
                          max_connections=1, extra_body=plan['extra_body']),
                      max_retries=0, stream=False, strict_tools=False, emulate_tools=False, memoize=False)
    # Empty target sets ensure fixtures cannot masquerade as correct QC decisions.
    answers = {cid: {'acceptable_decisions': []} for cid in plan['case_ids']}
    logs = inspect_eval(revised.make_task(plan, answers), model=model, display='none',
                        log_dir=str(pilot.ROOT / 'work/pilot2_transport' / mode / 'logs'),
                        log_format='json', max_samples=1, retry_on_error=0, max_retries=0,
                        log_model_api=False)
    log = read_eval_log(logs[0].location)
    assert log.status == 'success' and len(log.samples) == 4
    tools = [m for s in log.samples for m in s.messages if m.role == 'tool']
    assert not any(s.error for s in log.samples) and not any(m.error for m in tools)
    assert sum(r['phase'] == 'final' for r in guard.records) == 4
    assert guard.calls == (24 if mode == 'round_cap' else 12)
    assert len(tools) == (20 if mode == 'round_cap' else 4)
    assert all(next(iter(s.scores.values())).value['decision_joint'] == 0 for s in log.samples)
    assert all(next(iter(s.scores.values())).value['schema_valid'] == int(mode != 'malformed') for s in log.samples)
    assert all(s.metadata['final_submission_scheduled'] for s in log.samples)
    assert all(s.metadata['evidence_rounds'] == (5 if mode == 'round_cap' else 2) for s in log.samples)
    for body in seen:
        assert 'acceptable_decisions' not in json.dumps(body['messages'])
        assert 'expected.json' not in json.dumps(body['messages'])
    return {'mode': mode, 'status': 'pass', 'fake_http_requests': guard.calls,
            'actual_tool_calls': len(tools), 'output_reserved': guard.output_reserved,
            'synthetic_usage_not_real_tokens': True, 'network_requests': 0, 'provider_calls': 0,
            'model_quality_measured': False, 'records': guard.records}


if __name__ == '__main__':
    receipts = [run_fixture(mode) for mode in ('normal', 'round_cap', 'malformed')]
    pilot.write_json(pilot.ROOT / 'work/pilot2_transport/RECEIPT.json', {'fixtures': receipts})
    print('PASS: 3 native transport fixtures; 48 fake HTTP requests; 28 real tools; 0 network/provider calls')
