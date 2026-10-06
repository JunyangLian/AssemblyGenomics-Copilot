"""AGP consistency transformation using one real sequence prefix."""
from .common import Artifact, dna_prefix, fasta_bytes, json_bytes


def build(src):
    component, seq = dna_prefix(src)
    roles = ("arab_repeat_genome",)
    return {
        "assembly.fa": Artifact(fasta_bytes([("scaffold_1", seq)]), roles, "first 6000 source bases; object named scaffold_1", "fasta_records"),
        "layout.agp": Artifact(f"scaffold_1\t1\t6200\t1\tW\t{component}\t1\t6000\t+\n".encode(), roles,
                               "construct single component 1..6000 from real prefix; object end shifted by +200", "feature_subset"),
        "lengths.json": Artifact(json_bytes({"fasta_lengths": {"scaffold_1": len(seq)},
                                            "agp_object_ends": {"scaffold_1": 6200},
                                            "component_span_bp": 6000}), roles, "compute FASTA length and visible AGP object/component spans"),
    }
