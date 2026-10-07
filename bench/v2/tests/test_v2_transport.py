"""Transport revisions must preserve failed slots and never select model answers."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pytest
from bench.v2 import register_transport as transport
from bench.v2.runtime import canonical, read_json, write_json, V2


@pytest.fixture
def failed_cohort(tmp_path, monkeypatch):
    root = tmp_path / 'v2'; root.mkdir()
    plan = {'version': 'v2-run-1', 'models': [{'name': 'test'}], 'groups': ['B'],
            'cases': [{'case_id': 'test_case'}], 'implementation': {}}
    locked = {'plan': plan, 'plan_sha256': 'old', 'frozen_md_sha256': 'frozen'}
    monkeypatch.setattr(transport, 'verify', lambda root: locked)
    monkeypatch.setattr(transport, 'request', lambda *args: {})
    monkeypatch.setattr(transport, 'summary', lambda *args: {'test_only': True})
    for name in ('RUN_PLAN.json', 'API_APPROVAL.json', 'MOCK_REPORT.json', 'MOCK_REPORT.md',
                 'MOCK_RUNS.json', 'API_APPROVAL.template.json', 'A_REUSE_RECEIPT.json', 'RULES_PACKAGE.json'):
        write_json(root / name, plan if name == 'RUN_PLAN.json' else {})
    (root / 'RUN_PLAN.sha256').write_bytes(b'old\n')
    for name in ('register_transport.py', 'start_api.ps1'):
        (root / name).write_bytes((V2 / name).read_bytes())
    row = {'record_type': 'attempt', 'mode': 'api', 'model': 'test', 'group': 'B', 'case_id': 'test_case',
           'repetition': 1, 'attempt': 0, 'status': 'api_error', 'response': None, 'parsed': None, 'usage': None,
           'plan_sha256': 'old', 'frozen_md_sha256': 'frozen'}
    p = root / 'runs/previous/records.jsonl'; p.parent.mkdir(parents=True)
    p.write_bytes(canonical(row) + canonical({**row, 'record_type': 'observation'}))
    ledger = {'calls': 2, 'input_reserved': 200, 'output_reserved': 16384, 'slots': [
        {'slot': f'v2-run-1:test:B:test_case:{rep}:0', 'usage': None} for rep in (1, 2)]}
    write_json(root / 'runs/API_LEDGER.json', ledger)
    return root, p, ledger


def test_failed_interrupted_and_unattempted_slots_remain_in_archive(failed_cohort):
    root, path, ledger = failed_cohort
    original = path.read_bytes()
    result = transport.register(root)
    assert result['counts'] == {'api_error': 1, 'interrupted': 1, 'not_executed': 1}
    assert result['planned_observations'] == 3 and result['valid_model_responses'] == 0
    assert path.read_bytes() == original
    assert read_json(root / 'runs/API_LEDGER.json') == ledger
    assert read_json(root / 'RUN_PLAN.json')['version'] == 'v2-run-2'
    assert read_json(root / 'API_APPROVAL.json')['mock_report_sha256'] is None


def test_revision_refuses_any_valid_model_response(failed_cohort):
    root, path, _ = failed_cohort
    row = read_json_line = __import__('json').loads(path.read_text().splitlines()[0])
    row.update(status='ok', response={'model': 'test'}, parsed={'verdict': 'pass'})
    path.write_bytes(canonical(row))
    with pytest.raises(ValueError, match='zero model responses'): transport.register(root)
    assert not (root / 'history/v2-run-1').exists()
