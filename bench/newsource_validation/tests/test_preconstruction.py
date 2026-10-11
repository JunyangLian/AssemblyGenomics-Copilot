import copy
import json
from pathlib import Path

import pytest

from bench.inspect_adapter import t3_packets as old, t3_task
from bench.inspect_adapter.readonly import PublicFiles
from bench.newsource_validation import cases, intake, protocol


@pytest.mark.parametrize('name', ['../x', '/x', 'x\\y', 'C:/x', '', None, 17])
def test_transport_path_cannot_escape_or_be_nontext(tmp_path, name):
    with pytest.raises(ValueError, match='unsafe'):
        intake.safe_file(tmp_path, name)


def test_transport_cache_does_not_rescan_unchanged_originals(monkeypatch, tmp_path):
    # Transport plumbing fixture, not a benchmark source or simulated genome.
    path = tmp_path / 'fixture.txt'
    path.write_bytes(b'cache fixture\n')
    digest = intake.sha(path)
    manifest = {'format': 'v3-source-prepare-1', 'files': [{'path': path.name,
                'size_bytes': path.stat().st_size, 'sha256': digest}]}
    mp = tmp_path / 'MANIFEST.json'
    mp.write_bytes(old.canonical(manifest))
    mh = intake.sha(mp)
    (tmp_path / 'MANIFEST.sha256').write_bytes(f'{digest}  fixture.txt\n{mh}  MANIFEST.json\n'.encode())
    receipt = {'bundle_path': str(tmp_path.resolve()), 'transport_manifest_sha256': mh,
               'verified_signatures': {path.name: intake.signature(path)}}
    rp = tmp_path.parent / ('receipt-' + tmp_path.name + '.json')
    rp.write_bytes(old.canonical(receipt))
    monkeypatch.setattr(intake, 'sha', lambda path: pytest.fail('unexpected full SHA rescan'))
    assert intake.verify(tmp_path, rp) == receipt
    path.write_bytes(b'changed fixture\n')
    with pytest.raises(ValueError, match='identity changed'):
        intake.verify(tmp_path, rp)


def test_inline_and_retrieval_have_same_public_bytes_and_no_private_gold():
    files = PublicFiles(t3_task.DIRECTORY / 'cases/t3_001')
    inline, tools = (protocol.messages(files, c) for c in ('inline', 'tools'))
    assert inline[0] == tools[0]
    a, b = json.loads(inline[1]['content']), json.loads(tools[1]['content'])
    assert a['task'] == b['task'] and a['files'] == b['files']
    assert set(a['artifacts']) == {f['path'] for f in files.manifest() if f['path'].startswith('artifacts/')}
    for path, text in a['artifacts'].items():
        assert files.text(path) == text
    for msg in inline + tools:
        assert 'expected.json' not in msg['content'] and 'meta.json' not in msg['content']


def test_native_offline_phases_match_and_final_submission_disables_tools(tmp_path):
    for mode, expected in [('early', [2048, 8192] * 2), ('maximum', [2048] * 5 + [8192])]:
        calls = {}
        for condition in ('inline', 'tools'):
            log, calls[condition] = protocol.probe(condition, mode, tmp_path / mode / condition)
            assert len(log.samples) == 2
            sequence = [r['max_tokens'] for r in calls[condition]]
            assert sequence == (expected if mode == 'early' else expected * 2)
            for record in calls[condition]:
                assert all(record['extra_body'][k] == v for k, v in protocol.THINKING.items())
                if record['max_tokens'] == 8192:
                    assert record['tools'] == []
                else:
                    assert record['tools'] == (['list_files', 'read_file'] if condition == 'tools' else [])
        assert [r['extra_body'] for r in calls['inline']] == [r['extra_body'] for r in calls['tools']]


def development_selection():
    """Old real subsets only: never read new-source features before protocol lock."""
    records = list(old.read_json(t3_task.DIRECTORY / 'selection/SOURCE_SUBSETS.json').values())
    selected = {}
    for (accession, mode), source in zip(cases.ASSIGNMENT, records):
        record = copy.deepcopy(source)
        record['mode'] = mode
        selected[accession] = record
    return selected


def test_new_generator_is_deterministic_on_old_development_records_and_scope():
    selected = development_selection()
    generated = cases.generate(selected)
    assert generated == cases.generate(selected)
    result = cases.validate(generated, selected)
    assert len(result) == 12
    assert sum(r['type'] == 'fault' for r in result.values()) == 6
    assert all(r['artifact_read_pages'] <= 4 for r in result.values())
    assert all(not json.loads(p['expected.json'])['user_approved'] for p in generated.values())


def test_public_edit_or_gold_edit_rejected_even_when_schema_valid():
    selected = development_selection()
    generated = cases.generate(selected)
    generated['qc_001']['artifacts/models.gff3'] += b'# another row\n'
    with pytest.raises(ValueError, match='deterministic'):
        cases.validate(generated, selected)
    generated = cases.generate(selected)
    gold = json.loads(generated['qc_001']['expected.json'])
    gold['acceptable_decisions'][0]['verdict'] = 'warn'
    generated['qc_001']['expected.json'] = old.canonical(gold)
    with pytest.raises(ValueError, match='deterministic'):
        cases.validate(generated, selected)
