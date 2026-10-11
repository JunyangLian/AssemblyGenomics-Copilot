import json
import zipfile

import pytest

from bench.newsource_validation import review_audit as audit


def gff(cds_start=130, cds_end=150, parent='t', seqid='chr1', strand='+'):
    # Synthetic parser unit fixture only; never a source for a benchmark case.
    return ('##gff-version 3\n'
            'chr1\tX\tgene\t100\t300\t.\t+\t.\tID=g\n'
            'chr1\tX\tmRNA\t120\t200\t.\t+\t.\tID=t;Parent=g;partial=true\n'
            f'{seqid}\tX\tCDS\t{cds_start}\t{cds_end}\t.\t{strand}\t0\tID=c;Parent={parent};protein_id=P.1\n'
            'chr1\tX\tCDS\t170\t180\t.\t+\t0\tID=c;Parent=t;protein_id=P.1\n')


def test_same_cardinality_is_not_exact_protein_connection():
    facts = audit.inspect_records(gff(), '>P.101 description\nMAAA\n')
    assert len(facts['faa_headers']) == 1
    assert facts['issues']['missing_sequence_lines'] == [4, 5]
    assert facts['issues']['extra_protein_ids'] == ['P.101']
    assert not facts['contract_satisfied']


def test_all_parent_edges_checked_not_just_first_gene_to_mrna():
    facts = audit.inspect_records(gff(parent='unlisted'), '>P.1\nMAAA\n')
    assert facts['issues']['unresolved_parent_lines'] == [4]
    assert len(facts['parent_connections']) == 3
    assert not facts['contract_satisfied']


def test_coordinate_compares_direct_mrna_not_enclosing_gene():
    facts = audit.inspect_records(gff(cds_start=210, cds_end=220), '>P.1\nMAAA\n')
    assert facts['issues']['incompatible_parent_lines'] == [4]
    edge = next(e for e in facts['parent_connections'] if e['child_line'] == 4)
    assert edge['parent_interval'] == [120, 200]
    assert edge['parent_line'] == 3 and not edge['contained']


def test_partial_and_consistent_multipart_cds_are_valid():
    facts = audit.inspect_records(gff(), '>P.1\nMAAA\n')
    assert facts['contract_satisfied']
    assert len(facts['cds_connections']) == 2
    assert facts['issues']['duplicate_feature_issues'] == []


@pytest.mark.parametrize('changes', [{'seqid': 'chr2'}, {'strand': '-'}])
def test_parent_existence_does_not_waive_seqid_or_strand(changes):
    facts = audit.inspect_records(gff(**changes), '>P.1\nMAAA\n')
    assert facts['issues']['incompatible_parent_lines'] == [4]


def test_pointer_presence_not_misreported_as_complete_record_support():
    facts = audit.inspect_records(gff(), '>P.1\nMAAA\n')
    expected = {'key_evidence': [{'claim_id': 'E02', 'statement': 'all parent connections',
                'acceptable_pointers': ['artifacts/models.gff3:2', 'artifacts/models.gff3:3']}]}
    result = audit.pointer_details({'artifacts/models.gff3': gff().encode()}, expected, facts)[0]
    assert result['existing_pointer_values'][0]['resolved'].endswith('ID=g')
    assert result['supplemental_pointers_not_in_candidate'] == ['artifacts/models.gff3:4', 'artifacts/models.gff3:5']


def test_real_packets_blind_bundle_hides_gold_and_review_tables(tmp_path, monkeypatch):
    original = audit.DIRECTORY
    monkeypatch.setattr(audit, 'DIRECTORY', tmp_path)
    # Keep construction inputs byte-exact; output solely into isolated pytest temp.
    import shutil
    for name in ('cases', 'selection'):
        shutil.copytree(original / name, tmp_path / name)
    for name in ('CASE_MANIFEST.json', 'REVIEW_GUIDE.md', 'REVIEW_SHEET.csv', 'SOURCE_RECEIPT.json', 'PROTOCOL_LOCK.json'):
        shutil.copy2(original / name, tmp_path / name)
    shutil.copytree(original / 'schemas', tmp_path / 'schemas')
    (tmp_path / 'review').mkdir()
    for name in ('README.md', 'BLIND_INSTRUCTIONS.md'):
        shutil.copy2(original / 'review' / name, tmp_path / 'review' / name)
    reports, summary = audit.run()
    assert len(reports) == 12 and not summary['answers_frozen']
    assert summary['answers_changed'] is False
    with zipfile.ZipFile(tmp_path / 'review/blind_cases_package.zip') as stream:
        names = set(stream.namelist())
        assert len([n for n in names if n.endswith('/task.md')]) == 12
        assert not any(n.endswith(('expected.json', 'meta.json', '.csv')) or n.startswith('review/') for n in names)
        manifest = json.loads(stream.read('MANIFEST.json'))
        assert all(audit.digest(stream.read(n)) == sha for n, sha in manifest['files'].items())
    with zipfile.ZipFile(tmp_path / 'review/answer_review_package.zip') as stream:
        assert 'cases/qc_001/expected.json' in stream.namelist()
        assert 'review/qc_001.md' in stream.namelist()
        assert 'review/NSP1.md' in stream.namelist()
        pair = stream.read('review/NSP1.md').decode()
        assert '# qc_006' in pair and '# qc_008' in pair
        assert '### meta.json' in pair and '### task.md' in pair
        manifest = json.loads(stream.read('MANIFEST.json'))
        assert all(audit.digest(stream.read(n)) == sha for n, sha in manifest['files'].items())
    assert summary['cds_rows_checked'] == 148
    assert summary['parent_edges_checked'] == 352
    assert summary['existing_pointer_locations_checked'] == 140
