"""Offline gate, score and budget tests; no provider or model generation."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bench.inspect_adapter import pilot
from bench.inspect_adapter.readonly import PublicFiles


@pytest.fixture
def plan():
    return pilot.draft_plan()


def request(plan, **changes):
    return json.dumps({'model': plan['model_id'], 'temperature': 0,
                       'max_tokens': 2048, 'stream': False,
                       'messages': [{'role': 'user', 'content': 'unit request'}], **changes}).encode()


def test_api_gate_precedes_credentials_and_imports(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, 'PILOT', tmp_path)
    class UnreadableEnvironment:
        def get(self, *args):
            raise AssertionError('credential accessed before approval')
    monkeypatch.setattr(pilot, 'os', SimpleNamespace(environ=UnreadableEnvironment()))
    with pytest.raises(ValueError, match='user-approved pilot freeze'):
        pilot.execute()


def test_public_prompt_does_not_read_private_files(monkeypatch):
    files = PublicFiles(pilot.CASES / 'dev_001')
    schema = pilot.read_json(pilot.SCHEMA)
    def denied(*args, **kwargs):
        raise AssertionError('filesystem access during message building')
    monkeypatch.setattr(Path, 'read_bytes', denied)
    monkeypatch.setattr(Path, 'read_text', denied)
    messages = pilot.messages(files, schema)
    assert set(json.loads(messages[1]['content'])) == {'task', 'files'}
    assert 'acceptable_decisions' not in messages[0]['content'] + messages[1]['content']


def test_http_request_ceiling_includes_every_reserved_attempt(plan):
    guard = pilot.RequestBudget({**plan, 'max_http_requests': 2})
    url = plan['base_url'] + '/chat/completions'
    guard.reserve('POST', url, request(plan))
    guard.reserve('POST', url, request(plan))
    with pytest.raises(ValueError, match='limit reached'):
        guard.reserve('POST', url, request(plan))
    assert guard.calls == 2 and len(guard.records) == 2


@pytest.mark.parametrize('changes', [{'model': 'other-model'}, {'temperature': 0.5},
                                     {'max_tokens': 8192}, {'stream': True}])
def test_parameter_drift_rejected_before_reservation(plan, changes):
    guard = pilot.RequestBudget(plan)
    with pytest.raises(ValueError, match='parameters differ'):
        guard.reserve('POST', plan['base_url'] + '/chat/completions', request(plan, **changes))
    assert guard.calls == 0


def test_no_redirects_or_unplanned_endpoint(plan):
    guard = pilot.RequestBudget(plan)
    with pytest.raises(ValueError, match='endpoint'):
        guard.reserve('POST', 'https://other.example/v1/chat/completions', request(plan))
    with pytest.raises(ValueError, match='endpoint'):
        guard.reserve('GET', plan['base_url'] + '/models', request(plan))
    assert guard.calls == 0


@pytest.mark.parametrize('field', ['max_input_proxy_tokens', 'max_output_token_reservation', 'max_request_bytes'])
def test_reservation_caps_stop_before_request(plan, field):
    guard = pilot.RequestBudget({**plan, field: 1})
    with pytest.raises(ValueError, match='limit reached'):
        guard.reserve('POST', plan['base_url'] + '/chat/completions', request(plan))
    assert guard.calls == 0 and guard.records == []


def test_provider_stop_prevents_next_physical_request(plan):
    guard = pilot.RequestBudget(plan)
    guard.stopped_reason = 'provider_auth_or_quota_status_429'
    with pytest.raises(ValueError, match='pilot stopped'):
        guard.reserve('POST', plan['base_url'] + '/chat/completions', request(plan))
    assert guard.calls == 0


def answer():
    return {'verdict': 'rollback', 'observed_defect': 'low_functional_coverage',
            'root_cause': 'insufficient_evidence',
            'evidence': [{'pointer': 'artifacts/annotation.tsv:query',
                          'observation': 'unit-only intentionally unverified statement'}],
            'action': '核对证据后再交付', 'proposes_threshold_relaxation': False,
            'proposes_skipping_check': False}


def score(output):
    files = PublicFiles(pilot.CASES / 'dev_001')
    expected = pilot.read_json(pilot.CASES / 'dev_001/expected.json')
    return pilot.score_output(json.dumps(output, ensure_ascii=False), expected, files, pilot.read_json(pilot.SCHEMA))


def test_decision_and_locator_are_not_semantic_evidence_validation():
    labels, parsed, error = score(answer())
    assert labels == {'schema_valid': 1, 'evidence_locator_valid': 1, 'decision_joint': 1}
    assert parsed['evidence'][0]['observation'] == 'unit-only intentionally unverified statement'
    assert 'strict_success' not in labels and error is None


def test_observed_defect_is_part_of_joint_decision():
    output = answer()
    output['observed_defect'] = 'empty_hints'
    assert score(output)[0]['decision_joint'] == 0


def test_nonexistent_locator_not_scored_as_supported():
    output = answer()
    output['evidence'][0]['pointer'] = 'artifacts/annotation.tsv:absent_field'
    labels, _, error = score(output)
    assert labels['schema_valid'] == 1 and labels['evidence_locator_valid'] == 0 and error


def test_invalid_and_empty_outputs_keep_zero_labels():
    for content in ('', '{}', '{"verdict":"pass","verdict":"warn"}'):
        labels, parsed, error = pilot.score_output(content, {}, PublicFiles(pilot.CASES / 'dev_001'), pilot.read_json(pilot.SCHEMA))
        assert not any(labels.values()) and parsed is None and error


def test_freeze_simulation_only_in_tmp_and_change_detection(tmp_path, monkeypatch):
    # Test approval is a simulated fixture, never a production authorization.
    monkeypatch.setattr(pilot, 'PILOT', tmp_path)
    pilot.prepare()
    assert not (tmp_path / 'FROZEN.json').exists()
    with pytest.raises(ValueError, match='real approval quote'):
        pilot.freeze('')
    pilot.freeze('unit-test simulated approval, not an actual user authorization')
    plan, answers = pilot.approved()
    assert len(answers) == 4 and plan['max_http_requests'] == 32
    frozen = pilot.read_json(tmp_path / 'FROZEN.json')
    for cid, expected_hash in frozen['answers'].items():
        path = tmp_path / 'answers' / cid / 'expected.json'
        assert pilot.sha(path.read_bytes()) == expected_hash
        assert f'answers/{cid}/expected.json' in (tmp_path / 'FROZEN.md').read_text()
    with pytest.raises(ValueError, match='never replace'):
        pilot.freeze('unit-test second approval')
    modified = pilot.read_json(tmp_path / 'plan.draft.json')
    modified['max_http_requests'] = 33
    pilot.write_json(tmp_path / 'plan.draft.json', modified)
    with pytest.raises(ValueError, match='changed'):
        pilot.approved()


def test_modified_answer_file_cannot_be_frozen(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, 'PILOT', tmp_path)
    pilot.prepare()
    path = tmp_path / 'answers/dev_001/expected.json'
    changed = pilot.read_json(path)
    changed['acceptable_decisions'][0]['verdict'] = 'pass'
    pilot.write_json(path, changed)
    with pytest.raises(ValueError, match='expected.json differs'):
        pilot.freeze('unit-test simulated approval')
    assert not (tmp_path / 'APPROVAL.json').exists()


def test_one_approval_cannot_reset_budget_by_starting_a_second_run(tmp_path):
    frozen_hash = 'a' * 64
    path = pilot.claim_run(tmp_path, frozen_hash, 'unit-run-1')
    assert pilot.read_json(path)['run_id'] == 'unit-run-1'
    with pytest.raises(ValueError, match='already claimed'):
        pilot.claim_run(tmp_path, frozen_hash, 'unit-run-2')
    assert pilot.read_json(path)['run_id'] == 'unit-run-1'
