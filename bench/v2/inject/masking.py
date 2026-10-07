from __future__ import annotations
from inject.common import Artifact, fasta_records, fasta_bytes, json_bytes, tool_versions


def metrics(reference, delivery):
    original_n = sum(c.upper() == 'N' for c in reference)
    return {'sequence_length': len(delivery),
            'masked_sites': sum(c.islower() or c.upper() == 'N' for c in delivery),
            'masked_pct': round(100 * sum(c.islower() or c.upper() == 'N' for c in delivery) / len(delivery), 6),
            'reference_n_bases': original_n,
            'lowercase_bases': sum(c.islower() for c in delivery),
            'n_bases': sum(c.upper() == 'N' for c in delivery),
            'sequence_equal_ignorecase': reference.upper() == delivery.upper()}


def build_pair(src):
    ident, sequence = fasta_records(src.text('arab_repeat_genome'))[0]
    start, end = 100000, 112000  # one-based 100001..112000; two FASTA files fit byte upper bound
    window = sequence[start:end]
    if len(window) != end - start or not any(c.islower() for c in window):
        raise ValueError('registered real repeat window is unavailable or lacks lowercase bases')
    reference = window.upper()
    result = []
    for replace_lowercase in (False, True):
        delivery = ''.join('N' if c.islower() else c for c in window) if replace_lowercase else window
        selection = f'{ident}:100001..112000 one-based inclusive from real softmasked source; v1 first 6000 bp excluded'
        result.append({
            'reference.fa': Artifact(fasta_bytes([(ident, reference)]), ('arab_repeat_genome',), selection + '; uppercase source sequence to expose original base identities; original N retained', 'fasta_records'),
            'sequence.fa': Artifact(fasta_bytes([(ident, delivery)]), ('arab_repeat_genome',), selection + ('; replace only source lowercase bases with N' if replace_lowercase else '; original source bases and case unchanged'), 'fasta_records'),
            'mask_metrics.json': Artifact(json_bytes(metrics(reference, delivery)), ('arab_repeat_genome',), 'recompute delivered window counts and case-insensitive equality to reference; not full genome'),
            'versions.json': Artifact(json_bytes({**tool_versions(src, 'arab_repeat_run_record'), 'run_date': src.json('arab_repeat_run_record')['ts'].split('T')[0]}), ('arab_repeat_run_record',), 'project actual tool/database versions and actual provenance run date only')})
    return result
