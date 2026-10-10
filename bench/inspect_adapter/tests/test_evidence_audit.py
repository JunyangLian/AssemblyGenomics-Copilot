"""Integrity failures and fresh-clone replay, using the preserved real packet.

These checks do not turn author diagnoses into a semantic correctness scorer.
"""
import json
import shutil
from types import SimpleNamespace

import pytest

from bench.inspect_adapter import evidence_audit as audit


@pytest.fixture
def exported(tmp_path, monkeypatch):
    directory = tmp_path / 'audit'
    shutil.copytree(audit.DIRECTORY, directory)
    receipt = tmp_path / 'RUN_RECEIPT.json'
    receipt.write_bytes(audit.RECEIPT.read_bytes())
    (tmp_path / 'pilot2').mkdir()
    for name in ('FROZEN.json', 'packets.draft.json'):
        (tmp_path / 'pilot2' / name).write_bytes((audit.pilot.ROOT / 'pilot2' / name).read_bytes())
    monkeypatch.setattr(audit, 'DIRECTORY', directory)
    monkeypatch.setattr(audit, 'RECEIPT', receipt)
    # A fresh clone has public cases and this export, but no private run logs.
    monkeypatch.setattr(audit.pilot, 'ROOT', tmp_path)
    return directory


def change_json(path, mutate):
    data = json.loads(path.read_text(encoding='utf-8'))
    mutate(data)
    path.write_text(json.dumps(data), encoding='utf-8', newline='\n')


def test_export_verifies_without_keys_or_original_private_logs(exported, monkeypatch):
    class NoCredentials:
        def get(self, *args):
            raise AssertionError('offline verification accessed credentials')
    monkeypatch.setattr(audit.pilot, 'os', SimpleNamespace(environ=NoCredentials()))
    result = audit.verify()
    assert result['provider_calls'] == 0
    assert result['planned_cases'] == 4 and result['calculation_traces'] == 10
    assert result['evidence_items'] == 24
    assert result['official_counts']['decision_joint'] == {'N': 4, 'n': 3}
    assert result['private_native_logs_reverified'] is False
    assert result['private_artifacts_reverified'] == 0
    assert result['official_score_changed'] is False
    assert result['human_review'] is False and result['independent_review'] is False


@pytest.mark.parametrize('mutation,message', [
    (lambda p: p['cases'].pop(), 'dropped or replaced'),
    (lambda p: p['cases'][0]['evidence'][0].update(observation='replacement'), 'altered model response'),
    (lambda p: p['cases'][0]['evidence'][0]['cited_location'].update(text='replacement'), 'cited location'),
    (lambda p: p['cases'][0]['calculation_trace'][0]['recorded_result'].update(bytes=0), 'does not reproduce'),
    (lambda p: p['cases'][0]['calculation_trace'].pop(), 'calculation trace'),
])
def test_export_cannot_omit_samples_rewrite_evidence_or_forge_tool_results(exported, mutation, message):
    change_json(exported / 'PACKET.json', mutation)
    with pytest.raises(ValueError, match=message):
        audit.verify()


@pytest.mark.parametrize('field', ['human_review', 'blind', 'independent', 'official_score_changed'])
def test_review_cannot_be_relabelled_as_human_blind_or_formal_scoring(exported, field):
    change_json(exported / 'AUTHOR_REVIEW.json', lambda r: r.update({field: True}))
    with pytest.raises(ValueError, match='misrepresented'):
        audit.verify()


def test_notes_cannot_be_detached_from_original_evidence(exported):
    change_json(exported / 'AUTHOR_REVIEW.json',
                lambda r: r['cases'][0]['evidence'][0].update(item_sha256='0' * 64))
    with pytest.raises(ValueError, match='different evidence item'):
        audit.verify()


def test_original_result_copy_is_bound_to_receipt(exported):
    change_json(exported / 'MODEL_RESULTS.json', lambda r: r['rows'].pop())
    with pytest.raises(ValueError, match='audit source or receipt changed'):
        audit.verify()


def test_revised_public_bytes_cannot_be_hidden_by_refreshing_audit_manifest(exported, tmp_path, monkeypatch):
    case_root = tmp_path / 'cases'
    shutil.copytree(audit.pilot.CASES / 'dev_001', case_root / 'dev_001')
    task = case_root / 'dev_001/task.md'
    task.write_bytes(task.read_bytes() + b'\nreplacement task\n')
    files = audit.pilot.PublicFiles(case_root / 'dev_001')
    change_json(exported / 'PACKET.json', lambda p: p['cases'][0].update(public_manifest=files.manifest()))
    monkeypatch.setattr(audit.pilot, 'CASES', case_root)
    with pytest.raises(ValueError, match='public bytes differ'):
        audit.verify()


def test_frozen_manifest_cannot_be_replaced(exported):
    path = audit.pilot.ROOT / 'pilot2/packets.draft.json'
    change_json(path, lambda m: m.pop('dev_001'))
    with pytest.raises(ValueError, match='original freeze'):
        audit.verify()


def test_partial_private_log_presence_still_checks_available_bytes(exported):
    receipt = audit.pilot.read_json(audit.RECEIPT)
    name = next(iter(receipt['artifact_sha256']))
    private = audit.pilot.ROOT / name
    private.parent.mkdir(parents=True)
    private.write_bytes(b'changed private artifact')
    with pytest.raises(ValueError, match='available private logs changed'):
        audit.verify()


def test_audit_export_cannot_be_read_through_model_tools():
    files = audit.pilot.PublicFiles(audit.pilot.CASES / 'dev_001')
    for path in ('expected.json', 'meta.json', '../../audit/pilot2/MODEL_RESULTS.json'):
        with pytest.raises(ValueError, match='public whitelist'):
            files.text(path)
    with pytest.raises(ValueError, match='unsupported calculation operation'):
        audit.recompute(files, '__import__', {})
