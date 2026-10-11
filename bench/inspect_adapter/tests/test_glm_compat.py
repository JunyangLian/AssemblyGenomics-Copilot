import json
from types import SimpleNamespace

import pytest

from bench.inspect_adapter import glm_compat as compat


def payload(setup, phase):
    value = {'model': setup['model_id'], 'temperature': 0, 'stream': False,
             'messages': [{'role': 'user', 'content': 'offline'}], **setup['extra_body']}
    if phase == 'collect':
        value.update(max_tokens=2048, tools=[{}] * 5, tool_choice='auto')
    else:
        value.update(max_tokens=8192, response_format={'type': 'json_object'})
    return json.dumps(value).encode()


def test_combined_cap_and_thinking_reserved_before_transport():
    setup = compat.plan()
    guard = compat.RequestBudget(setup)
    phases = ['final', 'final'] + (['collect'] * 5 + ['final']) * 2
    for phase in phases:
        guard.reserve('POST', setup['base_url'] + '/chat/completions', payload(setup, phase))
    assert guard.calls == 14
    assert guard.output_reserved == 81920
    assert all(r['output_reserved'] == r['requested_max_tokens'] + 2048 for r in guard.records)
    with pytest.raises(ValueError):
        guard.reserve('POST', setup['base_url'] + '/chat/completions', payload(setup, 'final'))
    assert guard.calls == 14
    assert setup['previous_consumption']['output_reserved'] + guard.output_reserved == 168448


@pytest.mark.parametrize('mutation', [{'thinking_budget': 2049}, {'reasoning_effort': 'high'}, {'enable_thinking': False}])
def test_parameter_drift_reserves_nothing(mutation):
    setup = compat.plan()
    guard = compat.RequestBudget(setup)
    value = json.loads(payload(setup, 'final'))
    value.update(mutation)
    with pytest.raises(ValueError):
        guard.reserve('POST', setup['base_url'] + '/chat/completions', json.dumps(value).encode())
    assert (guard.calls, guard.input_proxy, guard.output_reserved) == (0, 0, 0)


def test_actual_usage_overage_and_empty_final_stop():
    setup = compat.plan()
    body = {'model': setup['model_id'], 'usage': {'completion_tokens': 10241},
            'choices': [{'message': {'content': '{}', 'reasoning_content': 'fixture'}}]}
    guard = compat.RequestBudget(setup)
    compat.observe_body(guard, {'phase': 'final', 'output_reserved': 10240}, 200, json.dumps(body).encode(), '')
    assert guard.stopped_reason == 'reported_output_exceeds_reservation'
    guard.stopped_reason = None
    body['usage']['completion_tokens'] = 1
    body['choices'][0]['message']['content'] = ''
    compat.observe_body(guard, {'phase': 'final', 'output_reserved': 10240}, 200, json.dumps(body).encode(), '')
    assert guard.stopped_reason == 'empty_final_submission'


def test_new_tasks_keep_exact_gold_targets_and_public_messages():
    setup = compat.plan()
    for condition in setup['conditions']:
        task = compat.make_task(setup, condition, True)
        assert len(task.dataset) == 2
        for sample in task.dataset:
            cid = sample.metadata['case_id']
            assert sample.target == (compat.packets.DIRECTORY / 'cases' / cid / 'expected.json').read_text(encoding='utf-8')
            text = str(sample.input)
            assert 'acceptable_decisions' not in text
            assert 'expected.json' not in text


def test_authorization_checked_before_environment_or_transport(monkeypatch):
    def blocked():
        raise ValueError('freeze unavailable')
    monkeypatch.setattr(compat, 'approved', blocked)
    monkeypatch.setattr(compat.os.environ, 'get', lambda *_: pytest.fail('credential read before freeze'))
    with pytest.raises(ValueError, match='freeze unavailable'):
        compat.execute()
