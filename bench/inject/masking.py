"""Replace existing lower-case real bases by Ns, without invented statistics."""
from .common import Artifact, dna_prefix, fasta_bytes, json_bytes


def build(src):
    ident, seq = dna_prefix(src)
    changed = "".join("N" if c.islower() else c for c in seq)
    if changed == seq:
        raise ValueError("selected source has no real lower-case bases")
    roles = ("arab_repeat_genome",)
    return {
        "sequence.fa": Artifact(fasta_bytes([(ident, changed)]), roles,
                                "first 6000 real bases; lower-case bases replaced by N, all other bases and ID preserved", "fasta_records"),
        "mask_metrics.json": Artifact(json_bytes({"sequence_length": len(changed),
            "lowercase_bases": sum(c.islower() for c in changed), "n_bases": changed.upper().count("N"),
            "repeat_bases_before_masking": sum(c.islower() for c in seq),
            "replacement_symbol": "N"}), roles, "recount exact visible sequence and source lower-case bases; no full-genome percentage substitution"),
    }
