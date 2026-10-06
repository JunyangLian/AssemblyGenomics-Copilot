"""Mix existing T1 yeast mates; generate no reads."""
import re
from .common import Artifact, json_bytes


def build(src):
    roles = ("yeast_rep1_r1", "yeast_rep2_r2")
    text = ["\n".join(src.text(role).splitlines()[:32]) + "\n" for role in roles]
    headers = [[re.sub(r"/[12]$", "", h.split()[0]) for h in t.splitlines()[::4]] for t in text]
    return {
        "sample_1.fastq": Artifact(text[0].encode(), (roles[0],), "first 8 complete R1 records of WT_Rep1", "fastq_records", "tool_verbatim", "lines 1-32, LF only"),
        "sample_2.fastq": Artifact(text[1].encode(), (roles[1],), "first 8 complete R2 records of WT_Rep2; neutral sample filename", "fastq_records", "tool_verbatim", "lines 1-32, LF only"),
        "read_statistics.json": Artifact(json_bytes({"read1_records": 8, "read2_records": 8,
            "matching_identifiers_by_position": sum(a == b for a, b in zip(*headers))}), roles,
            "count records and compare first header field, ignoring terminal /1 or /2"),
    }
