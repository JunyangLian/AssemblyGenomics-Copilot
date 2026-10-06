"""First server round: provenance checks, bounded source extraction, SRA, BUSCO.

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
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request

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


def run(command: list[str], log: Path, *, memory_gib=None, timeout=None) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    preexec = None
    if memory_gib is not None:
        import resource
        def limit_memory():
            ceiling = int(memory_gib * 1024 ** 3)
            resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
        preexec = limit_memory
    # No shell expansion, no environment/key dump, no credentials in command.
    with log.open("wb") as output:
        if memory_gib is None:
            subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=True,
                           timeout=timeout)
            return
        # A separate Linux process group lets the total job be stopped together.
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                   preexec_fn=preexec, start_new_session=True)
        started = time.monotonic()
        try:
            while process.poll() is None:
                rss = 0
                for directory in Path("/proc").iterdir():
                    if not directory.name.isdigit():
                        continue
                    try:
                        stat = (directory / "stat").read_text()
                        # After '(comm)': state, ppid, process group, ...
                        if int(stat[stat.rfind(")") + 2:].split()[2]) != process.pid:
                            continue
                        match = re.search(r"^VmRSS:\s+(\d+)\s+kB$",
                                          (directory / "status").read_text(), re.M)
                        if match:
                            rss += int(match[1]) * 1024
                    except (FileNotFoundError, ProcessLookupError, PermissionError):
                        continue
                if rss > memory_gib * 1024 ** 3:
                    raise ValueError("BUSCO process-group RSS exceeded configured memory budget")
                if timeout is not None and time.monotonic() - started > timeout:
                    raise subprocess.TimeoutExpired(command, timeout)
                time.sleep(0.25)
            if process.returncode:
                raise subprocess.CalledProcessError(process.returncode, command)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise


def version(executable: str, output: Path, option="--version") -> str:
    run([executable, option], output, timeout=30)
    return output.read_text(encoding="utf-8", errors="replace").strip()


def ena_metadata(accession: str, destination: Path) -> dict:
    if not re.fullmatch(r"(?:SRR|ERR|DRR)[0-9]+", accession):
        raise ValueError("invalid SRA run accession")
    query = urllib.parse.urlencode({"accession": accession, "result": "read_run",
        "fields": "run_accession,sample_accession,scientific_name,tax_id,library_layout,library_strategy",
        "format": "tsv"})
    url = "https://www.ebi.ac.uk/ena/portal/api/filereport?" + query
    with urllib.request.urlopen(url, timeout=20) as response:
        content = response.read(1024 * 1024)
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8")), delimiter="\t"))
    if len(rows) != 1 or rows[0]["run_accession"] != accession:
        raise ValueError(f"ENA did not return one matching run: {accession}")
    row = rows[0]
    if row["library_layout"] != "PAIRED" or not row["scientific_name"].startswith("Saccharomyces cerevisiae"):
        raise ValueError(f"not a paired S. cerevisiae run: {accession}")
    save_immutable(destination, content)
    return {**row, "metadata_url": url, "metadata_sha256": sha256(destination)}


def check_pairs(directory: Path, accession: str, maximum: int) -> dict:
    left, right = directory / f"{accession}_1.fastq", directory / f"{accession}_2.fastq"
    if not left.is_file() or not right.is_file():
        raise ValueError("SRA tool did not emit both paired files")
    count = 0
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            la, lb = a.readline(), b.readline()
            if not la and not lb:
                break
            aa, bb = [la] + [a.readline() for _ in range(3)], [lb] + [b.readline() for _ in range(3)]
            for record in (aa, bb):
                if (not all(record) or not record[0].startswith(b"@") or
                    not record[2].startswith(b"+") or
                    len(record[1].rstrip()) != len(record[3].rstrip())):
                    raise ValueError("invalid/incomplete FASTQ record")
            normalize = lambda header: re.sub(rb"/[12]$", b"", header.split()[0])
            if normalize(aa[0]) != normalize(bb[0]):
                raise ValueError("within-sample read identifiers do not match")
            count += 1
    if not 0 < count <= maximum:
        raise ValueError("unexpected subset record count")
    return {"pairs": count, "sha256": {p.name: sha256(p) for p in (left, right)}}


def prepare_sra(config: dict, bundle: Path, work: Path) -> dict:
    runs = config["runs"]
    if len(runs) != 2 or any(not r for r in runs) or runs[0] == runs[1]:
        raise ValueError("configure two confirmed, distinct SRA runs")
    count = config["spots"]
    if not isinstance(count, int) or not 0 < count <= 10000:
        raise ValueError("SRA spots must be 1..10000")
    if config.get("uploaded_subset_bundle"):
        uploaded = path(config["uploaded_subset_bundle"])
        verify(uploaded)
        upload_status = json.loads((uploaded / "STATUS.json").read_text(encoding="utf-8"))
        if upload_status["status"] != "complete":
            raise ValueError("uploaded SRA preparation was not complete")
        receipts, samples = [], []
        for accession in runs:
            source_dir = uploaded / "sra" / accession
            receipt = json.loads((source_dir / "run_record.json").read_text(encoding="utf-8"))
            checked = check_pairs(source_dir, accession, count)
            if checked != receipt["checked"] or receipt["selection"] != {"first_spot": 1, "last_spot": count}:
                raise ValueError("uploaded subset does not match requested spots or recorded hashes")
            rows = list(csv.DictReader(io.StringIO((source_dir / "metadata.tsv").read_text(encoding="utf-8")), delimiter="\t"))
            if (len(rows) != 1 or rows[0]["run_accession"] != accession or
                    rows[0]["library_layout"] != "PAIRED" or
                    not rows[0]["scientific_name"].startswith("Saccharomyces cerevisiae")):
                raise ValueError("uploaded SRA metadata has wrong identity/layout")
            samples.append(rows[0]["sample_accession"])
            for name in ("metadata.tsv", "run_record.json", f"{accession}_1.fastq", f"{accession}_2.fastq"):
                save_immutable(bundle / "sra" / accession / name, (source_dir / name).read_bytes())
            receipts.append(receipt)
        if not all(samples) or samples[0] == samples[1]:
            raise ValueError("uploaded runs must belong to different samples")
        return {"runs": receipts, "uploaded_manifest_sha256": sha256(uploaded / "MANIFEST.json")}
    metadata = []
    for accession in runs:
        destination = bundle / "sra" / accession / "metadata.tsv"
        if destination.exists():
            # Revalidate cached metadata, never assume arbitrary uploaded FASTQ is genuine.
            row = list(csv.DictReader(io.StringIO(destination.read_text(encoding="utf-8")), delimiter="\t"))
            if len(row) != 1 or row[0]["run_accession"] != accession:
                raise ValueError("invalid cached SRA metadata")
            if not row[0]["scientific_name"].startswith("Saccharomyces cerevisiae") or row[0]["library_layout"] != "PAIRED":
                raise ValueError("cached metadata has wrong species/layout")
            metadata.append(row[0])
        else:
            try:
                metadata.append(ena_metadata(accession, destination))
            except (OSError, ValueError) as error:
                raise ValueError(f"SRA external access/identity check unavailable; download locally then upload "
                                 f"a verified subset bundle: {error}") from error
    if not all(m.get("sample_accession") for m in metadata) or metadata[0]["sample_accession"] == metadata[1]["sample_accession"]:
        raise ValueError("two runs must belong to different public samples")
    tool = config["fastq_dump"]
    tool_version = version(tool, bundle / "logs" / "fastq_dump_version.log")
    run([tool, "--help"], bundle / "logs" / "fastq_dump_help.log", timeout=30)
    help_text = (bundle / "logs" / "fastq_dump_help.log").read_text(encoding="utf-8", errors="replace")
    if "--minSpotId" not in help_text or "--maxSpotId" not in help_text:
        raise ValueError("installed fastq-dump lacks ranged extraction; do not download full runs")
    results = []
    for accession, meta in zip(runs, metadata):
        target = work / "sra" / accession
        target.mkdir(parents=True, exist_ok=True)
        command = [tool, "--minSpotId", "1", "--maxSpotId", str(count),
                   "--split-files", "--skip-technical", "--outdir", str(target), accession]
        receipt_path = target / "completed.json"
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt["command"] != command or receipt["tool_version"] != tool_version:
                raise ValueError("SRA cache configuration changed; choose a new output directory")
            if any(receipt["metadata"].get(key) != meta.get(key) for key in
                   ("run_accession", "sample_accession", "scientific_name", "library_layout")):
                raise ValueError("cached SRA metadata differs from completed run record")
            checked = check_pairs(target, accession, count)
            if checked != receipt["checked"]:
                raise ValueError("SRA cached subset changed")
        else:
            if any(target.glob("*.fastq")):
                raise ValueError("incomplete SRA attempt exists; choose a new fixed output directory")
            # Limited spot extraction; tool may still use remote cache. No full prefetch.
            run(command, bundle / "logs" / f"{accession}.log", timeout=config["timeout_seconds"])
            checked = check_pairs(target, accession, count)
            receipt = {"command": command, "tool_version": tool_version, "checked": checked,
                       "metadata": meta, "selection": {"first_spot": 1, "last_spot": count}}
            write_json(receipt_path, receipt)
        for source in sorted(target.glob("*.fastq")):
            save_immutable(bundle / "sra" / accession / source.name, source.read_bytes())
        save_immutable(bundle / "sra" / accession / "run_record.json", receipt_path.read_bytes())
        results.append(receipt)
    return {"runs": results}


def prepare_busco(config: dict, bundle: Path, work: Path) -> dict:
    protein, lineage = path(config["protein_fasta"]), path(config["lineage"])
    if not config["publication"] or not config["protein_set_description"]:
        raise ValueError("configure published protein set identity/citation and isoform policy")
    cpu, memory = config["cpu"], config["memory_gib"]
    if not isinstance(cpu, int) or isinstance(cpu, bool) or not 0 < cpu <= (os.cpu_count() or 1):
        raise ValueError("configure explicit safe BUSCO CPU budget")
    if not isinstance(memory, (int, float)) or isinstance(memory, bool) or memory <= 0:
        raise ValueError("configure explicit BUSCO memory budget in GiB")
    if not lineage.is_dir() or not (lineage / "dataset.cfg").is_file():
        raise ValueError("BUSCO lineage must be a complete local dataset directory")
    lineage_rows = [{"path": n, "sha256": sha256(p), "size_bytes": p.stat().st_size}
                    for n, p in files(lineage).items()]
    write_json(bundle / "busco" / "lineage_manifest.json", lineage_rows)
    tool = config["executable"]
    versions = {"busco": version(tool, bundle / "logs" / "busco_version.log"),
                "hmmsearch": version(config["hmmsearch"], bundle / "logs" / "hmmsearch_version.log", "-h")}
    run([tool, "--help"], bundle / "logs" / "busco_help.log", timeout=30)
    help_text = (bundle / "logs" / "busco_help.log").read_text(encoding="utf-8", errors="replace")
    command = [tool, "-i", str(protein), "-m", "proteins", "-l", str(lineage),
               "-c", str(cpu), "--offline", "-o", "protein_qc", "--out_path", str(work / "busco")]
    if "--opt-out-run-stats" in help_text:
        command.append("--opt-out-run-stats")
    else:
        release = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", versions["busco"])
        if not release or tuple(map(int, release.groups())) >= (5, 6, 0):
            raise ValueError("BUSCO version cannot disable telemetry; select a supported version")
        # BUSCO introduced run-stat collection in 5.6.0; older releases have no flag.
    identity = {"command": command, "input_sha256": sha256(protein), "versions": versions,
                "lineage_manifest_sha256": sha256(bundle / "busco" / "lineage_manifest.json"),
                "memory_gib": memory, "publication": config["publication"],
                "memory_control": "per-process RLIMIT_AS plus 0.25s sampled process-group RSS guard",
                "protein_set_description": config["protein_set_description"]}
    receipt_path = work / "busco" / "completed.json"
    result = work / "busco" / "protein_qc"
    if receipt_path.exists():
        old = json.loads(receipt_path.read_text(encoding="utf-8"))
        if old["identity"] != identity:
            raise ValueError("BUSCO cache configuration changed; choose a new output directory")
    else:
        if result.exists():
            raise ValueError("incomplete BUSCO attempt exists; choose a new fixed output directory")
        result.parent.mkdir(parents=True, exist_ok=True)
        run(command, bundle / "logs" / "busco_run.log", memory_gib=memory)
    selected = {n: p for n, p in files(result).items()
                if (p.name.startswith("short_summary") or p.name in {"full_table.tsv", "missing_busco_list.tsv", "busco.log"})}
    if not any(n.endswith(".txt") and "short_summary" in n for n in selected) or not any(n.endswith("full_table.tsv") for n in selected):
        raise ValueError("BUSCO did not produce summary and full table")
    hashes = {n: sha256(p) for n, p in selected.items()}
    if receipt_path.exists() and old["output_sha256"] != hashes:
        raise ValueError("BUSCO cached result changed")
    if sha256(protein) != identity["input_sha256"] or any(sha256(lineage / r["path"]) != r["sha256"] for r in lineage_rows):
        raise ValueError("BUSCO input or lineage changed during run")
    receipt = {"runner": "user", "identity": identity, "output_sha256": hashes,
               "protein_path": str(protein), "lineage_path": str(lineage)}
    write_json(receipt_path, receipt)
    for name, source in selected.items():
        save_immutable(bundle / "busco" / "results" / name, source.read_bytes())
    save_immutable(bundle / "busco" / "run_record.json", receipt_path.read_bytes())
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--inventory-only", action="store_true", help="No SRA download or BUSCO execution")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output = Path(config["output_root"]).expanduser().resolve()
    snapshot = Path(config["snapshot_root"]).expanduser().resolve()
    project = Path(config["project_root"]).expanduser().resolve()
    if output == snapshot or output == project or snapshot in output.parents or project in output.parents:
        parser.error("output must be separate from snapshot and project")
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
        grouped, snapshot_record = snapshot_index(snapshot)
        write_json(bundle / "snapshot_record.json", snapshot_record)
        save_immutable(bundle / "snapshot_manifest.txt", (snapshot / "MANIFEST.txt").read_bytes())
        inventory = [{"path": str(p), "size_bytes": p.stat().st_size}
                     for p in sorted(snapshot.rglob("*")) if p.is_file() and not p.is_symlink()]
        write_json(bundle / "inventory.json", inventory)
        for spec in config["sources"]:
            try:
                role = spec["role"]
                if not re.fullmatch(r"[a-z0-9_]+", role):
                    raise ValueError("source role must be a safe neutral identifier")
                origin_pattern = spec["origin"]
                if not origin_pattern:
                    raise ValueError("origin path is not configured")
                origin_pattern = origin_pattern.replace("{project}", str(project)).replace("{home}", str(Path.home()))
                candidates = sorted(glob.glob(origin_pattern))
                if len(candidates) != 1:
                    raise ValueError(f"expected one origin file, got {len(candidates)}: {origin_pattern}")
                origin = path(candidates[0]); digest = sha256(origin)
                if spec.get("expected_sha256") and digest != spec["expected_sha256"]:
                    raise ValueError("origin does not match pre-existing SHA binding")
                snapshot_path = spec.get("snapshot_path")
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
                    # Newly identified scaffolding files: hash before/after read.
                    source = origin
                if sha256(source) != digest:
                    raise ValueError("snapshot bytes do not match manifest/origin")
                extraction_spec = dict(spec)
                if spec.get("id_source_role"):
                    matches = [r for r in status["sources"] if r["role"] == spec["id_source_role"]]
                    if len(matches) != 1:
                        raise ValueError("required selected query table has not been prepared")
                    extraction_spec["id_source_path"] = str(bundle / matches[0]["package_path"])
                content, selection = extract(source, extraction_spec)
                destination = bundle / "sources" / (role + spec["extension"])
                if destination.parent != bundle / "sources" or len(content) > config["max_file_bytes"]:
                    raise ValueError("unsafe output path or extracted file exceeds limit")
                save_immutable(destination, content)
                if sha256(source) != digest or sha256(origin) != digest:
                    raise ValueError("origin/snapshot changed while extracting")
                status["sources"].append({"role": role, "source_path": str(source),
                    "source_origin": str(origin), "source_sha256": digest,
                    "source_size_bytes": source.stat().st_size,
                    "package_path": destination.relative_to(bundle).as_posix(),
                    "package_sha256": sha256(destination), "selection": selection,
                    "cases": spec["cases"]})
            except (OSError, ValueError, KeyError, TypeError) as error:
                status["gaps"].append({"role": spec.get("role"), "required": spec.get("required", True), "reason": str(error)})
    except (OSError, ValueError, KeyError) as error:
        status["gaps"].append({"role": "snapshot", "required": True, "reason": str(error)})
    if not args.inventory_only:
        for name, job in (("sra", prepare_sra), ("busco", prepare_busco)):
            try:
                status["jobs"][name] = job(config[name], bundle, work)
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
                status["gaps"].append({"role": name, "required": True, "reason": str(error)})
    else:
        status["gaps"].append({"role": "execution", "required": True, "reason": "inventory only; SRA/BUSCO not executed"})
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
