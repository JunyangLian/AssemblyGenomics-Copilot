"""Reject altered payloads even when a forged transport manifest is consistent."""
from pathlib import Path
import shutil
import sys
import pytest

BENCH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BENCH))
from inject.common import digest, json_bytes
from transfer import manifest
from v2.accept_reproduction import V2, inspect, read

ORIGINAL = V2 / 'incoming/v2_cases_reproduction/bundle'
SERVER_SHA = 'cb96003d2e6ee1cffbb1c25fdd668b1d7f4bd4895def7d01378f16d58354e0c6'


@pytest.fixture
def bundle(tmp_path):
    if not ORIGINAL.exists(): pytest.skip('private Linux return bundle absent')
    target = tmp_path / 'bundle'
    shutil.copytree(ORIGINAL, target)
    # Unit-test transport fixture aligned to the current draft, NOT Linux proof.
    # The real return directory remains immutable and may be an older revision.
    shutil.copytree(V2 / 'cases', target / 'cases', dirs_exist_ok=True)
    (target / 'REPRODUCED_INPUTS.json').write_bytes((V2 / 'CASE_INPUTS.json').read_bytes())
    versions = read(target / 'versions.json')
    versions['code_sha256'] = {name:digest((BENCH / name).read_bytes()) for name in versions['code_sha256']}
    (target / 'versions.json').write_bytes(json_bytes(versions))
    manifest(target)
    return target


def rewritten_manifest(bundle):
    manifest(bundle)
    return digest((bundle / 'MANIFEST.json').read_bytes())


def test_real_linux_bundle_requires_current_reference():
    if not ORIGINAL.exists(): pytest.skip('private Linux return bundle absent')
    if read(ORIGINAL / 'REPRODUCED_INPUTS.json') != read(V2 / 'CASE_INPUTS.json'):
        with pytest.raises(ValueError, match='reconstruction reference differs'):
            inspect(ORIGINAL, SERVER_SHA)
        return
    result = inspect(ORIGINAL, SERVER_SHA)
    assert result['case_count'] == 24 and result['linux_reproduction_status'] == 'pass'
    assert not result['answers_frozen'] and result['model_calls'] == 0


def test_current_unit_transport_fixture_accepted(bundle):
    result = inspect(bundle, digest((bundle / 'MANIFEST.json').read_bytes()))
    assert result['case_count'] == 24 and not result['answers_frozen']


def test_altered_payload_rejected_by_transport(bundle):
    path = bundle / 'cases/new_017/artifacts/query.faa'
    path.write_bytes(path.read_bytes() + b'X\n')
    with pytest.raises(ValueError, match='mismatch'):
        inspect(bundle, SERVER_SHA)


def test_altered_answer_rejected_with_consistent_transport(bundle):
    path = bundle / 'cases/new_017/expected.json'
    answer = read(path); answer['acceptable_verdicts'] = ['pass']
    path.write_bytes(json_bytes(answer))
    with pytest.raises(ValueError, match='expected_sha256'):
        inspect(bundle, rewritten_manifest(bundle))


def test_altered_source_origin_rejected_with_consistent_transport(bundle):
    path = bundle / 'cases/new_017/meta.json'
    meta = read(path); meta['source_files'][0]['source_origin'] += '.other'
    path.write_bytes(json_bytes(meta))
    with pytest.raises(ValueError, match='portable_meta_sha256'):
        inspect(bundle, rewritten_manifest(bundle))


def test_windows_replay_cannot_satisfy_linux_gate(bundle):
    path = bundle / 'versions.json'
    value = read(path); value['platform'] = 'Windows-11'
    path.write_bytes(json_bytes(value))
    with pytest.raises(ValueError, match='not reported from Linux'):
        inspect(bundle, rewritten_manifest(bundle))
