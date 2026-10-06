"""Cut the trailer of deterministic gzip derived from real T1 DNA."""
import gzip
import io
from .common import Artifact, dna_prefix, fasta_bytes, json_bytes


def build(src):
    ident, seq = dna_prefix(src, 2000)
    stream = io.BytesIO()
    with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0, compresslevel=0) as handle:
        handle.write(fasta_bytes([(ident, seq)]))
    data = stream.getvalue()[:-8]
    try:
        gzip.decompress(data)
    except EOFError as error:
        diagnosis = {"file": "genome.fa.gz", "reader": "Python gzip.decompress",
                     "read_completed": False, "exception_type": type(error).__name__, "message": str(error)}
    else:
        raise ValueError("gzip transformation did not produce an incomplete stream")
    roles = ("arab_repeat_genome",)
    return {"genome.fa.gz": Artifact(data, roles, "first 2000 real bases; gzip stored blocks, filename='', mtime=0; remove final 8-byte trailer", "byte_ranges"),
            "integrity.json": Artifact(json_bytes(diagnosis), roles, "actual Python gzip.decompress exception from the visible gzip, not a fabricated tool log")}
