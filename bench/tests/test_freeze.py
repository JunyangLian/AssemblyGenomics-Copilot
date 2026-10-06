"""Tampering tests use copies of the committed frozen real-data benchmark."""
import json
from pathlib import Path
import shutil
import sys

import pytest

BENCH=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BENCH))
from freeze import verify


@pytest.fixture
def frozen_copy(tmp_path):
    if not (BENCH/'FROZEN.json').exists(): pytest.skip('freeze not created yet')
    root=tmp_path/'bench'; root.mkdir()
    lock=json.loads((BENCH/'FROZEN.json').read_text(encoding='utf-8'))
    for name in ['FROZEN.md','FROZEN.json',*[r['path'] for r in lock['files']]]:
        target=root/name; target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BENCH/name,target)
    return root


def test_frozen_copy_verifies(frozen_copy):
    result=verify(frozen_copy)
    assert result['status']=='pass' and result['case_count']==16


@pytest.mark.parametrize('relative',['cases/case_009/expected.json','cases/case_010/artifacts/functional.tsv',
    'cases/case_007/meta.json','context/skill_context.md','PREREGISTRATION.md'])
def test_frozen_bytes_cannot_change(frozen_copy,relative):
    p=frozen_copy/relative;p.write_bytes(p.read_bytes()+b'changed\n')
    with pytest.raises(ValueError,match='frozen byte mismatch'):verify(frozen_copy)


def test_extra_case_artifact_rejected(frozen_copy):
    (frozen_copy/'cases/case_009/artifacts/additional.txt').write_bytes(b'transport-only extra\n')
    with pytest.raises(ValueError,match='roster changed'):verify(frozen_copy)


def test_freeze_markdown_cannot_drift(frozen_copy):
    p=frozen_copy/'FROZEN.md';p.write_bytes(p.read_bytes()+b'changed\n')
    with pytest.raises(ValueError,match='canonical representation'):verify(frozen_copy)
