"""t3_batch_validate 测试：合成 mini GFF/FAA，验证统计、分组、带核验与并行融合语义。"""
from __future__ import annotations

import gzip
import json

import scripts.t3_batch_validate as tb


GFF = """##gff-version 3
##sequence-region chr1 1 1000
chr1\tn\tgene\t1\t900\t.\t+\t.\tID=g1;Name=g1
chr1\tn\tmRNA\t1\t900\t.\t+\t.\tID=t1;Parent=g1
chr1\tn\texon\t1\t400\t.\t+\t.\tParent=t1
chr1\tn\tCDS\t1\t400\t.\t+\t.\tParent=t1
chr1\tn\tmRNA\t500\t900\t.\t+\t.\tID=t2;Parent=g1
chr1\tn\tCDS\t500\t900\t.\t+\t.\tParent=t2
chr1\tn\tgene\t100\t500\t.\t-\t.\tID=g2
chr1\tn\tmRNA\t100\t500\t.\t-\t.\tID=t3;Parent=g2
chr1\tn\tCDS\t100\t500\t.\t-\t.\tParent=t3
chr1\tn\tgene\t2000\t2500\t.\t+\t.\tID=g3
chr1\tn\tncRNA\t2000\t2500\t.\t+\t.\tID=n1;Parent=g3
"""


def _make(tmp_path):
    gff = tmp_path / "GCF_000001735.4_TAIR10.1_genomic.gff.gz"
    with gzip.open(gff, "wt", encoding="utf-8") as f:
        f.write(GFF)
    faa = tmp_path / "GCF_000001735.4_TAIR10.1_protein.faa.gz"
    with gzip.open(faa, "wt", encoding="utf-8") as f:
        f.write(">p1 desc\nMKVL\n>p2 desc\nMK*R\n>p3 desc\nMKXZ\n>p1 dup\nAAAA\n")
    return tmp_path


def test_parse_gff_counts(tmp_path):
    gff = tmp_path / "a.gff.gz"
    with gzip.open(gff, "wt", encoding="utf-8") as f:
        f.write(GFF)
    s = tb.parse_gff(gff)
    assert s["gff_gene_loci"] == 3
    assert s["coding_genes"] == 2          # g3 只有 ncRNA 子特征
    assert s["noncoding_genes"] == 1
    assert s["cds_features"] == 3
    assert s["isoforms_per_gene"] == 1.5   # 3 transcript / 2 coding


def test_parse_faa_and_stops(tmp_path):
    faa = tmp_path / "a.faa.gz"
    with gzip.open(faa, "wt", encoding="utf-8") as f:
        f.write(">p1 desc\nMKVL\n>p2 desc\nMK*R\n>p3 desc\nMKXZ\n>p1 dup\nAAAA\n")
    s = tb.parse_faa(faa)
    assert s["proteins"] == 4
    assert s["duplicate_ids"] == 1
    assert s["ambiguous_residues"] == 2    # X、Z
    assert s["protein_median_len"] == 4
    assert tb.count_internal_stops(faa) == 1  # p2 的内部 *


def test_process_group_verdict(tmp_path):
    root = _make(tmp_path)
    files = {"gff": root / "GCF_000001735.4_TAIR10.1_genomic.gff.gz",
             "faa": root / "GCF_000001735.4_TAIR10.1_protein.faa.gz"}
    acc = "GCF_000001735.4"
    assert acc in tb.SPECIES_MAP
    tb.BANDS = None  # 无注册带 → 诚实 no_band
    row = tb.process_group((acc, files))
    assert row["species"] == "Arabidopsis_thaliana"
    assert row["coding_genes"] == 2
    assert row["band_verdict"] == "no_band"

    tb.BANDS = [{"metric": "protein_coding_gene_count", "taxon_scope": "viridiplantae",
                 "expected_range": [1, 100]}]
    assert tb.process_group((acc, files))["band_verdict"] == "in_band"
    tb.BANDS = [{"metric": "protein_coding_gene_count", "taxon_scope": "viridiplantae",
                 "expected_range": [50000, 90000]}]
    assert tb.process_group((acc, files))["band_verdict"] == "out_of_band"


def test_main_end_to_end(tmp_path, capsys):
    root = _make(tmp_path)
    rc = tb.main.__wrapped__ if hasattr(tb.main, "__wrapped__") else None
    import sys
    old = sys.argv
    sys.argv = ["t3_batch_validate.py", "--root", str(root)]
    try:
        assert tb.main() == 0
    finally:
        sys.argv = old
    report = (root / "t3_batch_report.tsv").read_text(encoding="utf-8").strip().split("\n")
    assert len(report) == 2  # 表头 + 1 物种
    summary = json.loads((root / "t3_batch_summary.json").read_text(encoding="utf-8"))
    assert summary["n_species"] == 1
    assert summary["clades"]["viridiplantae"]["n"] == 1


def test_builtin_bands_cover_all_clades():
    """独立部署（无 yaml 注册表）时，内置快照必须覆盖所有物种类群。"""
    for clade in set(tb.SPECIES_MAP.values()):
        for metric in ("protein_coding_gene_count", "median_protein_length"):
            assert (clade, metric) in tb.BUILTIN_BANDS, (clade, metric)
