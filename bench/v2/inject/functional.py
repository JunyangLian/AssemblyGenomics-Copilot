from __future__ import annotations
import csv
import io
import re
from inject.common import Artifact, json_bytes


def complete_records(text):
    """Keep complete original FAA headers and sequence wrapping, normalized to LF."""
    records = {}
    for part in text.split('>')[1:]:
        ident = part.splitlines()[0].split()[0]
        if ident in records:
            raise ValueError('duplicate source protein ID')
        records[ident] = ('>' + part.rstrip('\n') + '\n').encode('utf-8')
    return records


def metrics(table, query_ids):
    rows = list(csv.DictReader(io.StringIO(table), delimiter='\t'))
    ids = [r['query'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate functional query ID')
    flags = [k for k in rows[0] if k.endswith('-Annotated')]
    if len(flags) != 7 or any(r[f] not in ('0', '1') for r in rows for f in flags):
        raise ValueError('unsupported source annotation flags')
    annotated = {r['query'] for r in rows if any(r[f] == '1' for f in flags)}
    count = len(annotated & set(query_ids))
    return {'query_proteins': len(query_ids), 'annotation_rows': len(rows),
            'annotated_query_proteins': count,
            'annotation_coverage_pct': round(100 * count / len(query_ids), 6)}


def build_pair(src, count):
    originals = list(csv.DictReader(io.StringIO(src.text('arab_functional_table')), delimiter='\t'))
    fields = list(originals[0])
    flags = [f for f in fields if f.endswith('-Annotated')]
    proteins = complete_records(src.text('arab_query_proteins'))
    selected = [r for r in originals[64:] if r['query'] in proteins and any(r[f] == '1' for f in flags)][:count]
    if len(selected) != count or count not in (64, 32, 16):
        raise ValueError('insufficient complete real annotated queries')
    ids = [r['query'] for r in selected]
    if len(set(ids)) != count:
        raise ValueError('source selection has duplicate IDs')
    keep = count // 16
    result = []
    for change_ids in (False, True):
        rows = []
        for index, original in enumerate(selected):
            row = dict(original)
            if index >= keep:
                if change_ids:
                    # An injective representation change; matching prefix remains real.
                    suffix = re.search(r'\.t(\d+)$', row['query'])
                    if suffix is None:
                        raise ValueError('selected source requires a different registered ID transform')
                    row['query'] = row['query'][:suffix.start()] + '.transcript' + suffix[1]
                else:
                    for field in fields[1:]:
                        row[field] = '0' if field in flags else ''
            rows.append(row)
        output = io.StringIO(newline='\n')
        writer = csv.DictWriter(output, fields, delimiter='\t', lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
        table = output.getvalue()
        stats = metrics(table, ids)
        if stats['annotated_query_proteins'] != keep:
            raise ValueError('pair coverage could not be reproduced from actual transformed rows')
        selection = f'skip first 64 source table records; next {count} annotated complete FAA-linked queries in original order; IDs={",".join(ids)}; retain first {keep} exact joins'
        result.append({
            'query.faa': Artifact(b''.join(proteins[i] for i in ids), ('arab_query_proteins',), selection, 'fasta_records'),
            'functional.tsv': Artifact(table.encode(), ('arab_functional_table',), selection + ('; change terminal .tN to .transcriptN after retained prefix, preserve annotation values' if change_ids else '; clear all seven flags AND other annotation payload fields after retained prefix'), 'line_ranges'),
            'annotation_statistics.json': Artifact(json_bytes(stats), ('arab_functional_table', 'arab_query_proteins'), 'recompute exact-ID joined coverage from delivered table and selected FAA; not whole-run statistics')})
    return result
