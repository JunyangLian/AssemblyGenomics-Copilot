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


def test_cross_project_source_is_rejected_before_extraction(tmp_path):
    server = load_module("bench_prepare_scope_test", "server/prepare_sources.py")
    source = tmp_path / "unrelated_project" / "control.txt"
    roots = {"T1_arabidopsis": [tmp_path / "arabidopsis"]}
    with pytest.raises(ValueError, match="outside declared T1/T3"):
        server.check_scope(source, "T1_arabidopsis", roots)
    with pytest.raises(ValueError, match="outside declared T1/T3"):
        server.check_scope(source, "unregistered_cohort", roots)


def preparation_fixture(tmp_path):
    """Transport names/bytes only; no genome statistics or benchmark cases."""
    snapshot, project, output, t3_root = [tmp_path / n for n in ("snapshot", "project", "output", "t3")]
    snapshot.mkdir(); project.mkdir(); t3_root.mkdir()
    original = project / "control.txt"; original.write_bytes(b"transport control\n")
    copied = snapshot / "copy.txt"; copied.write_bytes(original.read_bytes())
    checksum_lines = [f"{transfer.sha256(original)}  copy.txt\n"]
    for suffix in ("genomic.gff", "protein.faa"):
        filename = f"GCF_000000000.1_control_{suffix}"
        source = t3_root / filename; source.write_bytes(b"transport fixture only\n")
        (snapshot / filename).write_bytes(source.read_bytes())
        checksum_lines.append(f"{transfer.sha256(source)}  {filename}\n")
    (snapshot / "MANIFEST.txt").write_bytes("".join(checksum_lines).encode())
    report = t3_root / "t3_batch_report.tsv"
    report.write_bytes(b"accession\tband_verdict\nGCF_000000000.1\tin_band\n")
    config = {"spec_version": "1.2", "source_scope": "T1_T3", "output_root": str(output),
              "project_root": str(project), "snapshot_root": str(snapshot), "max_file_bytes": 1024,
              "scope_roots": {"T1_arabidopsis": [str(project)], "T1_celegans": [str(project / "celegans")],
                              "T1_yeast": [str(project / "yeast")], "T3": [str(t3_root)]},
              "t3_report": str(report), "t3_accession": None,
              "sources": [{"role": "control", "origin": str(original), "cohort": "T1_arabidopsis",
                           "method": "copy", "max_bytes": 1024, "extension": ".txt", "cases": []}]}
    config_path = tmp_path / "config.json"; transfer.write_json(config_path, config)
    return config_path, output, original


def test_inventory_command_repeats_without_running_tools(tmp_path):
    config_path, output, original = preparation_fixture(tmp_path)
    script = Path(__file__).resolve().parents[1] / "server" / "prepare_sources.py"
    command = [sys.executable, str(script), "--config", str(config_path), "--inventory-only"]
    first = subprocess.run(command, capture_output=True, check=False)
    assert first.returncode == 0, first.stderr
    assert b"COMPLETE" in first.stdout
    before = transfer.verify(output / "bundle")
    second = subprocess.run(command, capture_output=True, check=False)
    assert second.returncode == 0, second.stderr
    assert transfer.verify(output / "bundle") == before
    status = json.loads((output / "bundle" / "STATUS.json").read_text(encoding="utf-8"))
    assert len(status["sources"]) == 1
    assert status["sources"][0]["source_sha256"] == transfer.sha256(original)
    assert not status["jobs"]


def test_preparation_does_not_access_network_or_run_external_tools(tmp_path, monkeypatch):
    import urllib.request
    server = load_module("bench_prepare_offline_test", "server/prepare_sources.py")
    config_path, output, _ = preparation_fixture(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("offline source preparation attempted network or external tool execution")
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(sys, "argv", ["prepare_sources.py", "--config", str(config_path)])
    assert server.main() == 0
    assert transfer.verify(output / "bundle")["verified_files"] > 0


def test_obsolete_download_config_is_rejected(tmp_path, monkeypatch):
    server = load_module("bench_prepare_old_config_test", "server/prepare_sources.py")
    config_path, _, _ = preparation_fixture(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8")); config["busco"] = {}
    transfer.write_json(config_path, config)
    monkeypatch.setattr(sys, "argv", ["prepare_sources.py", "--config", str(config_path)])
    with pytest.raises(SystemExit) as error:
        server.main()
    assert error.value.code == 2


@pytest.mark.parametrize("entry", ["correct", "wrong", "missing", "conflicting", "malformed"])
def test_historical_read_checksum_binding(tmp_path, entry):
    server = load_module("bench_prepare_checksum_test", "server/prepare_sources.py")
    source = tmp_path / "control.txt"
    source.write_bytes(b"transport bytes only\n")
    digest = transfer.sha256(source)
    rows = {"correct": f"{digest}  ./control.txt\n",
            "wrong": f"{'0'*64}  control.txt\n",
            "missing": f"{digest}  different.txt\n",
            "conflicting": f"{digest}  control.txt\n{'0'*64}  control.txt\n",
            "malformed": "not a checksum\n"}
    record = tmp_path / "checksums.txt"
    record.write_bytes(rows[entry].encode())
    if entry == "correct":
        server.check_read_checksum(source, digest, record)
    else:
        with pytest.raises(ValueError):
            server.check_read_checksum(source, digest, record)


def test_source_listing_size_mismatch_blocks_preparation(tmp_path, monkeypatch):
    server = load_module("bench_prepare_size_test", "server/prepare_sources.py")
    config_path, output, _ = preparation_fixture(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["sources"][0]["expected_size_bytes"] = 1
    transfer.write_json(config_path, config)
    monkeypatch.setattr(sys, "argv", ["prepare_sources.py", "--config", str(config_path)])
    assert server.main() == 2
    status = json.loads((output / "bundle" / "STATUS.json").read_text(encoding="utf-8"))
    assert not status["sources"]
    assert any("origin size differs" in gap["reason"] for gap in status["gaps"])
    assert transfer.verify(output / "bundle")["verified_files"] > 0


def test_repeat_sources_do_not_enter_read_pairing(tmp_path, monkeypatch):
    server = load_module("bench_prepare_repeat_test", "server/prepare_sources.py")
    config_path, output, _ = preparation_fixture(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["sources"][0]["role"] = "yeast_repeat_qc"
    transfer.write_json(config_path, config)
    monkeypatch.setattr(sys, "argv", ["prepare_sources.py", "--config", str(config_path)])
    assert server.main() == 0
    assert not (output / "bundle" / "t1_read_pairing.json").exists()


def test_confirmed_yeast_source_config_has_no_repeat_read_bindings():
    config = json.loads((Path(__file__).resolve().parents[1] / "server" /
                         "prepare_config.example.json").read_text(encoding="utf-8"))
    roles = {s["role"]: s for s in config["sources"]}
    for role in ("yeast_repeat_qc", "yeast_repeat_genome", "yeast_repeat_run_record"):
        assert "binding_record_role" not in roles[role]
    for role in ("yeast_rep1_r1", "yeast_rep1_r2", "yeast_rep2_r1", "yeast_rep2_r2"):
        assert roles[role]["origin"].startswith("{project}/yeast_test/0.Raw_Data/rnaseq/")
        assert roles[role]["expected_size_bytes"] > 0
        assert roles[role]["checksum_record_role"] == "yeast_rnaseq_checksums"
        assert roles[role]["binding_record_role"] == "yeast_rnaseq_record"
