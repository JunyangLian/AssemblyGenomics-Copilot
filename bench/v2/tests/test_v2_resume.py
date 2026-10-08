"""A roster correction must retain failures and cannot spend twice on a semantic slot."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import copy
import pytest
from bench.v2.runtime import V2, read_json, write_json, canonical
from bench.v2 import resume
from bench.v2.adapter import Budget, ApprovalError
from bench.v2.plan import models


@pytest.fixture
def indexed_run(tmp_path, monkeypatch):
    locked = {'plan': {'version': 'new', 'models': [{'name': 'model'}], 'groups': ['B'],
        'cases': [{'case_id': 'case'}]}, 'plan_sha256': 'new-hash', 'frozen_md_sha256': 'f'}
    def observation(rep, status):
        return {'record_type': 'observation', 'mode': 'api', 'model': 'model', 'group': 'B',
            'case_id': 'case', 'repetition': rep, 'plan_sha256': 'new-hash', 'frozen_md_sha256': 'f',
            'status': status, 'parsed': {'verdict': 'pass'} if status == 'ok' else None,
            'reused_from': {'record_sha256': str(rep)}}
    carried = [observation(1, 'ok'), observation(2, 'api_error')]
    monkeypatch.setattr(resume, 'parent_records', lambda *args: copy.deepcopy(carried))
    write_json(tmp_path / 'runs/API_LEDGER.json', {'calls': 2, 'slots': []})
    return tmp_path, locked


def test_restart_retains_good_and_failed_results_once_without_new_reservations(indexed_run):
    root, locked = indexed_run
    directories, known, paused = resume.prepare_api(root, locked, lambda *args: 'test_model_B_f')
    assert {k[-1]: r['status'] for k, r in known.items()} == {1: 'ok', 2: 'api_error'}
    path = next(iter(directories.values())) / 'records.jsonl'; original = path.read_bytes()
    again = resume.prepare_api(root, locked, lambda *args: pytest.fail('must reuse durable index'))
    assert path.read_bytes() == original and len(again[1]) == 2
    assert read_json(root / 'runs/API_LEDGER.json')['calls'] == 2


def test_unfinished_reservation_becomes_error_once_and_identity_pause_survives(indexed_run):
    root, locked = indexed_run
    dirs, _, _ = resume.prepare_api(root, locked, lambda *args: 'test_model_B_f')
    write_json(root / 'runs/API_LEDGER.json', {'calls': 3, 'slots': [
        {'slot': 'new:model:B:case:3:0', 'usage': None}]})
    _, known, _ = resume.prepare_api(root, locked, lambda *args: 'unused')
    assert known['model', 'B', 'case', 3]['status'] == 'interrupted'
    path = next(iter(dirs.values())) / 'records.jsonl'
    original = path.read_bytes(); resume.prepare_api(root, locked, lambda *args: 'unused')
    assert path.read_bytes() == original
    rows = resume.rows(path); rows[0]['status'] = 'identity_error'; rows[0]['parsed'] = None
    path.write_bytes(b''.join(canonical(r) for r in rows))
    assert resume.prepare_api(root, locked, lambda *args: 'unused')[2] == {'model'}


def test_parent_budget_slot_cannot_be_resent_under_a_new_plan(tmp_path, monkeypatch):
    monkeypatch.setattr('bench.v2.adapter.approval', lambda *args: {
        'max_calls': 10, 'max_input_tokens': 1000000, 'max_output_tokens': 100000})
    write_json(tmp_path / 'runs/API_LEDGER.json', {'calls': 1, 'input_reserved': 100,
        'output_reserved': 8192, 'slots': [{'slot': 'old:model:B:case:1:0'}]})
    locked = {'plan': {'version': 'new', 'resume': {'parent_version': 'old'}}, 'plan_sha256': 'p'}
    b = Budget(tmp_path, locked)
    body = {'messages': [{'role': 'user', 'content': 'test'}], 'max_tokens': 8192}
    with pytest.raises(ApprovalError, match='already reserved'):
        b.reserve('model:B:case:1:0', body)
    assert read_json(tmp_path / 'runs/API_LEDGER.json')['calls'] == 1


def test_roster_requires_explicit_post_start_amendment_and_preserves_thresholds(tmp_path):
    for name in ['models.yaml', 'MODEL_AUTHORIZATION.json', 'FROZEN.md', 'preregistration.json',
                 'PROVIDER_MODELS_ROSTER2.json', 'PROVIDER_MODELS.json', 'MODEL_ROSTER_REVISION.json',
                 'VISION_MODEL_REVISION.json', 'PROVIDER_MODELS_VISION.json',
                 'SIX_MODELS_REVISION.json', 'PROVIDER_MODELS_SIX.json']:
        (tmp_path / name).write_bytes((V2 / name).read_bytes())
    assert [m['requested_model_id'] for m in models(tmp_path)] == [
        'deepseek-v4-flash-vision', 'deepseek-v4-pro-0813', 'minimax-m3', 'glm-5.3', 'qwen3.8-27b', 'kimi-k2.6']
    doc = read_json(tmp_path / 'MODEL_ROSTER_REVISION.json'); doc['thresholds_changed'] = True
    write_json(tmp_path / 'MODEL_ROSTER_REVISION.json', doc)
    with pytest.raises(ValueError, match='invalid explicit roster amendment'): models(tmp_path)
    (tmp_path / 'MODEL_ROSTER_REVISION.json').unlink()
    (tmp_path / 'VISION_MODEL_REVISION.json').unlink()
    (tmp_path / 'SIX_MODELS_REVISION.json').unlink()
    with pytest.raises(ValueError, match='roster differs'): models(tmp_path)


def test_actual_parent_resume_preserves_all_results_and_unknown_call():
    from bench.v2.plan import verify
    locked = verify()
    rows = resume.parent_records(V2, locked)
    observations = [r for r in rows if r['record_type'] == 'observation']
    receipt = read_json(V2 / locked['plan']['resume']['receipt'])
    counts = receipt.get('carried_counts', receipt['counts'])
    assert len(observations) == receipt.get('carried_observations', receipt['observations'])
    for status in ['ok', 'api_error', 'interrupted']:
        assert sum(r['status'] == status for r in observations) == counts[status]
    assert all(r.get('reused_from') for r in rows)
    assert not any(r['model'] in locked['plan']['resume'].get('audit_only_models', []) for r in rows)


def test_replacement_does_not_reclassify_the_previous_flash_response():
    from bench.v2.plan import verify
    locked = verify()
    parent_path = V2 / 'history/v2-run-4/resume_records.jsonl'
    original = resume.rows(parent_path)
    old = [r for r in original if r['model'] == 'DeepSeek-V4-Flash-0731' and r['record_type'] == 'observation']
    assert len(old) == 72
    assert sum(r['status'] == 'identity_error' for r in old) == 1
    assert all(r['parsed'] is None for r in old)
    assert all(r['model'] != 'DeepSeek-V4-Flash-0731' for r in resume.parent_records(V2, locked))


def test_old_qwen_identity_failure_is_audit_only_not_promoted_to_fp8():
    from bench.v2.plan import verify
    old = [r for r in resume.rows(V2 / 'history/v2-run-6/resume_records.jsonl')
           if r['record_type'] == 'observation' and r['model'] == 'Qwen3.8-27B']
    assert len(old) == 144
    assert sum(r['status'] == 'identity_error' for r in old) == 1
    assert sum(r['status'] == 'identity_paused' for r in old) == 143
    assert all(r['parsed'] is None for r in old)
    from bench.v2.runtime import digest
    archived_plan = read_json(V2 / 'history/v2-run-7/RUN_PLAN.json')
    carried = resume.parent_records(V2, {'plan': archived_plan,
        'plan_sha256': digest((V2 / 'history/v2-run-7/RUN_PLAN.json').read_bytes()),
        'frozen_md_sha256': archived_plan['frozen_md_sha256']})
    assert not any(r['model'] in ('Qwen3.8-27B', 'Qwen3.8-27B-FP8') for r in carried)


def test_operator_stop_finishes_without_any_new_request_or_fake_failures(tmp_path, monkeypatch):
    from contextlib import nullcontext
    from bench.v2 import run
    locked = {'plan': {'models': [{'name': 'model'}], 'cases': [{'case_id': 'case'}]},
              'plan_sha256': 'p', 'frozen_md_sha256': 'f'}
    (tmp_path / 'schemas').mkdir()
    write_json(tmp_path / 'schemas/model_output.schema.json', {})
    directories = {}
    for group in ['B', 'C2']:
        directory = tmp_path / 'runs' / ('model_' + group); directory.mkdir(parents=True)
        (directory / 'records.jsonl').write_bytes(b'')
        directories[group, 'model'] = directory
    (tmp_path / 'runs/STOP_AFTER_CURRENT_REQUEST').write_bytes(b'operator requested stop\n')
    monkeypatch.setattr(run, 'verify', lambda *args: locked)
    monkeypatch.setattr(run, 'approval', lambda *args: None)
    monkeypatch.setattr(run, 'exclusive', lambda *args: nullcontext())
    monkeypatch.setattr(run, 'Budget', lambda *args: object())
    monkeypatch.setattr(run, 'prepare_api', lambda *args: (directories, {}, set()))
    monkeypatch.setattr(run, 'OpenAICompatible', lambda *args: pytest.fail('no credential/client access after stop'))
    assert run.execute('api', tmp_path) == []
    assert all((d / 'records.jsonl').read_bytes() == b'' for d in directories.values())
