"""Empty the real hint input and recount the resulting evidence."""
from .common import Artifact, json_bytes


def build(src):
    original = src.text("arab_hints")
    if not original.strip():
        raise ValueError("real hint source is already empty")
    record = src.json("arab_final_provenance")
    return {
        "hints.gff": Artifact(b"", ("arab_hints",), "remove all entries from a nonempty real hints excerpt", "feature_subset"),
        "run_inputs.json": Artifact(json_bytes({"evidence_mode": "ET", "rna_samples": len(record["samples"]),
            "hints_file": "hints.gff", "hints_entries": 0}), ("arab_hints", "arab_final_provenance"),
            "RNA sample count/mode from actual provenance; recount the visible emptied hint file, not a simulated BRAKER execution log"),
    }
