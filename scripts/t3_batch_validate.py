#!/usr/bin/env python3
"""T3 批量规则验证：一批 RefSeq 参考 GFF+Protein 的统计与基线带核验。

目的（roadmap T3）：基线规则**特异性**——正常 RefSeq 注释应落在类群带内；
参考注释越带说明带子要修（校准发现），不是数据错了。

输入布局两种都支持：扁平目录（GCF_*_genomic.gff.gz / GCF_*_protein.faa.gz，
如服务器 ~/临时）或按物种子目录组织。按 GCF accession 前缀分组，文件名
"(1)" 副本自动归并并告警。

并行：--jobs N 按物种并行；每物种一次 GFF 流式扫描 + 一次 FAA 流式扫描，
统计与带核验在任务内融合。

输出：t3_batch_report.tsv（逐物种判定表）+ t3_batch_summary.json（类群群体分布，
为 knowledge/baselines/ 新类群带提供群体证据）。

诚实约束：类群没有注册带的指标如实报 no_band，不猜（D-016）；参考 GFF 含
ncRNA 基因是正常的（与 PIT-005 的流程产物语境不同），单独列列不判罚。
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from check_baselines import load_registry
except Exception as _exc:  # pragma: no cover
    load_registry = None
    _IMPORT_WARN = f"check_baselines 不可用（{_exc}）——全部判 no_band"
else:
    _IMPORT_WARN = None

# GCF accession 前缀 → (物种, 类群)。来源：scripts/t3_download.sh + 校准报告 2026-09-24
SPECIES_MAP = {
    "GCF_052040795.2": ("Danio_rerio", "actinopterygii"),
    "GCF_965601325.2": ("Salmo_salar", "actinopterygii"),
    "GCF_059516105.1": ("Syngnathus_floridae", "actinopterygii"),
    "GCF_964197995.2": ("Scardinius_erythrophthalmus", "actinopterygii"),
    "GCF_960531495.2": ("Zeus_faber", "actinopterygii"),
    "GCF_000309985.3": ("Brassica_rapa", "viridiplantae"),
    "GCF_000188115.4": ("Solanum_lycopersicum", "viridiplantae"),
    "GCF_002870075.5": ("Lactuca_sativa", "viridiplantae"),
    "GCF_053813885.1": ("Theobroma_cacao", "viridiplantae"),
    "GCF_054855325.1": ("Carica_papaya", "viridiplantae"),
    "GCF_000001735.4": ("Arabidopsis_thaliana", "viridiplantae"),
    "GCF_045282275.1": ("Nakaseomyces_bracarensis", "fungi"),
    "GCF_037102585.1": ("Saccharomycopsis_crataegensis", "fungi"),
    "GCF_036370985.1": ("Arxiozyma_heterogenica", "fungi"),
    "GCF_947243775.1": ("Saccharomyces_kudriavzevii", "fungi"),
    "GCF_010111755.1": ("Nakaseomyces_glabratus", "fungi"),
    "GCF_010183535.1": ("Caenorhabditis_remanei", "nematoda"),
    "GCF_000002995.4": ("Brugia_malayi", "nematoda"),
    "GCF_000004555.2": ("Caenorhabditis_briggsae", "nematoda"),
    "GCF_001040885.1": ("Strongyloides_ratti", "nematoda"),
    "GCF_000181795.1": ("Trichinella_spiralis", "nematoda"),
    "GCF_000002985.6": ("Caenorhabditis_elegans", "nematoda"),
    "GCF_000001215.4": ("Drosophila_melanogaster", "insecta"),
    "GCF_943734735.2": ("Anopheles_gambiae", "insecta"),
    "GCF_016699485.2": ("Gallus_gallus", "aves"),
    "GCF_004115215.2": ("Ornithorhynchus_anatinus", "mammalia"),
    "GCF_027887165.2": ("Monodelphis_domestica", "mammalia"),
}

AMBIGUOUS = set("XBZJUO")


def _attrs(field: str) -> dict:
    out = {}
    for item in field.rstrip(";").split(";"):
        if "=" in item:
            k, _, v = item.partition("=")
            out[k] = v
    return out


def parse_gff(path: Path) -> dict:
    """一次流式扫描：基因座、编码/非编码基因、CDS/exon 数、异构体比。"""
    types: dict[str, int] = {}
    gene_ids: set[str] = set()
    tx2gene: dict[str, str] = {}
    genes_with_cds: set[str] = set()
    op = gzip.open if path.suffix == ".gz" else open
    with op(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 9:
                continue
            kind = f[2]
            types[kind] = types.get(kind, 0) + 1
            a = _attrs(f[8])
            fid, parents = a.get("ID", ""), a.get("Parent", "")
            if kind == "gene":
                if fid:
                    gene_ids.add(fid)
            elif kind in ("mRNA", "transcript"):
                g = parents.split(",")[0] if parents else ""
                if fid:
                    tx2gene[fid] = g
                else:  # 无 ID 的转录本行：Parent 即基因（GTF 习惯）
                    if g:
                        gene_ids.add(g)
            elif kind == "CDS":
                for p in parents.split(","):
                    if p in tx2gene:
                        genes_with_cds.add(tx2gene[p])
    coding = len(genes_with_cds)
    tx = types.get("mRNA", 0) + types.get("transcript", 0)
    return {
        "gff_gene_loci": len(gene_ids),
        "coding_genes": coding,
        "noncoding_genes": max(len(gene_ids) - coding, 0),
        "cds_features": types.get("CDS", 0),
        "exon_features": types.get("exon", 0),
        "isoforms_per_gene": round(tx / coding, 3) if coding else None,
    }


def parse_faa(path: Path) -> dict:
    op = gzip.open if path.suffix == ".gz" else open
    lengths: list[int] = []
    internal_stops = dup = ambiguous = 0
    seen: set[str] = set()
    cur_len = 0
    with op(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith(">"):
                hid = line[1:].split()[0] if len(line[1:].split()) else ""
                if hid in seen:
                    dup += 1
                seen.add(hid)
                if cur_len:
                    lengths.append(cur_len)
                cur_len = 0
            else:
                cur_len += len(line.strip())
                ambiguous += sum(1 for ch in line.strip() if ch in AMBIGUOUS)
    if cur_len:
        lengths.append(cur_len)
    # 内部终止符：序列内 *（此处按整条统计含末端 1 个的差值近似）
    return {
        "proteins": len(lengths),
        "protein_median_len": int(statistics.median(lengths)) if lengths else None,
        "ambiguous_residues": ambiguous,
        "duplicate_ids": dup,
        "internal_stops": internal_stops,
    }


def count_internal_stops(path: Path) -> int:
    op = gzip.open if path.suffix == ".gz" else open
    n = 0
    buf: list[str] = []
    with op(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith(">"):
                seq = "".join(buf)
                n += max(seq.count("*") - (1 if seq.endswith("*") else 0), 0)
                buf = []
            else:
                buf.append(line.strip())
        seq = "".join(buf)
        n += max(seq.count("*") - (1 if seq.endswith("*") else 0), 0)
    return n


def band_for(registry: list[dict] | None, clade: str, metric: str):
    if not registry:
        return None
    for entry in registry:
        if entry.get("metric") == metric and entry.get("taxon_scope") == clade:
            return entry.get("expected_range")
    return None


def process_group(task: tuple) -> dict:
    accession, files = task
    name, clade = SPECIES_MAP.get(accession, (accession, "unknown"))
    gff = files.get("gff")
    faa = files.get("faa")
    row: dict = {"accession": accession, "species": name, "clade": clade}
    row.update({k: None for k in ("gff_gene_loci", "coding_genes", "noncoding_genes",
                                  "cds_features", "exon_features", "isoforms_per_gene")})
    row.update({k: None for k in ("proteins", "protein_median_len",
                                  "ambiguous_residues", "duplicate_ids", "internal_stops")})
    if gff:
        row.update(parse_gff(gff))
    if faa:
        row.update(parse_faa(faa))
        row["internal_stops"] = count_internal_stops(faa)
    value = row.get("coding_genes")
    rng = band_for(BANDS, clade, "protein_coding_gene_count")
    row["band_range"] = str(rng) if rng else None
    if value is None or rng is None:
        row["band_verdict"] = "no_band" if rng is None else "no_data"
    else:
        row["band_verdict"] = "in_band" if rng[0] <= value <= rng[1] else "out_of_band"
    return row


REPORT_COLS = ["species", "clade", "accession", "gff_gene_loci", "coding_genes",
               "noncoding_genes", "cds_features", "exon_features", "isoforms_per_gene",
               "proteins", "protein_median_len", "internal_stops", "ambiguous_residues",
               "duplicate_ids", "band_range", "band_verdict"]


def main() -> int:
    global BANDS
    ap = argparse.ArgumentParser(description="T3 批量：RefSeq 参考 GFF+FAA 统计与基线带核验")
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default=None, help="报告输出目录（默认 root）")
    ap.add_argument("--jobs", type=int, default=1)
    args = ap.parse_args()

    try:
        BANDS = load_registry() if load_registry else None
    except Exception as exc:
        print(f"[警告] 基线注册表加载失败（{exc}）——全部判 no_band")
        BANDS = None
    if _IMPORT_WARN:
        print(f"[警告] {_IMPORT_WARN}")
    root = Path(args.root)
    out_dir = Path(args.out) if args.out else root

    groups: dict[str, dict] = {}
    dup_warns = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        stem = p.name
        if " (" in stem:  # "(1)" 副本
            dup_warns.append(p.name)
        kind = None
        if "_genomic.gff" in stem:
            kind = "gff"
        elif "_protein.faa" in stem:
            kind = "faa"
        if not kind:
            continue
        base = stem.split("_genomic.gff")[0].split("_protein.faa")[0].replace(" (1)", "")
        acc = "_".join(base.split("_")[:2]) if base.startswith("GCF_") else base
        groups.setdefault(acc, {})[kind] = p

    if dup_warns:
        print(f"[提示] 忽略文件名 (1) 副本归并：{dup_warns}")
    unknown = [a for a in groups if a not in SPECIES_MAP]
    if unknown:
        print(f"[提示] 未登记 accession（仍会统计，clade=unknown）：{unknown}")

    tasks = [(a, f) for a, f in sorted(groups.items())]
    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            rows = list(ex.map(process_group, tasks))
    else:
        rows = [process_group(t) for t in tasks]

    tsv = out_dir / "t3_batch_report.tsv"
    with tsv.open("w", encoding="utf-8") as fo:
        fo.write("\t".join(REPORT_COLS) + "\n")
        for r in rows:
            fo.write("\t".join(str(r.get(c)) for c in REPORT_COLS) + "\n")

    clades: dict[str, list[dict]] = {}
    for r in rows:
        clades.setdefault(r["clade"], []).append(r)
    summary = {"n_species": len(rows), "clades": {}}
    for clade, rs in sorted(clades.items()):
        vals = [r["coding_genes"] for r in rs if r.get("coding_genes")]
        mids = [r["protein_median_len"] for r in rs if r.get("protein_median_len")]
        verdicts = [r["band_verdict"] for r in rs]
        summary["clades"][clade] = {
            "n": len(rs),
            "coding_genes": {"min": min(vals), "median": int(statistics.median(vals)),
                             "max": max(vals)} if vals else None,
            "protein_median_len": {"min": min(mids), "max": max(mids)} if mids else None,
            "band_verdicts": {v: verdicts.count(v) for v in sorted(set(verdicts))},
        }
    (out_dir / "t3_batch_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[完成] {len(rows)} 物种 → {tsv}")
    for clade, s in summary["clades"].items():
        v = s["band_verdicts"]
        print(f"  {clade:15s} n={s['n']:2d}  带判定 {v}")
    out_of = [r["species"] for r in rows if r.get("band_verdict") == "out_of_band"]
    if out_of:
        print(f"[校准信号] 参考注释越带（带子需修，非数据错）：{out_of}")
    return 0


BANDS = None

if __name__ == "__main__":
    sys.exit(main())
