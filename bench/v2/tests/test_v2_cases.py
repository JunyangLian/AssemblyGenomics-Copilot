"""Check privacy, failure handling and real-data reconstruction, not mock QC rules."""
import copy
from pathlib import Path
import shutil
import sys

import pytest

BENCH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BENCH))
from inject.common import json_bytes
from visible_input import serialize
from v2.build_cases import V2, DEFAULT_BUNDLE, build, portable_meta
from v2.validate_cases import validate, read, semantic_errors


@pytest.fixture
def cases(tmp_path):
    if not DEFAULT_BUNDLE.exists(): pytest.skip('accepted private T1/T3 bundle absent')
    target = tmp_path / 'cases'
    shutil.copytree(V2 / 'cases', target)
    return target


def test_current_cases_reconstruct_from_real_sources():
    if not DEFAULT_BUNDLE.exists(): pytest.skip('accepted private T1/T3 bundle absent')
    result = validate()
    assert result['status'] == 'pass', result['errors']
    assert result['case_count'] == 24 and result['reproduction_checked']
    assert result['model_calls'] == 0
    assert result['answers_frozen'] == (V2 / 'FROZEN.md').exists()


def test_build_refuses_v1_output():
    with pytest.raises(ValueError, match='overlap v1'):
        build(None, BENCH / 'cases')


def test_private_side_labels_never_enter_visible_packet(cases):
    case = cases / 'new_017'
    (case / 'v2_labels.json').write_bytes(b'PRIVATE_C2_LABEL_SENTINEL')
    (case / 'expected.json').write_bytes(b'PRIVATE_ANSWER_SENTINEL')
    assert 'PRIVATE_' not in serialize(case)


def test_recomputed_coverage_rejects_fabricated_statistic(cases):
    path = cases / 'new_017/artifacts/annotation_statistics.json'
    value = read(path); value['annotation_coverage_pct'] = 99.0
    path.write_bytes(json_bytes(value))
    assert any('not computed from delivered' in e for e in semantic_errors(cases))


def test_changed_source_binding_is_rejected(cases):
    path = cases / 'new_017/meta.json'
    value = read(path); value['source_files'][0]['source_origin_sha256'] = '0' * 64
    path.write_bytes(json_bytes(value))
    result = validate(cases, reproduce=False)
    assert any('source binding differs' in e for e in result['errors'])


def test_private_label_leak_is_rejected(cases):
    path = cases / 'new_017/artifacts/functional.tsv'
    path.write_bytes(path.read_bytes() + b'v2_labels.json\n')
    assert any('v2 private label' in e for e in validate(cases, reproduce=False)['errors'])


def test_pressure_must_preserve_parent_data(cases):
    path = cases / 'new_023/artifacts/query.faa'
    path.write_bytes(path.read_bytes().replace(b'M', b'A', 1))
    assert any('pressure artifacts differ' in e for e in validate(cases, reproduce=False)['errors'])


def test_portable_metadata_changes_only_bundle_prefix():
    meta = read(V2 / 'cases/new_017/meta.json')
    changed = copy.deepcopy(meta)
    old = changed['source_snapshot']['root']
    new = '/home/user/bench/bench_transfer/v1_prepare_t1t3_r3/bundle'
    def relocate(value):
        if isinstance(value, dict): return {k:relocate(v) for k,v in value.items()}
        if isinstance(value, list): return [relocate(v) for v in value]
        return new + value[len(old):] if isinstance(value, str) and (value == old or value.startswith(old + '/')) else value
    assert portable_meta(meta) == portable_meta(relocate(changed))
    changed['source_files'][0]['source_origin'] += '.another'
    assert portable_meta(meta) != portable_meta(changed)
