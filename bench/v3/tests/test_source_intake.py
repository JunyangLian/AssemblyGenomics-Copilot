"""Transport/cache tests use toy files only, never benchmark source statistics."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import gzip
import hashlib
import json
import pytest
from bench.v3.server.prepare_sources import execute, VERSION
from bench.v3.verify_sources import verify


@pytest.fixture
def intake(tmp_path):
    raw = tmp_path / 'raw'; raw.mkdir()
    bench = tmp_path / 'bench'; bench.mkdir()
    names = ['GCF_TEST.1_genomic.gff.gz', 'GCF_TEST.1_protein.faa.gz']
    contents = [b'##gff-version 3\nseq\ttest\tgene\t1\t3\t.\t+\t.\tID=g1\n',
                b'>p1\nM\n']
    items = []
    for kind, name, body in zip(['gff', 'faa'], names, contents):
        (raw / name).write_bytes(gzip.compress(body, mtime=0))
        items.append({'source_group': 'GCF_TEST.1', 'species': 'test_fixture', 'clade': 'test',
                      'kind': kind, 'filename': name,
                      'recorded_size_bytes': (raw / name).stat().st_size})
    config = bench / 'config.json'
    config.write_text(json.dumps({'spec_version': VERSION, 'source_scope': 'T3',
                      'source_root': str(raw), 'output_root': 'bench_transfer/test',
                      'historical_report_notice': 'test only', 'files': items}), encoding='utf-8')
    return raw, bench, config, bench / 'bench_transfer/test/bundle'


def check_manifest(bundle):
    for item in json.loads((bundle / 'MANIFEST.json').read_bytes())['files']:
        body = (bundle / item['path']).read_bytes()
        assert len(body) == item['size_bytes']
        assert hashlib.sha256(body).hexdigest() == item['sha256']


def test_complete_exact_copy_and_local_receipt(intake):
    raw, bench, config, bundle = intake
    original = {p.name: p.read_bytes() for p in raw.iterdir()}
    status = execute(config, bench)
    assert status['status'] == 'complete' and len(status['sources']) == 2
    assert status['api_calls'] == status['analysis_runs'] == 0
    for name, body in original.items():
        assert (bundle / 'sources' / name).read_bytes() == body == (raw / name).read_bytes()
    check_manifest(bundle)
    receipt = verify(bundle.parent, config, bench / 'received.json')
    assert receipt['source_files'] == 2 and receipt['status'] == 'verified_transport_and_format'
    assert 'not QC gold' in status['inspection_scope']


def test_repeat_does_not_read_sources_or_repeat_gzip_inspection(intake, monkeypatch):
    raw, bench, config, bundle = intake
    first = execute(config, bench)
    original_open = Path.open
    def guarded_open(path, *args, **kwargs):
        if path.parent == raw:
            raise AssertionError('original sources re-read on cached rerun')
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded_open)
    monkeypatch.setattr('bench.v3.server.prepare_sources.inspect_copy', lambda *a: pytest.fail('inspection re-run'))
    second = execute(config, bench)
    assert second['cached_files_reused'] == 2
    assert first['sources'] == second['sources']
    check_manifest(bundle)


def test_missing_file_blocks_but_produces_diagnostic_bundle(intake):
    raw, bench, config, bundle = intake
    (raw / 'GCF_TEST.1_protein.faa.gz').unlink()
    status = execute(config, bench)
    assert status['status'] == 'blocked' and len(status['gaps']) == 1
    assert (bundle / 'logs/prepare.log').exists()
    check_manifest(bundle)
    with pytest.raises(ValueError, match='incomplete'):
        verify(bundle, config)


def test_truncated_gzip_never_becomes_admitted_source(intake):
    raw, bench, config, bundle = intake
    p = raw / 'GCF_TEST.1_protein.faa.gz'; p.write_bytes(p.read_bytes()[:-6])
    status = execute(config, bench)
    assert status['status'] == 'blocked' and 'integrity/format' in status['gaps'][0]['reason']
    check_manifest(bundle)
    with pytest.raises(ValueError, match='incomplete'):
        verify(bundle, config)


def test_transport_tamper_and_changed_cache_preserve_old_sources(intake):
    raw, bench, config, bundle = intake
    execute(config, bench)
    p = bundle / 'sources/GCF_TEST.1_protein.faa.gz'; p.write_bytes(b'changed')
    with pytest.raises(ValueError, match='checksum/size mismatch'):
        verify(bundle, config)
    status = execute(config, bench)
    assert status['status'] == 'blocked' and 'cached source/copy identity changed' in status['gaps'][0]['reason']
    assert p.read_bytes() == b'changed'
    check_manifest(bundle)  # BLOCKED bundle still has a truthful transport manifest.


def test_source_changed_requires_new_output_root(intake):
    raw, bench, config, bundle = intake
    execute(config, bench)
    p = raw / 'GCF_TEST.1_protein.faa.gz'; p.write_bytes(gzip.compress(b'>p2\nMM\n', mtime=0))
    status = execute(config, bench)
    assert status['status'] == 'blocked'
    fresh = execute(config, bench, 'bench_transfer/test_r2')
    assert fresh['status'] == 'complete'
    assert verify(bench / 'bench_transfer/test_r2', config)['source_files'] == 2


def test_selection_and_output_paths_cannot_escape(intake):
    raw, bench, config, bundle = intake
    with pytest.raises(ValueError, match='escapes configured root'):
        execute(config, bench, '../outside')
    assert not (bench.parent / 'outside').exists()
    doc = json.loads(config.read_bytes()); doc['files'][0]['filename'] = '../GCF_TEST.1_genomic.gff.gz'
    config.write_text(json.dumps(doc), encoding='utf-8')
    status = execute(config, bench)
    assert status['status'] == 'blocked' and 'invalid source filename' in status['gaps'][0]['reason']


def test_receiver_rejects_different_approved_selection(intake):
    raw, bench, config, bundle = intake
    execute(config, bench)
    doc = json.loads(config.read_bytes()); doc['files'][0]['species'] = 'different_species'
    config.write_text(json.dumps(doc), encoding='utf-8')
    with pytest.raises(ValueError, match='selection differs'):
        verify(bundle, config)
