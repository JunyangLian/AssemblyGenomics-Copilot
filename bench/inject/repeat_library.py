"""Project real versions and QC; change only the Dfam version for the fault."""
from .common import Artifact, json_bytes, projected_repeat_qc, tool_versions


def build(src, older=False):
    versions = tool_versions(src, "arab_repeat_run_record")
    if older:
        versions["database_version"] = "3.0"
    return {
        "versions.json": Artifact(json_bytes(versions), ("arab_repeat_run_record",),
                                  "project actual tools; Dfam 3.9 -> 3.0" if older else "project actual recorded tools, retaining Dfam 3.9"),
        "mask_metrics.json": Artifact(json_bytes(projected_repeat_qc(src, "arab_repeat_qc")),
                                      ("arab_repeat_qc",), "keep real numeric/invariance fields; omit original status, hash, timestamp and project-specific rule"),
    }
