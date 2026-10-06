"""P2: equal observed coverage, different content and ID-join mechanisms."""
import csv
import io
from .common import Artifact, fasta_records, fasta_bytes, json_bytes


def build(src, change_ids=False):
    source_rows = list(csv.DictReader(io.StringIO(src.text("arab_functional_table")), delimiter="\t"))[:16]
    columns = ["query"] + [key for key in source_rows[0] if key.endswith("-Annotated")]
    proteins = dict(fasta_records(src.text("arab_query_proteins")))
    identifiers = [r["query"] for r in source_rows]
    if len(source_rows) != 16 or any(ident not in proteins for ident in identifiers):
        raise ValueError("functional source lacks sixteen complete matching proteins")
    if not any(source_rows[0][k] == "1" for k in columns[1:]):
        raise ValueError("first retained real record has no annotation")
    rows = []
    for index, source in enumerate(source_rows):
        row = {key: source[key] for key in columns}
        if change_ids and index > 0:
            row["query"] = row["query"].replace(".t", "|t")
            if row["query"] == source["query"]:
                raise ValueError("selected real ID does not support the predefined format change")
        elif not change_ids and index > 0:
            for key in columns[1:]:
                row[key] = "0"
        rows.append(row)
    by_id = {r["query"]: r for r in rows}
    annotated = sum(ident in by_id and any(by_id[ident][k] == "1" for k in columns[1:]) for ident in identifiers)
    stream = io.StringIO(newline="\n")
    writer = csv.DictWriter(stream, fieldnames=columns, delimiter="\t", lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    roles = ("arab_functional_table", "arab_query_proteins")
    return {
        "query.faa": Artifact(fasta_bytes([(ident, proteins[ident]) for ident in identifiers]),
            ("arab_query_proteins",), "first 16 query IDs in real table; complete matching protein sequences, unchanged", "fasta_records"),
        "functional.tsv": Artifact(stream.getvalue().encode(), ("arab_functional_table",),
            "first 16 real rows, query plus original seven flags; preserve annotation flags but change .t -> |t in rows 2-16" if change_ids else
            "first 16 real rows, query plus original seven flags; keep row 1 and clear all flags in rows 2-16", "feature_subset"),
        "annotation_statistics.json": Artifact(json_bytes({"total_queries": len(identifiers),
            "annotated_queries": annotated, "unannotated_queries": len(identifiers) - annotated,
            "annotation_coverage_pct": round(100 * annotated / len(identifiers), 3),
            "unit": "percent", "denominator": "query proteins"}), roles,
            "recompute joined union of seven flags using exact ID matches; same denominator and coverage in both P2 cases"),
    }
