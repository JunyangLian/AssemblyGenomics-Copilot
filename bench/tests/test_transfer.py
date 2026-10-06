"""Transport-only fixtures: no fabricated genome artifacts or benchmark cases."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


transfer = load_module("bench_transfer_test", "transfer.py")


def make_bundle(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "内容 with space.txt").write_bytes(b"transport control\n")
    transfer.write_json(root / "STATUS.json", {"status": "complete"})
    transfer.manifest(root)
    return root


def test_unicode_paths_and_deterministic_manifest(tmp_path):
    root = make_bundle(tmp_path)
    before = {name: transfer.sha256(root / name) for name in transfer.CONTROL}
    result = transfer.verify(root)
    assert result["verified_files"] == 2
    transfer.manifest(root)
    assert before == {name: transfer.sha256(root / name) for name in transfer.CONTROL}
    assert b"\r\n" not in (root / "MANIFEST.json").read_bytes()


@pytest.mark.parametrize("operation", ["tamper", "extra", "missing"])
def test_changed_payload_is_rejected(tmp_path, operation):
    root = make_bundle(tmp_path)
    target = root / "内容 with space.txt"
    if operation == "tamper":
        target.write_bytes(b"transport changed\n")
    elif operation == "extra":
        (root / "unlisted.txt").write_bytes(b"extra\n")
    else:
        target.unlink()
    with pytest.raises(ValueError):
        transfer.verify(root)


@pytest.mark.parametrize("name", ["../outside", "/outside", "C:/outside", "a\\outside", "a/../outside", "./outside"])
def test_manifest_path_escape_is_rejected(tmp_path, name):
    root = make_bundle(tmp_path)
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = name
    transfer.write_json(root / "MANIFEST.json", manifest)
    with pytest.raises(ValueError, match="manifest path"):
        transfer.verify(root)


def test_duplicate_checksum_is_rejected(tmp_path):
    root = make_bundle(tmp_path)
    path = root / "MANIFEST.sha256"
    path.write_bytes(path.read_bytes() + path.read_bytes().splitlines(keepends=True)[0])
    with pytest.raises(ValueError, match="duplicate checksum"):
        transfer.verify(root)


def test_source_hash_conflict_and_immutable_write(tmp_path):
    server = load_module("bench_prepare_test", "server/prepare_sources.py")
    source = tmp_path / "source.txt"
    source.write_bytes(b"source\n")
    digest = transfer.sha256(source)
    manifest = tmp_path / "MANIFEST.txt"
    manifest.write_bytes(f"{digest}  source.txt\n{'0'*64}  source.txt\n".encode())
    with pytest.raises(ValueError, match="conflicting"):
        server.snapshot_index(tmp_path)
    destination = tmp_path / "fixed.txt"
    server.save_immutable(destination, b"transport\n")
    server.save_immutable(destination, b"transport\n")
    with pytest.raises(ValueError, match="differs"):
        server.save_immutable(destination, b"different\n")
    assert destination.read_bytes() == b"transport\n"


def test_sra_network_failure_blocks_tool_execution(tmp_path, monkeypatch):
    server = load_module("bench_prepare_network_test", "server/prepare_sources.py")
    def offline(*args, **kwargs):
        raise OSError("network unavailable")
    def no_tool(*args, **kwargs):
        pytest.fail("SRA tool must not run after a failed identity/network check")
    monkeypatch.setattr(server.urllib.request, "urlopen", offline)
    monkeypatch.setattr(server, "run", no_tool)
    config = {"runs": ["SRR1", "SRR2"], "spots": 10}
    with pytest.raises(ValueError, match="external access/identity"):
        server.prepare_sra(config, tmp_path / "bundle", tmp_path / "work")


def test_inventory_command_repeats_without_running_tools(tmp_path):
    # Plain transport bytes only, never a genome/statistics fixture.
    snapshot, project, output = [tmp_path / n for n in ("snapshot", "project", "output")]
    snapshot.mkdir(); project.mkdir()
    original = project / "control.txt"; original.write_bytes(b"transport control\n")
    copied = snapshot / "copy.txt"; copied.write_bytes(original.read_bytes())
    (snapshot / "MANIFEST.txt").write_bytes(f"{transfer.sha256(original)}  copy.txt\n".encode())
    config = {"output_root": str(output), "project_root": str(project),
              "snapshot_root": str(snapshot), "max_file_bytes": 1024,
              "sources": [{"role": "control", "origin": str(original), "method": "copy",
                           "max_bytes": 1024, "extension": ".txt", "cases": []}]}
    config_path = tmp_path / "config.json"; transfer.write_json(config_path, config)
    script = Path(__file__).resolve().parents[1] / "server" / "prepare_sources.py"
    command = [sys.executable, str(script), "--config", str(config_path), "--inventory-only"]
    first = subprocess.run(command, capture_output=True, check=False)
    assert first.returncode == 2, first.stderr
    assert b"BLOCKED" in first.stdout
    before = transfer.verify(output / "bundle")
    second = subprocess.run(command, capture_output=True, check=False)
    assert second.returncode == 2, second.stderr
    assert transfer.verify(output / "bundle") == before
    status = json.loads((output / "bundle" / "STATUS.json").read_text(encoding="utf-8"))
    assert len(status["sources"]) == 1
    assert status["sources"][0]["source_sha256"] == transfer.sha256(original)
    assert not status["jobs"]
