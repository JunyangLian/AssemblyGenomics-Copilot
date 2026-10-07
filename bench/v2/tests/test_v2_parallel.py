"""Budget races and slow-model isolation must be tested before paid concurrency."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import pytest
from bench.v2.runtime import read_json
from bench.v2.concurrent_budget import ConcurrentBudget, atomic_read_json
from bench.v2.adapter import ApprovalError
from bench.v2.parallel import schedule

BODY = {'messages': [{'role': 'user', 'content': 'fixture'}], 'max_tokens': 8192}


def budget(tmp_path, monkeypatch, cap):
    monkeypatch.setattr('bench.v2.concurrent_budget.approval', lambda *args: {
        'max_calls': cap, 'max_input_tokens': 1000000, 'max_output_tokens': cap * 8192})
    locked = {'plan': {'version': 'parallel-test'}, 'plan_sha256': 'test'}
    return ConcurrentBudget(tmp_path, locked)


def test_concurrent_reservations_cannot_overspend_or_lose_usage(tmp_path, monkeypatch):
    shared = budget(tmp_path, monkeypatch, 7)
    def run(i):
        try: shared.reserve(f'model:B:case:{i}:0', BODY)
        except ApprovalError: return False
        shared.usage(f'model:B:case:{i}:0', {'prompt_tokens': 10, 'completion_tokens': i})
        return True
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(run, range(30)))
    state = read_json(tmp_path / 'runs/API_LEDGER.json')
    assert sum(results) == state['calls'] == len(state['slots']) == 7
    assert state['output_reserved'] == 7 * 8192
    assert len({r['slot'] for r in state['slots']}) == 7
    assert all(isinstance(r['usage'], dict) for r in state['slots'])
    assert all(r['input_reserved'] > 0 for r in state['slots'])


def test_duplicate_simultaneous_requests_reserve_once(tmp_path, monkeypatch):
    shared = budget(tmp_path, monkeypatch, 10)
    def attempt(_):
        try: shared.reserve('model:B:case:1:0', BODY); return True
        except ApprovalError: return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(8))) == 1
    assert read_json(tmp_path / 'runs/API_LEDGER.json')['calls'] == 1


def test_progress_readers_always_see_complete_atomic_ledger(tmp_path, monkeypatch):
    shared = budget(tmp_path, monkeypatch, 40)
    shared.reserve('init', BODY)
    finished = threading.Event(); failures = []
    def reader():
        while not finished.is_set():
            try:
                state = atomic_read_json(shared.path)
                assert state['calls'] == len(state['slots'])
            except Exception as exc: failures.append(type(exc).__name__)
    thread = threading.Thread(target=reader); thread.start()
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda i: shared.reserve(f'slot{i}', BODY), range(20)))
    finally: finished.set(); thread.join(timeout=5)
    assert failures == []


def test_over_limit_usage_stops_other_workers_and_preserves_prior_state(tmp_path, monkeypatch):
    shared = budget(tmp_path, monkeypatch, 10)
    shared.reserve('first', BODY)
    shared.usage('first', {'prompt_tokens': 10000000, 'completion_tokens': 1})
    with pytest.raises(ApprovalError, match='exceeded'):
        shared.reserve('second', BODY)
    assert read_json(shared.path)['calls'] == 1
    assert read_json(shared.path)['provider_usage_exceeded_reservation'] is True


def test_four_workers_rotate_fifth_model_without_same_model_overlap():
    guard = threading.Lock(); active = Counter(); peak = 0; starts = []
    queues = {name: [{'case_id': str(i)} for i in range(4)] for name in ['slow', 'p', 'm', 'g', 'q']}
    slow_release = threading.Event()
    def work(name, job):
        nonlocal peak
        with guard:
            active[name] += 1; starts.append((name, job['case_id']))
            assert active[name] == 1
            peak = max(peak, sum(active.values()))
        if name == 'slow':
            assert slow_release.wait(5)
        else:
            time.sleep(0.02)
            if name == 'q': slow_release.set()
        with guard: active[name] -= 1
        return {'status': 'ok'}
    result = schedule(queues, work, set(), lambda *args: pytest.fail('unexpected pause'), lambda: False)
    assert peak == result['peak_active'] == 4
    assert result['completed_new_observations'] == 20
    assert len(starts) == len(set(starts)) == 20
    assert ('q', '0') in starts[:5]  # fifth model runs before the slow model completes


def test_identity_error_pauses_its_remaining_jobs_without_affecting_others():
    called, paused_rows = [], []
    def work(name, job): called.append((name, job['case_id'])); return {'status': 'identity_error' if name == 'bad' else 'ok'}
    queues = {name: [{'case_id': str(i)} for i in range(3)] for name in ['bad', 'good']}
    result = schedule(queues, work, set(), lambda name, job: paused_rows.append((name, job['case_id'])), lambda: False)
    assert called.count(('bad', '0')) == 1
    assert sum(name == 'bad' for name, _ in called) == 1
    assert len(paused_rows) == 2 and sum(name == 'good' for name, _ in called) == 3
    assert result['completed_new_observations'] == 6


def test_graceful_stop_drains_existing_workers_without_starting_remaining_jobs():
    stop = threading.Event(); called = []; guard = threading.Lock(); barrier = threading.Barrier(4)
    def work(name, job):
        with guard: called.append(name)
        barrier.wait(timeout=5); stop.set(); time.sleep(0.03)
        return {'status': 'ok'}
    queues = {name: [{'case_id': str(i)} for i in range(3)] for name in ['a', 'b', 'c', 'd', 'e']}
    result = schedule(queues, work, set(), lambda *args: pytest.fail('unexpected pause'), stop.is_set)
    assert len(called) == result['completed_new_observations'] == 4
    assert result['status'] == 'paused'
