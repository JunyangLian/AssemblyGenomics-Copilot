from __future__ import annotations
from collections import Counter
from urllib.parse import unquote
from inject.common import Artifact, complete_gene_blocks, json_bytes, fasta_records
from v2.inject.functional import complete_records


def attributes(row):
    return dict(item.split('=', 1) for item in row.split('\t')[8].split(';') if '=' in item)


def metrics(gff, proteins):
    rows = [r.split('\t') for r in gff.splitlines() if r and not r.startswith('#')]
    faa = fasta_records(proteins)
    return {'feature_rows': len(rows), 'gene_rows': sum(r[2] == 'gene' for r in rows),
            'mrna_rows': sum(r[2] == 'mRNA' for r in rows), 'cds_rows': sum(r[2] == 'CDS' for r in rows),
            'protein_records': len(faa), 'protein_total_aa': sum(len(s) for _, s in faa),
            'protein_lengths_aa': [len(s) for _, s in faa]}


def build_pair(src):
    text = src.text('t3_gff')
    genes = sum(r.split('\t')[2] == 'gene' for r in text.splitlines() if r and not r.startswith('#'))
    blocks = complete_gene_blocks(text, limit=genes, full_source=True)
    records = complete_records(src.text('t3_proteins'))
    selected, ids = [], []
    for block in blocks[2:]:
        cds = [r for r in block if r.split('\t')[2] == 'CDS']
        counts = Counter(unquote(attributes(r)['protein_id']) for r in cds)
        if not counts or max(counts.values()) < 2 or not set(counts) <= records.keys():
            continue
        if any(r.split('\t')[2] not in ('gene', 'mRNA', 'exon', 'CDS') for r in block):
            continue
        selected.append(block)
        ids.extend(i for i in counts if i not in ids)
        if len(selected) == 2: break
    if len(selected) != 2:
        raise ValueError('source lacks two complete, previously unshown multi-CDS gene blocks')
    original = '##gff-version 3\n' + '\n'.join(r for b in selected for r in b) + '\n'
    proteins = b''.join(records[i] for i in ids)
    gene_ids = [attributes(b[0])['ID'] for b in selected]
    result = []
    for change_ids in (False, True):
        rows = []
        for line in original.splitlines():
            if change_ids and line and not line.startswith('#') and line.split('\t')[2] == 'CDS':
                fields = line.split('\t')
                fields[8] = ';'.join('protein_id=' + value.split('=', 1)[1] + '.protein' if value.startswith('protein_id=') else value for value in fields[8].split(';'))
                line = '\t'.join(fields)
            rows.append(line)
        gff = '\n'.join(rows) + '\n'
        selection = f'first two source multi-CDS gene blocks after excluding first two v1 displayed blocks; complete genes={",".join(gene_ids)}; proteins={",".join(ids)}'
        result.append({
            'models.gff3': Artifact(gff.encode(), ('t3_gff',), selection + ('; append .protein only to CDS protein_id values; other attributes/coordinates unchanged' if change_ids else '; original feature rows unchanged'), 'feature_subset'),
            'proteins.faa': Artifact(proteins, ('t3_proteins',), selection + '; complete original FAA records', 'fasta_records'),
            'annotation_metrics.json': Artifact(json_bytes(metrics(gff, proteins.decode())), ('t3_gff', 't3_proteins'), 'recompute feature and FAA counts/lengths from delivered excerpts only')})
    return result
