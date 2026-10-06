"""Byte-preserving, fail-closed transport manifests (no biological QC rules)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

CONTROL = {"MANIFEST.json", "MANIFEST.sha256"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True,
                                 indent=2) + "\n").encode("utf-8"))


def files(root: Path) -> dict[str, Path]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed: {path}")
        if path.is_file():
            name = path.relative_to(root).as_posix()
            if any(c in name for c in "\r\n\\"):
                raise ValueError(f"unsupported manifest filename: {name!r}")
            result[name] = path
    return result


def manifest(root: Path) -> None:
    entries = [{"path": name, "sha256": sha256(path),
                "size_bytes": path.stat().st_size}
               for name, path in files(root).items() if name not in CONTROL]
    write_json(root / "MANIFEST.json", {"format": 1, "files": entries})
    all_entries = files(root)
    lines = [f"{sha256(path)}  {name}\n" for name, path in all_entries.items()
             if name != "MANIFEST.sha256"]
    (root / "MANIFEST.sha256").write_bytes("".join(lines).encode("utf-8"))


def verify(root: Path) -> dict:
    if root.is_symlink():
        raise ValueError("bundle root cannot be a symlink")
    root = root.resolve(strict=True)
    actual = files(root)
    data = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    if data.get("format") != 1 or not isinstance(data.get("files"), list):
        raise ValueError("unsupported manifest format")
    expected = {}
    for row in data["files"]:
        name = row["path"]
        rel = PurePosixPath(name)
        if (not name or rel.is_absolute() or ".." in rel.parts or
                "\\" in name or ":" in name or rel.as_posix() != name or
                name in CONTROL or name in expected):
            raise ValueError(f"invalid/duplicate manifest path: {name!r}")
        expected[name] = row
    if set(actual) != set(expected) | CONTROL:
        raise ValueError(f"file set mismatch: missing={sorted(set(expected)-set(actual))}; "
                         f"extra={sorted(set(actual)-set(expected)-CONTROL)}")
    for name, row in expected.items():
        if (actual[name].stat().st_size != row["size_bytes"] or
                sha256(actual[name]) != row["sha256"]):
            raise ValueError(f"size/SHA-256 mismatch: {name}")
    checksum_rows = {}
    for line in (root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if name in checksum_rows:
            raise ValueError(f"duplicate checksum path: {name}")
        checksum_rows[name] = digest
    if set(checksum_rows) != set(actual) - {"MANIFEST.sha256"}:
        raise ValueError("checksum manifest file set mismatch")
    for name, digest in checksum_rows.items():
        if sha256(actual[name]) != digest:
            raise ValueError(f"checksum manifest mismatch: {name}")
    return {"verified_files": len(expected),
            "verified_bytes": sum(row["size_bytes"] for row in expected.values()),
            "manifest_sha256": sha256(root / "MANIFEST.json"),
            "checksum_manifest_sha256": sha256(root / "MANIFEST.sha256")}
