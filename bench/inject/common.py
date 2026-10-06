from __future__ import annotations

from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path
import re


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


@dataclass
class Artifact:
    data: bytes
    roles: tuple[str, ...]
    selection: str
    method: str = "derived_summary"
    text_origin: str = "derived"
    verbatim_selection: str | None = None


class Sources:
    def __init__(self, bundle: Path, receipt: Path):
        self.root = bundle.resolve(strict=True)
        self.receipt = receipt.resolve(strict=True)
        proof = json.loads(self.receipt.read_text(encoding="utf-8"))
        if not proof.get("usable_for_cases") or proof.get("preparation_status") != "complete":
            raise ValueError("source bundle has no successful acceptance receipt")
        if digest((self.root / "MANIFEST.json").read_bytes()) != proof["manifest_sha256"]:
            raise ValueError("receipt belongs to a different source manifest")
        status = json.loads((self.root / "STATUS.json").read_text(encoding="utf-8"))
        if status["status"] != "complete":
            raise ValueError("source preparation is incomplete")
        self.rows = {r["role"]: r for r in status["sources"]}
        self.manifest = json.loads((self.root / "MANIFEST.json").read_text(encoding="utf-8"))
        self.entries = {r["path"]: r for r in self.manifest["files"]}
        self.record_sha = self.entries["STATUS.json"]["sha256"]
        if digest((self.root / "STATUS.json").read_bytes()) != self.record_sha:
            raise ValueError("preparation record differs from accepted bytes")
        for row in self.rows.values():
            if row["cohort"] not in {"T1_arabidopsis", "T1_celegans", "T1_yeast", "T3"}:
                raise ValueError("source outside authorized cohorts")
            if row["package_sha256"] != self.entries[row["package_path"]]["sha256"]:
                raise ValueError("preparation record differs from accepted manifest")

    def path(self, role: str) -> Path:
        original = self.root / self.rows[role]["package_path"]
        if any(p.is_symlink() for p in [original, *original.parents]):
            raise ValueError("source symlink is not allowed")
        p = original.resolve(strict=True)
        if self.root not in p.parents or p.is_symlink():
            raise ValueError("source path leaves accepted bundle")
        return p

    def raw(self, role: str) -> bytes:
        return self.path(role).read_bytes()

    def text(self, role: str) -> str:
        data = self.raw(role)
        if self.path(role).suffix == ".gz":
            data = gzip.decompress(data)
        return data.decode("utf-8").replace("\r\n", "\n")

    def json(self, role: str):
        return json.loads(self.text(role))

    def reference(self, role: str) -> dict:
        r = self.rows[role]
        return {"path": self.path(role).as_posix(), "source_origin": r["source_origin"],
                "sha256": r["package_sha256"], "source_origin_sha256": r["source_sha256"],
                "size_bytes": self.entries[r["package_path"]]["size_bytes"], "role": role,
                "cohort": r["cohort"], "source_kind": "prepared_subset",
                "preparation_record_sha256": self.record_sha}


def fasta_records(text: str) -> list[tuple[str, str]]:
    records, header, parts = [], None, []
    for line in text.splitlines():
        if line.startswith(">"):
            if header is not None:
                records.append((header, "".join(parts)))
            header, parts = line[1:].split()[0], []
        elif line.strip():
            if header is None:
                raise ValueError("sequence before FASTA header")
            parts.append(line.strip())
    if header is not None:
        records.append((header, "".join(parts)))
    return records


def fasta_bytes(records) -> bytes:
    return "".join(">" + ident + "\n" + "\n".join(seq[i:i+80] for i in range(0, len(seq), 80)) + "\n"
                   for ident, seq in records).encode("utf-8")


def dna_prefix(src: Sources, length: int = 6000) -> tuple[str, str]:
    ident, seq = fasta_records(src.text("arab_repeat_genome"))[0]
    if len(seq) < length:
        raise ValueError("real DNA subset is shorter than requested")
    return ident, seq[:length]


def complete_gene_blocks(text: str, seqid: str | None = None, limit: int = 1, full_source: bool = False):
    blocks, current = [], []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 9:
            raise ValueError("source feature row must have nine columns")
        if fields[2] == "gene":
            if current and (seqid is None or current[0].split("\t")[0] == seqid):
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)
    # Prepared prefixes may end inside a gene: never use that last block.
    if full_source and current and (seqid is None or current[0].split("\t")[0] == seqid):
        blocks.append(current)
    if len(blocks) < limit:
        raise ValueError("source excerpt lacks enough complete gene blocks")
    return blocks[:limit]


def busco_summary(text: str) -> dict:
    result = re.search(r"C:([\d.]+)%\[S:([\d.]+)%,D:([\d.]+)%\],F:([\d.]+)%,M:([\d.]+)%,n:(\d+)", text)
    lineage = re.search(r"lineage dataset is:\s*(\S+)", text)
    mode = re.search(r"run in mode:\s*(\S+)", text)
    if not result or not lineage or not mode:
        raise ValueError("real BUSCO summary has an unsupported format")
    names = ("complete_pct", "single_pct", "duplicated_pct", "fragmented_pct", "missing_pct")
    return {**dict(zip(names, map(float, result.groups()[:5]))), "n": int(result[6]),
            "lineage": lineage[1], "mode": mode[1]}


def projected_repeat_qc(src: Sources, role: str) -> dict:
    qc = src.json(role)
    return {k: qc[k] for k in ("ids_equal", "lengths_equal", "sequence_equal_ignorecase", "lowercase_pct", "n_pct")}


def tool_versions(src: Sources, role: str) -> dict:
    tools = src.json(role)["tools"]
    version = next(re.search(r"Version\s*:\s*(\S+)", row)[1] for row in tools["famdb"] if "Version" in row)
    return {"repeatmodeler": tools["repeatmodeler"], "repeatmasker": tools["repeatmasker"],
            "database": "Dfam", "database_version": version}
