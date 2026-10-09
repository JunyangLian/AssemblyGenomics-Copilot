"""Read-only capability and exact arithmetic guards over public development data."""
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from bench.inspect_adapter.readonly import PublicFiles
from bench.inspect_adapter.tool_demo import CASES, program


@pytest.fixture(scope='module')
def packets():
    return {cid: PublicFiles(CASES / cid) for cid in ('dev_001', 'dev_002', 'dev_003', 'dev_004')}


@pytest.mark.parametrize('path', ['../expected.json', 'expected.json', 'meta.json',
                                 'artifacts/expected.json', '/etc/passwd',
                                 'C:\\Users\\name\\secret', 'artifacts/../meta.json',
                                 'artifacts//query.faa', 'task.md\x00'])
def test_private_absolute_and_noncanonical_paths_denied(packets, path):
    with pytest.raises(ValueError, match='public whitelist'):
        packets['dev_001'].text(path)


def test_snapshot_load_never_reads_gold_or_meta(monkeypatch):
    original = Path.read_bytes
    def guarded(path):
        if path.name in {'expected.json', 'meta.json'}:
            raise AssertionError('private file accessed')
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', guarded)
    files = PublicFiles(CASES / 'dev_001')
    assert {p['path'] for p in files.manifest()} == {
        'task.md', 'artifacts/query.faa', 'artifacts/annotation.tsv', 'artifacts/annotation_metrics.json'}


def test_tools_after_loading_never_touch_filesystem(packets, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('filesystem read after snapshot creation')
    monkeypatch.setattr(Path, 'read_bytes', denied)
    monkeypatch.setattr(Path, 'read_text', denied)
    counts = packets['dev_001'].annotation_counts('artifacts/query.faa', 'artifacts/annotation.tsv')
    assert counts['query_records'] == counts['table_rows'] == counts['matched_ids'] == 32
    assert counts['annotated_query_records'] == 2
    assert counts['coverage_percent'] == 6.25
    assert not counts['queries_without_row'] and not counts['table_ids_without_query']
    assert not counts['duplicate_table_ids']


def test_empty_hints_are_observed_not_inferred_as_execution(packets):
    assert packets['dev_002'].stats('artifacts/hints.gff') == {
        'path': 'artifacts/hints.gff', 'bytes': 0, 'format': 'features',
        'feature_rows': 0, 'feature_counts': {}}
    assert packets['dev_002'].read_lines('artifacts/hints.gff')['lines'] == []


def test_intervals_use_closed_coordinates_and_delivery_role(packets):
    good = packets['dev_003'].interval_counts('artifacts/sequence.fa', 'artifacts/regions.tsv')['regions']
    other = packets['dev_004'].interval_counts('artifacts/sequence.fa', 'artifacts/regions.tsv')['regions']
    assert [r['length'] for r in good] == [115, 32, 33]
    assert sum(r['lowercase_acgt'] for r in good) == 180 and sum(r['N'] for r in good) == 0
    assert sum(r['N'] for r in other) == 180 and sum(r['lowercase_acgt'] for r in other) == 0


def test_line_pagination_does_not_silently_drop_remaining_lines(packets):
    files = packets['dev_003']
    page = files.read_lines('artifacts/sequence.fa', 1, 2)
    assert page['truncated'] and page['next_line'] == 3
    assert [r['line'] for r in page['lines']] == [1, 2]
    next_page = files.read_lines('artifacts/sequence.fa', page['next_line'], 2)
    assert [r['line'] for r in next_page['lines']] == [3, 4]
    for count in (0, 201, True):
        with pytest.raises(ValueError, match='line range'):
            files.read_lines('task.md', 1, count)


def test_snapshot_is_immutable_and_mock_plan_uses_only_public_names(packets):
    assert isinstance(packets['dev_001']._data, MappingProxyType)
    with pytest.raises(TypeError):
        packets['dev_001']._data['task.md'] = b'changed'
    names = {p['path'] for p in packets['dev_001'].manifest()}
    plan = program(packets['dev_001'].manifest())
    assert plan[1] == ('read_file', {'path': '../expected.json'})
    reads = [args['path'] for function, args in plan if function == 'read_file' and args['path'] != '../expected.json']
    assert set(reads) == names


def test_duplicate_fasta_and_malformed_tsv_rejected(packets):
    # Unit-only mutations of actual public fragments, not new benchmark sources.
    files = object.__new__(PublicFiles)
    fasta = packets['dev_001'].text('artifacts/query.faa')
    first = '>' + fasta.split('>', 2)[1]
    table = packets['dev_001'].text('artifacts/annotation.tsv')
    files._data = MappingProxyType({'q.faa': (fasta + first).encode(),
                                  'table.tsv': (table + 'missing-columns\n').encode()})
    with pytest.raises(ValueError, match='duplicated'):
        files.fasta('q.faa')
    with pytest.raises(ValueError, match='width'):
        files.table('table.tsv')
