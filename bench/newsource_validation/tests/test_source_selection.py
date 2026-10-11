import json

import pytest

from bench.newsource_validation.audit_sources import exposed_accessions, select


def row(accession, species='Novel_species', clade='fungi', size=100, complete='True'):
    return {'accession': accession, 'species': species, 'clade': clade,
            'recorded_pair_bytes': str(size), 'recorded_complete_pair': complete,
            'server_gff_paths': '/source/genomic.gff.gz', 'server_faa_paths': '/source/protein.faa.gz'}


def test_prior_case_and_T1_species_cannot_be_selected():
    rows = [row('GCF_000001.1'), row('GCF_000002.1', species='Arabidopsis_thaliana'),
            row('GCF_000003.1', size=200), row('GCF_000004.1', complete='False')]
    assert select(rows, {'GCF_000001.1'}, count=1)[0]['accession'] == 'GCF_000003.1'


def test_no_silent_replacement_when_source_diversity_insufficient():
    with pytest.raises(ValueError, match='no automatic substitution'):
        select([row('GCF_000001.1'), row('GCF_000002.1')], set(), count=2)


def test_selection_does_not_filter_by_historical_baseline_result():
    rows = [dict(row('GCF_000002.1', size=200), report_verdict='in_band'),
            dict(row('GCF_000001.1', size=100), report_verdict='no_band')]
    assert select(rows, set(), count=1)[0]['accession'] == 'GCF_000001.1'
    assert select(list(reversed(rows)), set(), count=1) == select(rows, set(), count=1)


def test_source_fields_count_as_exposure_but_aggregate_comment_does_not(tmp_path):
    path = tmp_path / 'meta.json'
    path.write_text(json.dumps({'source_files': [{'source_origin': '/x/GCF_123456.1_genomic.gff.gz'}],
                               'notes': 'aggregate report also lists GCF_654321.1'}), encoding='utf-8')
    assert exposed_accessions([path]) == {'GCF_123456.1'}
