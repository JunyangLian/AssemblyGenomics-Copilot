"""Protect the approved live scope, physical request limits, and failed slots."""
import json
from pathlib import Path

import pytest

from bench.inspect_adapter import structured_pilot, t1_live as live
from bench.v2.runtime import write_json


@pytest.fixture(scope='module')
def setup():
    return live.plan()


def test_approved_scope_has_no_budget_or_case_expansion(setup):
    assert setup['planned_observations'] == 114 and len(setup['case_ids']) == 19
    assert setup['api_call_authorized'] and not setup['new_answers_assigned']
    assert setup['max_http_requests'] == 399
    assert setup['max_input_proxy_tokens'] == 2_000_000
    assert setup['max_output_token_reservation'] == 379392
    assert setup['automatic_retries'] == setup['sdk_retries'] == setup['format_retries'] == 0
    assert setup['analysis']['primary_unit'].startswith('case')


def test_freeze_tamper_fails_before_credential_access(tmp_path, monkeypatch, setup):
    monkeypatch.setattr(live, 'DIRECTORY', tmp_path)
    monkeypatch.setattr(live, 'plan', lambda: setup)
    live.prepare()
    assert live.approved() == setup
    with pytest.raises(ValueError, match='already frozen'):
        live.prepare()
    write_json(tmp_path / 'PLAN.json', {**setup, 'max_http_requests': 400})
    with pytest.raises(ValueError, match='frozen'):
        live.approved()


def final_request(setup):
    return json.dumps({'model': setup['model_id'], 'messages': [], 'temperature': 0,
        'stream': False, 'max_tokens': 2048, 'enable_thinking': False,
        'response_format': {'type': 'json_object'}}).encode()


def test_limits_count_reserved_calls_even_without_response(setup):
    guard = structured_pilot.RequestBudget({**setup, 'max_http_requests': 1})
    url = setup['base_url'] + '/chat/completions'
    guard.reserve('POST', url, final_request(setup))
    assert guard.calls == 1 and guard.output_reserved == 2048 and guard.records[0]['phase'] == 'final'
    with pytest.raises(ValueError, match='limit reached'):
        guard.reserve('POST', url, final_request(setup))
    assert guard.calls == 1


@pytest.mark.parametrize('status,model,usage,reason', [
    (429, None, {}, 'provider_stop_status_429'),
    (200, 'other-model', {}, 'unapproved_returned_model_identity'),
    (200, 'deepseek-ai/DeepSeek-V4-Flash', {'completion_tokens_details': {'reasoning_tokens': 1}}, 'unexpected_reasoning_usage')])
def test_provider_stop_blocks_following_physical_requests(setup, status, model, usage, reason):
    guard = structured_pilot.RequestBudget(setup)
    record = {}
    data = json.dumps({'model': model, 'usage': usage, 'error': 'private-fixture-key'}).encode()
    redacted = live.observe_body(guard, record, status, data, 'private-fixture-key')
    assert b'private-fixture-key' not in redacted and guard.stopped_reason == reason
    with pytest.raises(ValueError, match='stopped'):
        guard.reserve('POST', setup['base_url'] + '/chat/completions', final_request(setup))
    assert guard.calls == 0


def test_failed_and_missing_slots_are_not_dropped(setup):
    rows = [{'condition': condition, 'case_id': cid, 'repetition': rep, 'status': 'missing',
             'parsed': None, 'scores': {}, 'tool_calls': 0, 'tool_errors': 0}
            for condition in setup['conditions'] for cid in setup['case_ids'] for rep in (1, 2, 3)]
    groups = live.summarize(setup, rows)
    for group in groups.values():
        assert group['observations_planned'] == 57 and len(group['cases']) == 19
        assert group['statuses'] == {'missing': 57}
        assert group['case_counts']['joint_correct'] == group['observation_counts']['joint_correct'] == 0
        assert all(r['incomplete_repeats'] == 3 for r in group['cases'])
