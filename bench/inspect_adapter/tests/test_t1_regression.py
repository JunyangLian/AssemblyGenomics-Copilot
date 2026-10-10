"""Protect legacy targets, explicit coverage gaps and public-message separation."""
import json
from pathlib import Path

import pytest

from bench.inspect_adapter import bridge, t1_regression as regression
from bench.v2.runtime import V2, canonical, read_json


@pytest.fixture(scope='module')
def plan():
    return regression.draft_plan()


def test_selection_retains_binary_gap_and_all_three_t1_sources(plan):
    assert plan['case_counts'] == {'candidates': 20, 'eligible': 19, 'not_supported': 1}
    assert plan['source_case_counts'] == {'T1_arabidopsis': 17, 'T1_yeast': 2, 'T1_celegans': 1}
    assert plan['eligible_source_case_counts'] == {'T1_arabidopsis': 16, 'T1_yeast': 2, 'T1_celegans': 1}
    omitted = [r for r in plan['inventory'] if r['status'] != 'eligible']
    assert [r['case_id'] for r in omitted] == ['regression_002']
    assert 'binary gzip' in omitted[0]['reason']
    assert plan['repetitions'] == 3 and plan['planned_observations'] == 114
    assert plan['max_http_requests_proposed'] == 399
    assert plan['max_output_token_reservation_proposed'] == 379392
    assert not plan['api_call_authorized'] and not plan['new_answers_assigned']


@pytest.mark.parametrize('condition', ['inline', 'tools'])
def test_public_messages_never_open_private_answers_or_metadata(monkeypatch, condition):
    original_bytes, original_text = Path.read_bytes, Path.read_text
    def bytes_guard(path, *args, **kwargs):
        if path.name in {'expected.json', 'meta.json'}:
            raise AssertionError('private case data entered prompt construction')
        return original_bytes(path, *args, **kwargs)
    def text_guard(path, *args, **kwargs):
        if path.name in {'expected.json', 'meta.json'}:
            raise AssertionError('private case data entered prompt construction')
        return original_text(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_bytes', bytes_guard)
    monkeypatch.setattr(Path, 'read_text', text_guard)
    for cid in regression.CASE_IDS:
        if cid == 'regression_002':
            continue
        messages = regression.messages(cid, condition)
        user = json.loads(messages[1]['content'])
        assert set(user) == ({'task', 'files'} if condition == 'tools' else {'task', 'artifacts'})
        assert 'key_evidence' not in user and 'acceptable_verdicts' not in user


def test_no_other_source_or_binary_case_silently_gets_an_input():
    for cid in ('new_019', 'regression_013', 'regression_002', '../expected.json'):
        with pytest.raises(ValueError, match='unsupported'):
            regression.messages(cid, 'tools')


def test_all_selected_historical_labels_keep_legacy_contract(plan):
    report = bridge.archive()
    checked = 0
    for row in bridge.final_rows(report).values():
        if row['case_id'] not in plan['case_ids']:
            continue
        expected = read_json(V2 / 'cases' / row['case_id'] / 'expected.json')
        assert expected == report['cases'][row['case_id']]['expected']
        text = canonical(row['parsed']).decode('utf-8') if row['status'] == 'ok' else ''
        _, labels = bridge.evaluate_output(row['status'], text, row['case_id'], expected)
        verdict = bool(row['parsed'] and row['parsed']['verdict'] in expected['acceptable_verdicts'])
        root = bool(row['parsed'] and row['parsed']['root_cause'] == expected['root_cause'])
        assert labels == {'verdict_correct': int(verdict), 'root_correct': int(root),
                          'joint_correct': int(verdict and root), 'valid_output': int(row['status'] == 'ok')}
        checked += 1
    assert checked == 19 * 9 * 3  # Four models x two historical groups, plus A.


def test_malformed_or_private_evidence_does_not_gain_legacy_credit():
    expected = read_json(V2 / 'cases/regression_012/expected.json')
    output = {'verdict': 'pass', 'root_cause': 'none', 'evidence': ['expected.json:1'],
              'action': 'Fixture.', 'proposes_threshold_relaxation': False, 'proposes_skipping_check': False}
    with pytest.raises(ValueError, match='legacy parser'):
        bridge.evaluate_output('ok', json.dumps(output), 'regression_012', expected)
    with pytest.raises(ValueError, match='legacy parser'):
        bridge.evaluate_output('ok', 'Not JSON', 'regression_012', expected)


def test_reviewed_draft_is_not_silently_overwritten(tmp_path):
    path = tmp_path / 'PLAN.draft.json'
    regression.save_draft(path, b'original\n')
    regression.save_draft(path, b'original\n')
    with pytest.raises(ValueError, match='new version'):
        regression.save_draft(path, b'replacement\n')
    assert path.read_bytes() == b'original\n'
