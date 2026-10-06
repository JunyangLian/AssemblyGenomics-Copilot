"""Use real accident and final outputs to replay a stage comparison."""
from .common import Artifact, busco_summary, complete_gene_blocks, json_bytes


def build(src):
    result = {}
    for prefix, source in (("baseline", "arab_final"), ("delivery", "arab_prior")):
        role = source + "_models"
        blocks = complete_gene_blocks(src.text(role), limit=2)
        excerpt = "\n".join(line for block in blocks for line in block) + "\n"
        result[prefix + ".gtf"] = Artifact(excerpt.encode(), (role,), "first 2 complete gene blocks from the real prepared GTF", "feature_subset", "tool_verbatim", "first 2 complete gene blocks; exact rows with LF only")
        metrics = {"gene_count": src.rows[role]["selection"]["full_source_unique_gene_ids"],
                   "busco": busco_summary(src.text(source + "_busco"))}
        result[prefix + "_metrics.json"] = Artifact(json_bytes(metrics), (role, source + "_busco"),
            "gene_count from full original scan receipt; BUSCO from real matching summary; repaired final serves as comparison reference and real archive as delivery, not claimed historical adjacency")
    return result
