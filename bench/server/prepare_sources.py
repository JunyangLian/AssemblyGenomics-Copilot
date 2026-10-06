"""First server round: offline provenance checks and bounded T1/T3 extraction.

No cases/answers, model calls, annotation pipelines, or A-group scoring here.
Python 3.10+, standard library only. User runs this on the Linux server.
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import io
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transfer import files, manifest, sha256, verify, write_json


def path(value: str) -> Path:
    if not value:
        raise ValueError("required path is not configured")
    return Path(value).expanduser().resolve(strict=True)


def text_stream(source: Path):
    return (gzip.open(source, "rt", encoding="utf-8", newline=None)
            if source.suffix == ".gz" else source.open("r", encoding="utf-8", newline=None))


def save_immutable(destination: Path, content: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_bytes() != content:
        raise ValueError(f"existing payload differs; use a new fixed output directory: {destination}")
    destination.write_bytes(content)


def check_read_checksum(origin: Path, digest: str, checksum_file: Path) -> None:
    """Bind a read to the historical sha256sum list, without guessing hashes."""
    matches = set()
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-fA-F0-9]{64}) [ *](.+)", line)
        if not match:
            raise ValueError("invalid historical RNA-seq checksum line")
        if Path(match[2]).name == origin.name:
            matches.add(match[1].lower())
    if matches != {digest}:
        raise ValueError("T1 read SHA is missing, conflicting, or differs from rnaseq.sha256")


def snapshot_index(root: Path) -> tuple[dict[str, list[Path]], dict]:
    source = root / "MANIFEST.txt"
    grouped, named = {}, {}
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        # GNU sha256sum: 64 hex, space, text/binary marker, then whole pathname.
        match = re.fullmatch(r"([a-f0-9]{64}) [ *](.+)", line)
        if not match:
            raise ValueError(f"unsupported snapshot manifest record: {line[:100]}")
        digest, name = match.groups()
        candidate = Path(name)
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        if root not in candidate.parents:
            raise ValueError(f"snapshot manifest path leaves snapshot: {candidate}")
        if candidate in named and named[candidate] != digest:
            raise ValueError(f"conflicting snapshot hashes: {candidate}")
        named[candidate] = digest
        grouped.setdefault(digest, []).append(candidate)
    return grouped, {"root": str(root), "manifest_path": str(source),
                     "manifest_sha256": sha256(source), "entries": len(named)}


def extract(source: Path, spec: dict) -> tuple[bytes, dict]:
    method = spec["method"]
    if method == "copy":
        if source.stat().st_size > spec["max_bytes"]:
            raise ValueError(f"source exceeds copy limit: {source}")
        return source.read_bytes(), {"method": "whole_file"}
    if method == "lines":
        with text_stream(source) as stream:
            selected = []
            for number, line in enumerate(stream, 1):
                selected.append(line)
                if number == spec["limit"]:
                    break
        return "".join(selected).encode("utf-8"), {"method": "line_ranges",
                "first_line": 1, "last_line": len(selected), "newline": "LF"}
    if method == "fastq":
        # Existing, real T1 reads only. No reads are generated or downloaded.
        selected, count = [], 0
        with text_stream(source) as stream:
            for _ in range(spec["records"]):
                header = stream.readline()
                if not header:
                    break
                record = [header] + [stream.readline() for _ in range(3)]
                if (not all(record) or not header.startswith("@") or
                        not record[2].startswith("+") or
                        len(record[1].rstrip("\n")) != len(record[3].rstrip("\n"))):
                    raise ValueError("invalid/incomplete FASTQ record in T1 source")
                selected.extend(record); count += 1
        if count != spec["records"]:
            raise ValueError("T1 reads have fewer records than requested subset")
        return "".join(selected).encode("utf-8"), {"method": "fastq_records",
                "first_record": 1, "records": count, "newline": "LF"}
    if method == "fasta":
        selected, records, bases = [], 0, 0
        with text_stream(source) as stream:
            for line in stream:
                if line.startswith(">"):
                    if records == spec["records"] or bases >= spec["max_bases"]:
                        break
                    selected.append(line); records += 1
                else:
                    if not records:
                        raise ValueError(f"sequence before FASTA header: {source}")
                    seq = line.strip()
                    remaining = spec["max_bases"] - bases
                    selected.append(seq[:remaining] + "\n")
                    bases += min(len(seq), remaining)
                    if bases >= spec["max_bases"]:
                        break
        if not records or not bases:
            raise ValueError(f"empty FASTA source: {source}")
        return "".join(selected).encode("utf-8"), {"method": "fasta_records",
                "records": records, "bases": bases, "selection": "first records/prefix; no coordinate renaming",
                "newline": "LF", "partial_last_record_possible": True}
    if method == "gtf":
        genes, prefix = set(), []
        with text_stream(source) as stream:
            for number, line in enumerate(stream, 1):
                if number <= spec["limit"]:
                    prefix.append(line)
                if line.startswith("#"):
                    continue
                fields = line.rstrip("\n").split("\t")
                if len(fields) != 9:
                    raise ValueError(f"invalid GTF row {number}: {source}")
                ids = re.findall(r'(?:^|;)\s*gene_id\s+"([^"]+)"', fields[8])
                if len(ids) != 1:
                    raise ValueError(f"cannot count gene_id at GTF row {number}: {source}")
                genes.add(ids[0])
        return "".join(prefix).encode("utf-8"), {"method": "line_ranges",
                "first_line": 1, "last_line": len(prefix), "full_source_unique_gene_ids": len(genes),
                "count_scope": "entire original GTF, all features with gene_id", "newline": "LF"}
    if method == "fasta_by_query":
        query_file = path(spec["id_source_path"])
        rows = list(csv.DictReader(io.StringIO(query_file.read_text(encoding="utf-8")), delimiter="\t"))
        requested = {r["query"] for r in rows}
        if not requested or len(requested) != len(rows):
            raise ValueError("selected functional rows must have unique query identifiers")
        found, selected = set(), []
        keep, record_id = False, None
        with text_stream(source) as stream:
            for line in stream:
                if line.startswith(">"):
                    record_id = line[1:].split()[0]
                    keep = record_id in requested
                    if keep:
                        if record_id in found:
                            raise ValueError(f"duplicate protein ID: {record_id}")
                        found.add(record_id)
                if keep:
                    selected.append(line)
        if found != requested:
            raise ValueError(f"query proteins missing: {len(requested - found)}")
        return "".join(selected).encode("utf-8"), {"method": "fasta_records",
                "query_file_sha256": sha256(query_file), "records": len(found),
                "selection": "complete FASTA records matching selected functional query column",
                "newline": "LF"}
    raise ValueError(f"unknown extraction method: {method}")


COHORTS = {"T1_arabidopsis", "T1_celegans", "T1_yeast", "T3"}


def scope_roots(config: dict, project: Path) -> dict[str, list[Path]]:
    result = {}
    for cohort, values in config["scope_roots"].items():
        if cohort not in COHORTS:
            raise ValueError(f"unsupported source cohort: {cohort}")
        result[cohort] = [Path(value.replace("{project}", str(project)).replace(
            "{home}", str(Path.home()))).expanduser().resolve() for value in values]
    if set(result) != COHORTS:
        raise ValueError("scope_roots must explicitly define the three T1 species and T3")
    return result


def check_scope(origin: Path, cohort: str, roots: dict[str, list[Path]]) -> None:
    if cohort not in COHORTS or not any(root == origin or root in origin.parents for root in roots[cohort]):
        raise ValueError(f"origin is outside declared T1/T3 cohort: {origin}")


def check_output_layout(output: Path, snapshot: Path, project: Path) -> None:
    """Allow managed bench output inside the project, never source overlap."""
    if output == snapshot or snapshot in output.parents or output in snapshot.parents:
        raise ValueError("output and source snapshot must not overlap")
    if output == project or output in project.parents:
        raise ValueError("output must not contain the project")
    managed = (project / "bench" / "bench_transfer").resolve()
    if project in output.parents and managed not in output.parents:
        raise ValueError("output inside project must be a run directory under bench/bench_transfer")


def select_t3_pair(config: dict, grouped: dict, roots: dict) -> dict:
    """Select one existing report-backed GFF/FAA pair by total compressed size."""
    report = Path(config["t3_report"].replace("{home}", str(Path.home()))).expanduser().resolve(strict=True)
    check_scope(report, "T3", roots)
    with report.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    eligible = {r["accession"]: r for r in rows if r.get("band_verdict") == "in_band"}
    requested = config.get("t3_accession")
    if requested and requested not in eligible:
        raise ValueError("selected T3 accession is not an in_band run in the existing report")
    original_roots = [r for r in roots["T3"] if r.is_dir()]
    candidates = {}
    snapshot_files = {p for paths in grouped.values() for p in paths if p.is_file()}
    for p in sorted(snapshot_files):
        match = re.match(r"^(GCF_[0-9]+\.[0-9]+)_.*(_genomic\.gff|_protein\.faa)(?:\.gz)?$", p.name)
        if not match:
            continue
        accession, suffix = match.groups()
        if accession not in eligible or (requested and requested != accession):
            continue
        origins = {q.resolve() for root in original_roots for q in root.rglob(p.name) if q.is_file()}
        if len(origins) != 1:
            continue
        origin = next(iter(origins))
        kind = "gff" if suffix == "_genomic.gff" else "faa"
        candidates.setdefault(accession, {}).setdefault(kind, []).append((p, origin))
    complete = []
    for accession, pair in candidates.items():
        if set(pair) != {"gff", "faa"}:
            continue
        selected = {}
        for kind, options in pair.items():
            # Ambiguous versions/copies must be resolved, not silently chosen.
            unique = {(str(p), str(o)): (p, o) for p, o in options}
            if len(unique) != 1:
                break
            selected[kind] = next(iter(unique.values()))
        if len(selected) == 2:
            total = sum(p.stat().st_size for p, _ in selected.values())
            complete.append((total, accession, selected))
    if not complete:
        raise ValueError("no complete report-backed T3 GFF/FAA pair in snapshot and original roots")
    total, accession, selected = min(complete, key=lambda row: (row[0], row[1]))
    return {"accession": accession, "report_row": eligible[accession],
            "report_path": str(report), "report_sha256": sha256(report), "total_source_bytes": total,
            "files": {kind: {"snapshot_path": str(p), "source_origin": str(o)}
                      for kind, (p, o) in selected.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--inventory-only", action="store_true", help="Compatibility flag; all preparation is offline and extracts existing files only")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config.get("source_scope") != "T1_T3" or config.get("spec_version") != "1.2":
        parser.error("use the 1.2 T1/T3-only preparation config")
    if "sra" in config or "busco" in config:
        parser.error("new downloads or BUSCO execution are outside current source scope")
    output = Path(config["output_root"]).expanduser().resolve()
    snapshot = Path(config["snapshot_root"]).expanduser().resolve()
    project = Path(config["project_root"]).expanduser().resolve()
    try:
        check_output_layout(output, snapshot, project)
    except ValueError as error:
        parser.error(str(error))
    bundle, work = output / "bundle", output / "work"
    bundle.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True)
    status = {"status": "blocked", "inventory_only": args.inventory_only,
              "sources": [], "gaps": [], "jobs": {}}
    write_json(bundle / "config.json", config)
    save_immutable(bundle / "scripts" / "prepare_sources.py", Path(__file__).read_bytes())
    save_immutable(bundle / "scripts" / "transfer.py", (Path(__file__).resolve().parents[1] / "transfer.py").read_bytes())
    write_json(bundle / "python_version.json", {"version": sys.version, "executable": sys.executable,
               "platform": sys.platform})
    log = bundle / "logs" / "prepare.log"; log.parent.mkdir(exist_ok=True)
    try:
        roots = scope_roots(config, project)
        grouped, snapshot_record = snapshot_index(snapshot)
        write_json(bundle / "snapshot_record.json", snapshot_record)
        save_immutable(bundle / "snapshot_manifest.txt", (snapshot / "MANIFEST.txt").read_bytes())
        inventory = [{"path": str(p), "size_bytes": p.stat().st_size}
                     for p in sorted(snapshot.rglob("*")) if p.is_file() and not p.is_symlink()]
        write_json(bundle / "inventory.json", inventory)
        try:
            t3 = select_t3_pair(config, grouped, roots)
            write_json(bundle / "t3_selection.json", t3)
        except (OSError, ValueError, KeyError) as error:
            t3 = None
            status["gaps"].append({"role": "t3_selection", "required": True, "reason": str(error)})
        for spec in config["sources"]:
            try:
                role = spec["role"]
                if not re.fullmatch(r"[a-z0-9_]+", role):
                    raise ValueError("source role must be a safe neutral identifier")
                origin_patterns = spec.get("origin_candidates", [spec.get("origin")])
                if spec.get("t3_kind"):
                    if t3 is None:
                        raise ValueError("T3 pair selection is unavailable")
                    chosen = t3["files"][spec["t3_kind"]]
                    origin_patterns = [chosen["source_origin"]]
                if not origin_patterns or any(not p for p in origin_patterns):
                    raise ValueError("origin path is not configured")
                patterns = [p.replace("{project}", str(project)).replace("{home}", str(Path.home()))
                            for p in origin_patterns]
                candidates = sorted({p for pattern in patterns for p in glob.glob(pattern)})
                if len(candidates) != 1:
                    raise ValueError(f"expected one origin file, got {len(candidates)}: {patterns}")
                origin = path(candidates[0])
                check_scope(origin, spec["cohort"], roots)
                if "expected_size_bytes" in spec and origin.stat().st_size != spec["expected_size_bytes"]:
                    raise ValueError("origin size differs from user-reported file listing")
                if spec["cohort"] == "T3" and not spec.get("t3_kind"):
                    allowed_reports = {"t3_report": "t3_batch_report.tsv", "t3_summary": "t3_batch_summary.json"}
                    if allowed_reports.get(role) != origin.name:
                        raise ValueError("T3 source must be the selected GFF/FAA pair or existing batch reports")
                digest = sha256(origin)
                if spec.get("expected_sha256") and digest != spec["expected_sha256"]:
                    raise ValueError("origin does not match pre-existing SHA binding")
                snapshot_path = chosen["snapshot_path"] if spec.get("t3_kind") else spec.get("snapshot_path")
                if snapshot_path:
                    source = path(snapshot_path)
                    if source not in grouped.get(digest, []):
                        raise ValueError("configured snapshot path is not manifest-bound to origin")
                elif spec.get("snapshot_required", True):
                    matches = sorted(set(grouped.get(digest, [])))
                    if not matches:
                        raise ValueError("no snapshot copy matches the full origin SHA")
                    source = matches[0]
                else:
                    # Existing T1 reads/report missing from snapshot: hash before/after read.
                    source = origin
                if source != origin and sha256(source) != digest:
                    raise ValueError("snapshot bytes do not match manifest/origin")
                extraction_spec = dict(spec)
                binding_receipts = {}
                if spec.get("checksum_record_role"):
                    matches = [r for r in status["sources"] if r["role"] == spec["checksum_record_role"]]
                    if len(matches) != 1:
                        raise ValueError("historical RNA-seq checksum list has not been prepared")
                    check_read_checksum(origin, digest, bundle / matches[0]["package_path"])
                    binding_receipts["checksum_record_sha256"] = matches[0]["package_sha256"]
                if spec.get("binding_record_role"):
                    matches = [r for r in status["sources"] if r["role"] == spec["binding_record_role"]]
                    if len(matches) != 1:
                        raise ValueError("T1 RNA-seq provenance has not been prepared")
                    record = json.loads((bundle / matches[0]["package_path"]).read_text(encoding="utf-8"))
                    samples = [r for r in record["samples"] if r["id"] == spec["sample_id"]]
                    if len(samples) != 1 or samples[0][spec["mate"] + "_sha256"] != digest:
                        raise ValueError("T1 read SHA does not match original RNA-seq provenance")
                    binding_receipts["provenance_sha256"] = matches[0]["package_sha256"]
                if spec.get("id_source_role"):
                    matches = [r for r in status["sources"] if r["role"] == spec["id_source_role"]]
                    if len(matches) != 1:
                        raise ValueError("required selected query table has not been prepared")
                    extraction_spec["id_source_path"] = str(bundle / matches[0]["package_path"])
                content, selection = extract(source, extraction_spec)
                if binding_receipts:
                    selection["source_bindings"] = binding_receipts
                destination = bundle / "sources" / (role + spec["extension"])
                if spec.get("t3_kind"):
                    destination = bundle / "sources" / (role + (".gff3" if spec["t3_kind"] == "gff" else ".faa")
                                                        + (".gz" if source.suffix == ".gz" else ""))
                if destination.parent != bundle / "sources" or len(content) > config["max_file_bytes"]:
                    raise ValueError("unsafe output path or extracted file exceeds limit")
                save_immutable(destination, content)
                if sha256(source) != digest or (source != origin and sha256(origin) != digest):
                    raise ValueError("origin/snapshot changed while extracting")
                status["sources"].append({"role": role, "source_path": str(source),
                    "cohort": spec["cohort"],
                    "source_origin": str(origin), "source_sha256": digest,
                    "source_size_bytes": source.stat().st_size,
                    "package_path": destination.relative_to(bundle).as_posix(),
                    "package_sha256": sha256(destination), "selection": selection,
                    "cases": spec["cases"]})
            except (OSError, ValueError, KeyError, TypeError, EOFError) as error:
                status["gaps"].append({"role": spec.get("role"), "required": spec.get("required", True), "reason": str(error)})
    except (OSError, ValueError, KeyError) as error:
        status["gaps"].append({"role": "snapshot", "required": True, "reason": str(error)})
    try:
        read_rows = {r["role"]: r for r in status["sources"]
                     if re.fullmatch(r"yeast_rep[12]_r[12]", r["role"])}
        if read_rows:
            pair_receipts = []
            for replicate in (1, 2):
                names = [f"yeast_rep{replicate}_r{mate}" for mate in (1, 2)]
                if any(name not in read_rows for name in names):
                    raise ValueError("incomplete T1 sample subset; both mates are required")
                headers = []
                for name in names:
                    lines = (bundle / read_rows[name]["package_path"]).read_text(encoding="utf-8").splitlines()
                    headers.append([re.sub(r"/[12]$", "", h.split()[0]) for h in lines[::4]])
                if headers[0] != headers[1]:
                    raise ValueError("real within-sample T1 subset identifiers do not pair")
                pair_receipts.append({"sample": f"WT_Rep{replicate}", "pairs": len(headers[0]),
                                      "roles": names})
            if len({read_rows[f"yeast_rep{rep}_r1"]["source_sha256"] for rep in (1, 2)}) != 2:
                raise ValueError("T1 two-sample source copies are identical")
            write_json(bundle / "t1_read_pairing.json", pair_receipts)
    except (OSError, ValueError, KeyError) as error:
        status["gaps"].append({"role": "T1_read_pairing", "required": True, "reason": str(error)})
    required_gaps = [g for g in status["gaps"] if g["required"]]
    status["status"] = "blocked" if required_gaps else "complete"
    write_json(bundle / "STATUS.json", status)
    log.write_bytes((json.dumps({"status": status["status"], "gaps": status["gaps"]}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    manifest(bundle)
    checked = verify(bundle)
    print(f"{status['status'].upper()}: {len(status['sources'])} sources; {len(required_gaps)} required gaps")
    print(f"Bundle: {bundle}; SHA-256 manifest: {checked['manifest_sha256']}")
    print(f"Files: {checked['verified_files']}; bytes: {checked['verified_bytes']}; jobs: {', '.join(status['jobs']) or 'none'}")
    for gap in status["gaps"]:
        print(f"GAP {gap['role']}: {gap['reason']}")
    return 2 if required_gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
