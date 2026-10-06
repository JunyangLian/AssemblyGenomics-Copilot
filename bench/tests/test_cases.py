"""Privacy and adversarial validation tests; biology fixtures are accepted real data."""
import json
from pathlib import Path
import shutil
import sys

import pytest

BENCH=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BENCH))
from visible_input import serialize
from validate_cases import validate, evidence_valid, leak_errors
from build_cases import DEFAULT_BUNDLE


def test_private_files_never_enter_packet(tmp_path):
    case=tmp_path/'case'; (case/'artifacts').mkdir(parents=True)
    (case/'task.md').write_bytes(b'Privacy control\n')
    (case/'artifacts/control.txt').write_bytes(b'visible\n')
    (case/'expected.json').write_bytes(b'PRIVATE_ANSWER_SENTINEL')
    (case/'meta.json').write_bytes(b'PRIVATE_META_SENTINEL')
    text=serialize(case)
    assert 'visible' in text
    assert 'PRIVATE_' not in text


def test_private_named_artifact_rejected(tmp_path):
    case=tmp_path/'case'; (case/'artifacts').mkdir(parents=True)
    (case/'task.md').write_bytes(b'Privacy control\n')
    (case/'artifacts/meta.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='private filename'): serialize(case)


@pytest.fixture
def real_case(tmp_path):
    if not DEFAULT_BUNDLE.exists(): pytest.skip('accepted private T1/T3 source bundle absent')
    path=tmp_path/'case_009'; shutil.copytree(BENCH/'cases/case_009',path)
    return path


def test_injection_words_in_artifacts_are_rejected(real_case):
    meta=json.loads((real_case/'meta.json').read_text(encoding='utf-8'))
    p=real_case/'artifacts/functional.tsv'; p.write_bytes(p.read_bytes()+b'injected\n')
    assert any('trace word' in e for e in leak_errors(real_case,meta,['none','id_mismatch']))


def test_underscore_enum_never_has_exception(real_case):
    meta=json.loads((real_case/'meta.json').read_text(encoding='utf-8'))
    p=real_case/'task.md'; p.write_bytes(p.read_bytes()+b'id_mismatch\n')
    assert any('root enum' in e for e in leak_errors(real_case,meta,['id_mismatch']))


def test_singleword_derived_text_not_exempt(real_case):
    meta=json.loads((real_case/'meta.json').read_text(encoding='utf-8'))
    p=real_case/'artifacts/functional.tsv'; p.write_bytes(p.read_bytes()+b'None\n')
    assert any('single-word enum' in e for e in leak_errors(real_case,meta,['none']))


def test_evidence_cannot_refer_to_answers_or_missing_fields(real_case):
    assert not evidence_valid(real_case,'expected.json:root_cause')
    assert not evidence_valid(real_case,'../task.md:1')
    assert not evidence_valid(real_case,'annotation_statistics.json:missing_field')
    assert evidence_valid(real_case,'functional.tsv:3')


def test_pair_changes_fail_validation(tmp_path):
    if not DEFAULT_BUNDLE.exists(): pytest.skip('accepted private T1/T3 source bundle absent')
    cases=tmp_path/'cases'; shutil.copytree(BENCH/'cases',cases)
    p=cases/'case_010/task.md'; p.write_bytes(p.read_bytes()+b'Extra request\n')
    result=validate(cases,reproduce=False)
    assert result['status']=='fail'
    assert any('P2 surface differs' in e for e in result['errors'])


def test_pressure_artifact_change_fails(tmp_path):
    if not DEFAULT_BUNDLE.exists(): pytest.skip('accepted private T1/T3 source bundle absent')
    cases=tmp_path/'cases'; shutil.copytree(BENCH/'cases',cases)
    p=cases/'case_015/artifacts/delivery_metrics.json'
    obj=json.loads(p.read_text()); obj['gene_count']+=1
    p.write_bytes((json.dumps(obj)+'\n').encode())
    result=validate(cases,reproduce=False)
    assert any('pressure artifacts differ' in e for e in result['errors'])
