"""Protected answers, knowledge, analysis and file roster must reject mutation."""
from pathlib import Path
import shutil
import sys
import pytest

BENCH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BENCH))
from inject.common import json_bytes
from v2.freeze import V2, create, read, verify


@pytest.fixture
def frozen_copy(tmp_path):
    if not (V2 / 'FROZEN.json').exists(): pytest.skip('v2 not yet frozen')
    root = tmp_path / 'v2'; root.mkdir()
    names = [r['path'] for r in read(V2 / 'FROZEN.json')['files']] + ['FROZEN.json','FROZEN.md']
    for name in names:
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(V2 / name, target)
    assert verify(root)['status'] == 'pass'
    return root


def test_freeze_cannot_be_overwritten():
    if not (V2 / 'FROZEN.json').exists(): pytest.skip('v2 not yet frozen')
    with pytest.raises(ValueError, match='already exists'): create()


def test_frozen_answer_mutation_rejected(frozen_copy):
    path = frozen_copy / 'cases/new_019/expected.json'
    value = read(path); value['acceptable_verdicts'] = ['block']; path.write_bytes(json_bytes(value))
    with pytest.raises(ValueError, match='frozen byte mismatch'): verify(frozen_copy)


def test_frozen_context_mutation_rejected(frozen_copy):
    path = frozen_copy / 'context/skill_context.md'; path.write_bytes(path.read_bytes() + b'Changed guidance\n')
    with pytest.raises(ValueError, match='frozen byte mismatch'): verify(frozen_copy)


def test_frozen_threshold_mutation_rejected(frozen_copy):
    path = frozen_copy / 'preregistration.json'
    value = read(path); value['h1_min_joint_gain_cases'] = 0; path.write_bytes(json_bytes(value))
    with pytest.raises(ValueError, match='frozen byte mismatch'): verify(frozen_copy)


def test_unlisted_case_file_rejected(frozen_copy):
    (frozen_copy / 'cases/new_019/artifacts/extra.txt').write_bytes(b'Extra input\n')
    with pytest.raises(ValueError, match='file roster changed'): verify(frozen_copy)
