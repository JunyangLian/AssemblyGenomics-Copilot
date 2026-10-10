"""Offline approval and phase guards; fixtures are not real model judgments."""
import json
from types import SimpleNamespace

import pytest

from bench.inspect_adapter import pilot, structured_pilot as revised


def request(plan, phase='collect', **changes):
    body = {'model': plan['model_id'], 'temperature': 0, 'stream': False,
            'max_tokens': plan['evidence_max_tokens'] if phase == 'collect' else plan['final_max_tokens'],
            'enable_thinking': False, 'messages': [{'role': 'user', 'content': 'unit-only fixture'}]}
    if phase == 'collect':
        body.update(tools=[{'type': 'function'}] * 5, tool_choice='auto')
    else:
        body['response_format'] = plan['final_response_format']
    return json.dumps({**body, **changes}).encode()


def test_phase_reservations_track_actual_limits_and_preserve_plan():
    plan = revised.draft_plan()
    guard = revised.RequestBudget(plan)
    for phase in ('collect', 'final'):
        guard.reserve('POST', plan['base_url'] + '/chat/completions', request(plan, phase))
    assert guard.calls == 2 and guard.output_reserved == 512 + 2048
    assert [r['phase'] for r in guard.records] == ['collect', 'final']
    assert guard.plan is plan and plan['max_tokens'] == 2048


@pytest.mark.parametrize('phase,changes', [
    ('collect', {'max_tokens': 2048}), ('collect', {'tools': []}),
    ('collect', {'response_format': {'type': 'text'}}),
    ('final', {'tools': [{'type': 'function'}]}), ('final', {'tool_choice': 'auto'}),
    ('final', {'max_tokens': 4096}), ('final', {'response_format': {'type': 'json_schema'}}),
    ('final', {'enable_thinking': True}),
])
def test_phase_drift_rejected_before_any_request(phase, changes):
    plan = revised.draft_plan()
    guard = revised.RequestBudget(plan)
    with pytest.raises(ValueError):
        guard.reserve('POST', plan['base_url'] + '/chat/completions', request(plan, phase, **changes))
    assert guard.calls == 0 and guard.records == [] and guard.plan is plan


def test_mixed_phase_caps_stop_before_extra_final_request():
    plan = {**revised.draft_plan(), 'max_output_token_reservation': 2560}
    guard = revised.RequestBudget(plan)
    url = plan['base_url'] + '/chat/completions'
    guard.reserve('POST', url, request(plan))
    guard.reserve('POST', url, request(plan, 'final'))
    with pytest.raises(ValueError, match='limit reached'):
        guard.reserve('POST', url, request(plan, 'final'))
    assert guard.calls == 2


def test_bindings_restore_frozen_entry_points_even_after_error():
    before = {name: getattr(pilot, name) for name in revised.BASE}
    directory = pilot.PILOT
    with pytest.raises(RuntimeError):
        with revised.bindings():
            assert pilot.PILOT == revised.DIRECTORY
            raise RuntimeError('unit fixture')
    assert pilot.PILOT == directory
    assert all(getattr(pilot, name) is value for name, value in before.items())


def test_unapproved_new_version_fails_before_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(revised, 'DIRECTORY', tmp_path)
    class UnreadableEnvironment:
        def __setitem__(self, *args):
            raise AssertionError('transport/credential access before approval')
        def get(self, *args):
            raise AssertionError('credential access before approval')
    monkeypatch.setattr(revised, 'os', SimpleNamespace(environ=UnreadableEnvironment()))
    with pytest.raises(ValueError, match='user-approved pilot freeze'):
        revised.execute()


def test_prepare_reuses_answer_bytes_and_prompt_changes_invalidate_freeze(tmp_path, monkeypatch):
    monkeypatch.setattr(revised, 'DIRECTORY', tmp_path)
    for name in ('system.txt', 'final.txt'):
        (tmp_path / name).write_bytes((pilot.ROOT / 'pilot2' / name).read_bytes())
    revised.prepare()
    assert not (tmp_path / 'FROZEN.json').exists()
    for cid in revised.draft_plan()['case_ids']:
        assert (tmp_path / f'answers/{cid}/expected.json').read_bytes() == (
            pilot.ROOT / f'pilot/answers/{cid}/expected.json').read_bytes()
    with revised.bindings():
        pilot.freeze('unit-test simulation only; not user authorization')
        pilot.approved()
        with (tmp_path / 'final.txt').open('ab') as handle:
            handle.write(b'unit changed prompt\n')
        with pytest.raises(ValueError, match='changed'):
            pilot.approved()


def test_generic_prompt_contains_no_private_case_mapping():
    schema = pilot.read_json(pilot.SCHEMA)
    for cid in pilot.CASE_IDS:
        content = json.dumps(revised.messages(pilot.PublicFiles(pilot.CASES / cid), schema), ensure_ascii=False)
        assert 'acceptable_decisions' not in content and 'source_expected_sha256' not in content
        assert 'expected.json' not in content and 'meta.json' not in content
        assert 'dev_00' not in content
