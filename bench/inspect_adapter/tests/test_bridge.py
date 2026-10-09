"""Regression guards for denominator preservation and input separation."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bench.inspect_adapter.bridge import archive, final_rows, public_messages, evaluate_output
from bench.inspect_adapter.replay import verify_parity


@pytest.fixture(scope='module')
def report():
    return archive()


def replay_log(report):
    samples = []
    for key, row in final_rows(report).items():
        content = json.dumps(row['parsed']) if row['status'] == 'ok' else ''
        _, labels = evaluate_output(row['status'], content, row['case_id'],
                                    report['cases'][row['case_id']]['expected'])
        samples.append(SimpleNamespace(
            id=key, error=None, output=SimpleNamespace(completion=content),
            metadata={'case_id': row['case_id'], 'group': row['group'],
                      'historical_model': row['model'], 'historical_repetition': row['repetition'],
                      'historical_status': row['status']},
            scores={'qc': SimpleNamespace(value=labels)}))
    return SimpleNamespace(samples=samples)


def test_public_messages_never_read_private_files(monkeypatch):
    original = Path.read_text
    def guarded(path, *args, **kwargs):
        if path.name in {'meta.json', 'expected.json'}:
            raise AssertionError('private file read during public prompt construction')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', guarded)
    for group in ('B', 'C2'):
        messages = public_messages('new_019', group, 'DeepSeek-V4-Pro-0813')
        assert len(messages) == 2
        # Frozen C2 instructions name forbidden private files. Mentioning their
        # names is not reading their contents; keep the original prompt intact.
        packet = json.loads(messages[1]['content'])
        assert set(packet) == {'task', 'artifacts'}
        assert all(Path(a['filename']).name not in {'expected.json', 'meta.json'}
                   for a in packet['artifacts'])


def test_all_failure_types_remain_in_archived_denominator(report):
    rows = final_rows(report)
    assert len(rows) == 648
    assert sum(r['group'] != 'A' for r in rows.values()) == 576
    assert {r['status'] for r in rows.values()} == {'ok', 'api_error', 'parse_error', 'interrupted', 'not_covered'}
    for row in rows.values():
        if row['status'] != 'ok':
            parsed, labels = evaluate_output(row['status'], '', row['case_id'], report['cases'][row['case_id']]['expected'])
            assert parsed is None and not any(labels.values())


def test_replay_cannot_rescue_failure(report):
    row = next(r for r in final_rows(report).values() if r['status'] == 'parse_error')
    with pytest.raises(ValueError, match='must not acquire'):
        evaluate_output(row['status'], '{}', row['case_id'], report['cases'][row['case_id']]['expected'])


def test_duplicate_repetitions_rejected(report):
    altered = copy.deepcopy(report)
    first = next(iter(altered['scored']['groups'][0]['cases'].values()))
    first['observations'][1]['repetition'] = 1
    with pytest.raises(ValueError, match='planned repetition'):
        final_rows(altered)


def test_missing_failure_sample_cannot_shrink_denominator(report):
    log = replay_log(report)
    log.samples = [s for s in log.samples if s.metadata['historical_status'] == 'ok']
    with pytest.raises(ValueError, match='discarded'):
        verify_parity(report, log)


def test_corrupt_inspect_grade_rejected(report):
    log = replay_log(report)
    log.samples[0].scores['qc'].value['joint_correct'] = 9
    with pytest.raises(ValueError, match='scorer disagrees'):
        verify_parity(report, log)


def test_full_log_parity(report, monkeypatch):
    # Base repository tests need no Inspect installation; runtime records version.
    monkeypatch.setattr('bench.inspect_adapter.replay.version', lambda _: 'test-only')
    parity = verify_parity(report, replay_log(report))
    assert parity['status'] == 'pass'
    assert parity['group_case_checks'] == 216
    assert parity['stratified_panels_checked'] == 810
    assert parity['provider_calls'] == 0
