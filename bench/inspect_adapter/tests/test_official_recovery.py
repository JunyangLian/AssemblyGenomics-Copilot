"""Original budget and source identity cannot be silently reset on recovery."""
import json
from types import SimpleNamespace

import pytest

from bench.inspect_adapter.official import recover


@pytest.fixture
def recovery(tmp_path, monkeypatch):
    previous = tmp_path / 'previous'
    previous.mkdir()
    (previous / 'REQUEST_BUDGET.json').write_text(json.dumps({'calls': 12, 'stopped_reason': None}), encoding='utf-8')
    monkeypatch.setattr(recover, 'PREVIOUS', previous)
    monkeypatch.setattr(recover, 'DIRECTORY', tmp_path / 'recovery')
    monkeypatch.setattr(recover.live, 'approved', lambda: {'max_http_requests': 32})
    monkeypatch.setattr(recover, 'originals', lambda: {'original-result': '1' * 64})
    monkeypatch.setattr(recover, 'selection', lambda: {'theory_of_mind': [5]})
    recover.prepare()
    return recover.DIRECTORY


def test_remaining_budget_is_inherited_not_refreshed(recovery):
    plan = json.loads((recovery / 'PLAN.json').read_text())
    assert plan['calls_already_reserved'] == 12 and plan['calls_remaining'] == 20
    assert plan['full_run'] is False and plan['selection'] == {'theory_of_mind': [5]}


def test_changed_previous_records_rejected_before_key(recovery, monkeypatch):
    monkeypatch.setattr(recover, 'originals', lambda: {'original-result': '2' * 64})
    def forbid(*args):
        raise AssertionError('credential accessed before original identity check')
    monkeypatch.setattr(recover, 'os', SimpleNamespace(environ=SimpleNamespace(get=forbid)))
    with pytest.raises(ValueError, match='original records changed'):
        recover.execute()
