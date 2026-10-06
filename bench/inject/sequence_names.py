"""Align excerpts first, then change only GFF sequence identifiers."""
from .common import Artifact, complete_gene_blocks, fasta_records, fasta_bytes, json_bytes


def build(src):
    ident, seq = fasta_records(src.text("arab_repeat_genome"))[0]
    block = complete_gene_blocks(src.text("arab_gene_models"), seqid=ident)[0]
    end = max(int(line.split("\t")[4]) for line in block)
    if end > len(seq):
        raise ValueError("matched real feature lies outside source DNA prefix")
    seq = seq[:max(end, 6000)]
    changed_id = ident + ".v2"
    rows = []
    for line in block:
        fields = line.split("\t"); fields[0] = changed_id
        rows.append("\t".join(fields))
    return {
        "reference.fa": Artifact(fasta_bytes([(ident, seq)]), ("arab_repeat_genome",), f"original ID and first {len(seq)} real bases, covering complete selected gene", "fasta_records"),
        "models.gff3": Artifact(("##gff-version 3\n" + "\n".join(rows) + "\n").encode(),
            ("arab_gene_models",), f"first complete gene on {ident}; only seqid changed to {changed_id}; original coordinates/attributes preserved", "feature_subset"),
        "sequence_names.json": Artifact(json_bytes({"reference_sequence_names": [ident],
            "annotation_sequence_names": [changed_id], "common_sequence_names": []}),
            ("arab_repeat_genome", "arab_gene_models"), "derive names from visible FASTA/GFF; baseline matched before seqid-only transformation"),
    }
