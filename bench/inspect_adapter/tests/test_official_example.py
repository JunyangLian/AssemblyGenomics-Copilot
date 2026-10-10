"""Reject changed upstream sources or version drift before loading task code."""
import shutil

import pytest

from bench.inspect_adapter.official import run


def test_modified_upstream_example_rejected_before_import(tmp_path, monkeypatch):
    shutil.copytree(run.ROOT, tmp_path / 'official')
    monkeypatch.setattr(run, 'ROOT', tmp_path / 'official')
    monkeypatch.setattr(run, 'version', lambda _: '0.3.277')
    path = run.ROOT / 'upstream/tool_use.py'
    path.write_bytes(path.read_bytes() + b'\nraise RuntimeError("changed source must not execute")\n')
    with pytest.raises(ValueError, match='source identity changed'):
        run.upstream_task()


def test_version_drift_is_not_silently_called_upstream_reproduction(monkeypatch):
    monkeypatch.setattr(run, 'version', lambda _: 'different-version')
    with pytest.raises(ValueError, match='versions differ'):
        run.upstream_task()
