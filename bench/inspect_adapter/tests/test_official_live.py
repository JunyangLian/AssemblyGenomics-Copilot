"""Selection/approval changes fail before credentials or HTTP access."""
import json
from types import SimpleNamespace

import pytest

from bench.inspect_adapter.official import live


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    monkeypatch.setattr(live, 'DIRECTORY', tmp_path)
    monkeypatch.setattr(live, 'candidates', lambda: [{'task': 'unit_only', 'index': 1,
                         'target': 'unit-only official target fixture', 'target_sha256': '2' * 64}])
    monkeypatch.setattr(live, 'file_hashes', lambda: {'upstream-fixture': '1' * 64})
    live.prepare()
    return tmp_path


@pytest.mark.parametrize('name', ['PLAN.json', 'TARGETS.json', 'APPROVAL.json'])
def test_changed_plan_selection_or_approval_blocked_before_key_access(frozen, monkeypatch, name):
    path = frozen / name
    data = json.loads(path.read_text())
    if isinstance(data, list):
        data[0]['target'] = 'replacement'
    else:
        data['replacement'] = True
    path.write_text(json.dumps(data), encoding='utf-8', newline='\n')
    def forbid(*args):
        raise AssertionError('credential accessed before freeze verification')
    monkeypatch.setattr(live, 'os', SimpleNamespace(environ=SimpleNamespace(get=forbid)))
    with pytest.raises(ValueError, match='frozen sources or plan changed'):
        live.execute()


def test_prepare_does_not_overwrite_an_existing_approved_snapshot(frozen):
    before = (frozen / 'FROZEN.json').read_bytes()
    with pytest.raises(ValueError, match='no overwrite'):
        live.prepare()
    assert (frozen / 'FROZEN.json').read_bytes() == before
