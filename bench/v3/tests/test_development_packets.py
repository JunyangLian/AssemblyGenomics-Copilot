"""Checks use committed real-derived drafts; modified copies are validator test objects."""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path
import pytest

V3 = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('v3_development_validator', V3/'validate_development.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


@pytest.fixture
def packets():
    return validator.load_packets(V3/'development/cases')


def test_real_derived_drafts_have_valid_evidence_and_role_pair(packets):
    details = validator.validate_packets(packets)
    assert len(details) == 4
    assert all(item['visible_utf8_bytes'] < 30000 for item in details.values())


def test_incorrect_summary_cannot_be_used_as_reference_truth(packets):
    changed = copy.deepcopy(packets)
    metrics = json.loads(changed['dev_001']['artifacts/annotation_metrics.json'])
    metrics['coverage_percent'] += 1
    changed['dev_001']['artifacts/annotation_metrics.json'] = validator.builder.json_bytes(metrics)
    with pytest.raises(ValueError, match='statistics/ID relation'):
        validator.validate_packets(changed)


def test_private_answer_label_in_task_is_rejected(packets):
    changed = copy.deepcopy(packets)
    changed['dev_001']['task.md'] += b'\ninsufficient_evidence\n'
    with pytest.raises(ValueError, match='enum leak'):
        validator.validate_packets(changed)


def test_nonexistent_evidence_location_is_rejected(packets):
    changed = copy.deepcopy(packets)
    answer = json.loads(changed['dev_002']['expected.json'])
    answer['key_evidence'][0]['acceptable_pointers'] = ['artifacts/input_metrics.json:unprovided_field']
    changed['dev_002']['expected.json'] = validator.builder.json_bytes(answer)
    with pytest.raises(ValueError, match='field does not exist'):
        validator.validate_packets(changed)


def test_pair_contract_cannot_drift(packets):
    changed = copy.deepcopy(packets)
    changed['dev_004']['task.md'] += '\n补充不同审核范围。\n'.encode('utf-8')
    with pytest.raises(ValueError, match='pair task/surface'):
        validator.validate_packets(changed)


def test_approved_answer_stops_builder_before_writes(packets, monkeypatch):
    work = V3/'work'
    work.mkdir(exist_ok=True)
    monkeypatch.setattr(validator.builder, 'generate', lambda _: packets)
    with tempfile.TemporaryDirectory(prefix='guard-test-',dir=work) as temp:
        output = Path(temp).resolve()
        assert output.is_relative_to(work.resolve())
        path = output/'dev_001/expected.json'
        path.parent.mkdir(parents=True)
        answer = json.loads(packets['dev_001']['expected.json'])
        answer['user_approved'] = True
        content = validator.builder.json_bytes(answer)
        path.write_bytes(content)
        with pytest.raises(ValueError, match='approved answer cannot'):
            validator.builder.build(output)
        assert path.read_bytes() == content
        assert not (output/'dev_002').exists()
