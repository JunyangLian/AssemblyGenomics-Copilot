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

BENCH_ROOT = Path(__file__).resolve().parents[1]
if not (BENCH_ROOT / "transfer.py").is_file():
    print(f"Missing required file: {BENCH_ROOT / 'transfer.py'}. "
          "Upload local bench/transfer.py to the server bench/ directory "
          "(one level above server/), then rerun.", file=sys.stderr)
    raise SystemExit(2)
sys.path.insert(0, str(BENCH_ROOT))
from transfer import manifest, sha256, verify, write_json


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
        named.setdefault(candidate, set()).add(digest)
    conflicts = []
    for candidate, digests in sorted(named.items()):
        if len(digests) > 1:
            conflicts.append({"path": str(candidate), "recorded_sha256": sorted(digests),
                              "resolution": "excluded_from_source_matching"})
        else:
            grouped.setdefault(next(iter(digests)), []).append(candidate)
    return grouped, {"root": str(root), "manifest_path": str(source),
                     "manifest_sha256": sha256(source), "entries": len(named),
                     "excluded_conflicts": conflicts}


def feature_gene_id(fields: list[str]) -> tuple[str | None, str | None]:
    """Read explicit IDs, including Augustus/TSEBRA bare gene feature IDs."""
    attributes = fields[8].strip()
    ids = re.findall(r'(?:^|;)\s*gene_id(?:\s*=\s*|\s+)(?:"([^"]+)"|([^;\s"]+))', attributes)
    if len(ids) > 1:
        raise ValueError("repeated gene_id attribute")
    if ids:
        quoted, unquoted = ids[0]
        return quoted or unquoted, "gene_id_attribute"
    if fields[2] == "gene":
        ids = re.findall(r'(?:^|;)\s*ID=([^;\s]+)', attributes)
        if len(ids) > 1:
            raise ValueError("repeated gene feature ID")
        if ids:
            return ids[0], "gene_feature_ID"
        if attributes != "." and re.fullmatch(r'[^;\s=\"]+;?', attributes):
            return attributes.rstrip(";"), "bare_gene_feature_ID"
        raise ValueError(f"gene feature has no explicit identifier: {attributes[:160]}")
    return None, None


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
        genes, prefix, formats = set(), [], set()
        gene_records, rows_without_gene_id = 0, 0
        with text_stream(source) as stream:
            for number, line in enumerate(stream, 1):
                if number <= spec["limit"]:
                    prefix.append(line)
                if line.startswith("#") or not line.strip():
                    continue
                fields = line.rstrip("\n").split("\t")
                if len(fields) != 9:
                    raise ValueError(f"invalid GTF row {number}: {source}")
                try:
                    identifier, format_name = feature_gene_id(fields)
                except ValueError as error:
                    raise ValueError(f"GTF row {number}: {error}: {source}") from error
                gene_records += fields[2] == "gene"
                if identifier:
                    genes.add(identifier); formats.add(format_name)
                else:
                    rows_without_gene_id += 1
        if not genes:
            raise ValueError(f"no explicit gene identifiers in original GTF: {source}")
        return "".join(prefix).encode("utf-8"), {"method": "line_ranges",
                "first_line": 1, "last_line": len(prefix), "full_source_unique_gene_ids": len(genes),
                "count_scope": "entire original GTF, explicit gene feature IDs and gene_id attributes",
                "gene_id_formats": sorted(formats), "gene_feature_records": gene_records,
                "rows_without_gene_id": rows_without_gene_id, "newline": "LF"}
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


def select_t3_pair(config: dict, grouped: dict, roots: dict, diagnostics: dict | None = None) -> dict:
    """Locate an existing report-backed pair in T3 roots, independent of snapshots."""
    if diagnostics is None:
        diagnostics = {}
    report = Path(config["t3_report"].replace("{home}", str(Path.home())).replace(
        "{project}", str(Path(config["project_root"]).expanduser().resolve()))).expanduser().resolve(strict=True)
    check_scope(report, "T3", roots)
    with report.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        diagnostics["report_columns"] = reader.fieldnames
        rows = list(reader)
    eligible = {r["accession"]: r for r in rows if r.get("band_verdict") == "in_band"}
    diagnostics.update(report_path=str(report), eligible_accessions=sorted(eligible),
                       roots=[{"path": str(r), "exists": r.is_dir()} for r in roots["T3"]],
                       candidate_files=[], skipped_pairs=[])
    requested = config.get("t3_accession")
    if requested and requested not in eligible:
        raise ValueError("selected T3 accession is not an in_band run in the existing report")
    candidates = {}
    discovered = {p.resolve() for root in roots["T3"] if root.is_dir()
                  for p in root.rglob("*") if p.is_file() and
                  re.search(r"\.(?:gff3?|faa)(?:\.gz)?$", p.name)}
    for origin in sorted(discovered):
        check_scope(origin, "T3", roots)
        kind = "faa" if re.search(r"\.faa(?:\.gz)?$", origin.name) else "gff"
        # RefSeq accession in filename or species directory; never infer species from size.
        identity = next((match.group(1) for part in (origin.name, *[p.name for p in origin.parents])
                         if (match := re.match(r"^(GCF_[0-9]+\.[0-9]+)(?:_|\.|$)", part))), None)
        diagnostics["candidate_files"].append({"path": str(origin), "kind": kind,
            "accession": identity, "report_eligible": identity in eligible,
            "size_bytes": origin.stat().st_size})
        if identity not in eligible or (requested and requested != identity):
            continue
        candidates.setdefault(identity, {}).setdefault(kind, []).append(origin)
    complete = []
    for accession, pair in sorted(candidates.items()):
        if set(pair) != {"gff", "faa"}:
            diagnostics["skipped_pairs"].append({"accession": accession, "reason": "missing mate",
                "present_kinds": sorted(pair)})
            continue
        if any(len(options) != 1 for options in pair.values()):
            diagnostics["skipped_pairs"].append({"accession": accession, "reason": "ambiguous file paths",
                "paths": {kind: [str(p) for p in options] for kind, options in pair.items()}})
            continue
        selected = {kind: options[0] for kind, options in pair.items()}
        total = sum(p.stat().st_size for p in selected.values())
        complete.append((total, accession, selected))
    if not complete:
        raise ValueError(f"no unique report-backed T3 GFF/FAA pair in declared roots "
                         f"({len(eligible)} eligible accessions; {len(discovered)} annotation files); "
                         "see t3_locations.json for paths")
    total, accession, selected = min(complete, key=lambda row: (row[0], row[1]))
    diagnostics["selected_accession"] = accession
    return {"accession": accession, "report_row": eligible[accession],
            "report_path": str(report), "report_sha256": sha256(report), "total_source_bytes": total,
            "selection_policy": "smallest existing report-backed original pair; accession tie-break",
            "files": {kind: {"snapshot_path": None, "source_origin": str(origin)}
                      for kind, origin in selected.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", type=Path,
                        help="Use a new fixed run directory without changing the saved config")
    parser.add_argument("--inventory-only", action="store_true", help="Compatibility flag; all preparation is offline and extracts existing files only")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.output_root is not None:
        config["output_root"] = str(args.output_root)
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
        t3_locations = {}
        try:
            t3 = select_t3_pair(config, grouped, roots, t3_locations)
            write_json(bundle / "t3_selection.json", t3)
        except (OSError, ValueError, KeyError) as error:
            t3 = None
            status["gaps"].append({"role": "t3_selection", "required": True, "reason": str(error)})
        write_json(bundle / "t3_locations.json", t3_locations)
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
                matched_snapshot = None
                if snapshot_path:
                    matched_snapshot = path(snapshot_path)
                    if matched_snapshot not in grouped.get(digest, []):
                        raise ValueError("configured snapshot path is not manifest-bound to origin")
                else:
                    matches = sorted(set(grouped.get(digest, [])))
                    if matches:
                        matched_snapshot = matches[0]
                # User confirms stable originals. Extract there and record SHA once;
                # historical snapshot bookkeeping is not a global integrity gate.
                source = origin
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
                selection["source_hash_policy"] = "original_recorded_once"
                if binding_receipts:
                    selection["source_bindings"] = binding_receipts
                destination = bundle / "sources" / (role + spec["extension"])
                if spec.get("t3_kind"):
                    destination = bundle / "sources" / (role + (".gff3" if spec["t3_kind"] == "gff" else ".faa")
                                                        + (".gz" if source.suffix == ".gz" else ""))
                if destination.parent != bundle / "sources" or len(content) > config["max_file_bytes"]:
                    raise ValueError("unsafe output path or extracted file exceeds limit")
                save_immutable(destination, content)
                status["sources"].append({"role": role, "source_path": str(source),
                    "manifest_matched_snapshot_path": str(matched_snapshot) if matched_snapshot else None,
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
        label = "GAP" if gap["required"] else "OPTIONAL"
        print(f"{label} {gap['role']}: {gap['reason']}")
    if "snapshot_record" in locals() and snapshot_record["excluded_conflicts"]:
        print(f"NOTE: {len(snapshot_record['excluded_conflicts'])} ambiguous historical snapshot paths "
              "excluded; recorded in snapshot_record.json")
    return 2 if required_gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
