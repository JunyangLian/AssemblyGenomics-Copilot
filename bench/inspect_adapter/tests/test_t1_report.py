"""Reporting must retain unsuccessful slots and never promote offline fixtures."""
from pathlib import Path

import pytest

from bench.inspect_adapter import pilot, t1_live as live, t1_report as report


@pytest.fixture
def failed_run(tmp_path, monkeypatch):
    setup = live.plan()
    directory = tmp_path / 'public'
    directory.mkdir()
    (directory / 'FROZEN.json').write_bytes(b'frozen reporting fixture\n')
    output = tmp_path / 'work/run'
    output.mkdir(parents=True)
    monkeypatch.setattr(live, 'DIRECTORY', directory)
    monkeypatch.setattr(live, 'WORK', tmp_path / 'work')
    monkeypatch.setattr(live, 'approved', lambda: setup)
    rows = [{'condition': c, 'case_id': cid, 'repetition': rep, 'status': 'missing', 'parsed': None,
             'scores': {}, 'tool_calls': 0, 'tool_errors': 0}
            for c in setup['conditions'] for cid in setup['case_ids'] for rep in (1, 2, 3)]
    result = {'run_id': 'fixture-reporting-only', 'fixture': False, 'rows': rows,
        'frozen_sha256': pilot.sha((directory / 'FROZEN.json').read_bytes()),
        'summary': live.summarize(setup, rows), 'fatal_error_class': 'OfflineTest'}
    pilot.write_json(output / 'RESULTS.json', result)
    pilot.write_json(output / 'REQUEST_BUDGET.json', {'fixture': False, 'calls': 0, 'records': [],
        'input_proxy': 0, 'output_reserved': 0, 'stopped_reason': 'offline-testing-only'})
    return directory, output, result


def test_all_missing_run_has_full_denominators_and_no_cost(failed_run):
    directory, output, _ = failed_run
    receipt = report.export(output)
    assert receipt['observations'] == {'missing': 114}
    assert receipt['reference_cost_cny'] == 0
    assert receipt['conditions']['inline']['case_counts']['joint_correct'] == 0
    text = (directory / 'REPORT.md').read_text(encoding='utf-8')
    assert '0/19 (0.0%)' in text and '0/57 (0.0%)' in text
    assert '不是账单' in text and '没有独立真人专家盲审' in text


def test_mock_or_lost_slot_cannot_be_published_as_completed(failed_run):
    directory, output, result = failed_run
    pilot.write_json(output / 'RESULTS.json', {**result, 'fixture': True})
    with pytest.raises(ValueError, match='fixture'):
        report.export(output)
    pilot.write_json(output / 'RESULTS.json', {**result, 'rows': result['rows'][:-1]})
    with pytest.raises(ValueError, match='slots'):
        report.export(output)
    assert not (directory / 'RUN_RECEIPT.json').exists()
