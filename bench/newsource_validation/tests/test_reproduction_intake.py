import shutil

import pytest

from bench.newsource_validation import reproduction_intake as intake
from bench.newsource_validation import cases


def seal(root):
    files = {p.relative_to(root).as_posix(): cases.old.digest(p.read_bytes()) for p in root.rglob('*')
             if p.is_file() and p.name not in ('MANIFEST.json', 'MANIFEST.sha256')}
    cases.old.write_json(root / 'MANIFEST.json', {'algorithm': 'sha256', 'files': files})
    files['MANIFEST.json'] = cases.old.digest((root / 'MANIFEST.json').read_bytes())
    (root / 'MANIFEST.sha256').write_bytes(''.join(f'{sha}  {name}\n' for name, sha in sorted(files.items())).encode())


@pytest.fixture
def returned(tmp_path):
    # All fixture case bytes are real frozen-construction drafts, not invented sources.
    root = tmp_path / 'bundle'
    shutil.copytree(cases.DIRECTORY / 'cases', root / 'cases')
    receipt = cases.old.read_json(cases.DIRECTORY / 'LINUX_REPRODUCTION.json')['server_receipt']
    cases.old.write_json(root / 'RECEIPT.json', receipt)
    seal(root)
    return root


def test_parity_never_manufactures_freeze_or_api_permission(returned):
    result = intake.verify(returned)
    assert result['case_count'] == 12 and result['case_files'] == 72 and result['differences'] == 0
    assert result['transport_payloads'] == 73
    assert not result['answer_approval'] and not result['answers_frozen']
    assert result['api_calls'] == result['original_source_rescans'] == 0


def test_changed_or_missing_case_rejected(returned):
    path = returned / 'cases/qc_001/artifacts/models.gff3'
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='payload SHA'):
        intake.verify(returned)
    path.unlink()
    with pytest.raises(ValueError, match='missing'):
        intake.verify(returned)


def test_self_consistent_altered_gold_cannot_pass_reference(returned):
    path = returned / 'cases/qc_001/expected.json'
    answer = cases.old.read_json(path)
    answer['rationale'] = 'Altered fixture, never a real expected answer.'
    cases.old.write_json(path, answer)
    seal(returned)
    with pytest.raises(ValueError, match='reference bytes differ'):
        intake.verify(returned)


def test_forged_package_identity_cannot_pass_parity(returned):
    path = returned / 'RECEIPT.json'
    receipt = cases.old.read_json(path)
    receipt['package_inputs_sha256'] = '0' * 64
    cases.old.write_json(path, receipt)
    seal(returned)
    with pytest.raises(ValueError, match='identity differs'):
        intake.verify(returned)


def test_escape_extra_files_and_sidecar_tampering_rejected(returned):
    path = returned / 'MANIFEST.json'
    original = path.read_bytes()
    manifest = cases.old.read_json(path)
    manifest['files']['../outside'] = '0' * 64
    cases.old.write_json(path, manifest)
    with pytest.raises(ValueError, match='unsafe'):
        intake.verify(returned)
    path.write_bytes(original)
    (returned / 'unregistered.txt').write_bytes(b'fixture only')
    with pytest.raises(ValueError, match='inventory differs'):
        intake.verify(returned)
    (returned / 'unregistered.txt').unlink()
    (returned / 'MANIFEST.sha256').write_bytes(b'0  MANIFEST.json\n')
    with pytest.raises(ValueError, match='sidecar'):
        intake.verify(returned)
