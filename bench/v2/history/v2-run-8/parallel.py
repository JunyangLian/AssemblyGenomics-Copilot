"""Registered request workers, fair rotation, at most one request per model."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import os
from bench.v2.runtime import REPO, canonical, read_json, write_json, digest
from bench.v2.adapter import Mock, OpenAICompatible
from bench.v2.concurrent_budget import atomic_json
from bench.v2.resume import rows as read_rows, prepare_api
from rule_adapter import evaluate_case


def schedule(queues, work, paused, emit_paused, should_stop, snapshot=lambda **state: None, max_workers=4):
    if type(max_workers) is not int or not 1 <= max_workers <= 6:
        raise ValueError('worker limit must be between1 and6')
    queues = {name: deque(jobs) for name, jobs in queues.items()}
    ready = deque(name for name, jobs in queues.items() if jobs)
    active, completed, peak = {}, 0, 0
    stopped = False
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='bench-model') as pool:
        while ready or active:
            stopped = stopped or should_stop()
            while ready and len(active) < max_workers and not stopped:
                stopped = stopped or should_stop()
                if stopped: break
                name = ready.popleft()
                if name in paused:
                    while queues[name]:
                        emit_paused(name, queues[name].popleft()); completed += 1
                    continue
                job = queues[name].popleft()
                future = pool.submit(work, name, job)
                active[future] = (name, job)
                peak = max(peak, len(active))
            snapshot(active=[{'model': name, **job} for name, job in active.values()],
                     pending=sum(map(len, queues.values())), completed=completed, peak_active=peak, stop_requested=stopped)
            if not active: break
            finished, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in finished:
                name, job = active.pop(future)
                result = future.result()  # transport failures are logged; unexpected worker failures must stop, never vanish
                completed += 1
                if result['status'] == 'identity_error': paused.add(name)
                if queues[name]: ready.append(name)
        snapshot(active=[], pending=sum(map(len, queues.values())), completed=completed,
                 peak_active=peak, stop_requested=stopped)
    return {'status': 'paused' if stopped else 'complete', 'completed_new_observations': completed,
            'peak_active': peak, 'max_workers': max_workers}


def execute(mode, root, locked, budget, schema, make_id, observe):
    plan = locked['plan']; paths = []
    if mode == 'api':
        directories, existing, paused = prepare_api(root, locked, make_id)
        paths = read_json(root / 'API_RUNS.json')['runs']
    else:
        existing, paused, directories = {}, set(), {}
        rid = make_id('mock-rules', 'A', locked['frozen_md_sha256'])
        directory = root / 'runs' / rid; directory.mkdir(parents=True)
        with (directory / 'records.jsonl').open('xb') as stream:
            for case in plan['cases']:
                for repetition in range(1, 4):
                    row = {'record_type': 'observation', 'mode': 'mock', 'group': 'A', 'model': 'rules',
                        'run_id': rid, 'case_id': case['case_id'], 'repetition': repetition,
                        'plan_sha256': locked['plan_sha256'], 'frozen_md_sha256': locked['frozen_md_sha256'],
                        'usage': None, 'usage_source': 'not_applicable', 'elapsed_seconds': 0,
                        'request_summary': {'visible_payload_sha256': case['visible_payload_sha256']},
                        **evaluate_case(root / 'cases' / case['case_id'], REPO, mock=True)}
                    stream.write(canonical(row))
        summarize(directory, 'mock', 'A', 'rules', locked)
        paths.append(directory.relative_to(root).as_posix())
        for group in plan['groups']:
            for model in plan['models']:
                directory = root / 'runs' / make_id('mock-' + model['name'], group, locked['frozen_md_sha256'])
                directory.mkdir(parents=True); (directory / 'records.jsonl').write_bytes(b'')
                directories[group, model['name']] = directory
                paths.append(directory.relative_to(root).as_posix())
    models = {m['name']: m for m in plan['models']}
    clients = {}
    def emit(name, group, row):
        directory = directories[group, name]
        row['run_id'] = directory.name
        with (directory / 'records.jsonl').open('ab') as stream:
            stream.write(canonical(row)); stream.flush()
    def work(name, job):
        if name not in clients:
            clients[name] = Mock(schema, plan['mock_seed']) if mode == 'mock' else OpenAICompatible(models[name], budget)
        result = observe(root / 'cases' / job['case_id'], job['group'], models[name], clients[name],
            job['repetition'], locked, lambda row: emit(name, job['group'], row), root)
        if mode == 'api' and plan.get('credential_recovery') and result.get('error') == 'HTTP 429':
            # Replacement credentials may also lack quota or hit a shared limit.
            # Preserve pending slots and wait for the existing requests to finish.
            (root / 'runs/STOP_AFTER_CURRENT_REQUEST').write_bytes(
                b'HTTP429 in credential-recovery cohort; review before further dispatch\n')
        return result
    def emit_paused(name, job):
        emit(name, job['group'], {'record_type': 'observation', 'mode': mode, 'model': name,
            **job, 'plan_sha256': locked['plan_sha256'], 'frozen_md_sha256': locked['frozen_md_sha256'],
            'status': 'identity_paused', 'parsed': None, 'response': None, 'usage': None,
            'attempts': 0, 'error': 'prior model identity mismatch'})
    queues = {m['name']: [{'group': g, 'case_id': c['case_id'], 'repetition': repetition}
        for g in plan['groups'] for c in plan['cases'] for repetition in range(1, 4)
        if (m['name'], g, c['case_id'], repetition) not in existing] for m in plan['models']}
    def snapshot(**state):
        atomic_json(root / 'runs/SCHEDULER_STATUS.json', {'mode': mode, 'pid': os.getpid(),
            'plan_sha256': locked['plan_sha256'], 'updated_at_utc': datetime.now(timezone.utc).isoformat(),
            'max_workers': plan['execution']['max_workers'], 'per_model_limit': 1, **state})
    outcome = schedule(queues, work, paused, emit_paused,
        lambda: mode == 'api' and (root / 'runs/STOP_AFTER_CURRENT_REQUEST').exists(),
        snapshot, plan['execution']['max_workers'])
    for (group, name), directory in directories.items():
        result = summarize(directory, mode, group, name, locked)
        print(f'{mode} {group} {name}: {result["observations"]} observations; {result["calls"]} calls', flush=True)
    write_json(root / ('MOCK_RUNS.json' if mode == 'mock' else 'API_RUNS.json'),
        {'mode': mode, 'plan_sha256': locked['plan_sha256'], 'runs': paths, 'execution': outcome})
    print(f'{mode}: {outcome["status"]}; peak workers {outcome["peak_active"]}', flush=True)
    return paths


def summarize(directory, mode, group, model, locked):
    rows = read_rows(directory / 'records.jsonl')
    attempts = [r for r in rows if r['record_type'] == 'attempt' and r['called']]
    observations = [r for r in rows if r['record_type'] == 'observation']
    result = {'mode': mode, 'run_id': directory.name, 'group': group, 'model': model,
        'plan_sha256': locked['plan_sha256'], 'frozen_md_sha256': locked['frozen_md_sha256'],
        'observations': len(observations), 'calls': len(attempts), 'api_calls': len(attempts) if mode == 'api' else 0,
        'calls_reused_from_parent': sum(bool(r.get('reused_from')) for r in attempts),
        'calls_executed_this_plan': sum(not r.get('reused_from') for r in attempts),
        'parse_errors': sum(r['status'] == 'parse_error' for r in observations),
        'input_proxy_sum': sum(r['request_summary']['input_estimate']['proxy'] for r in attempts),
        'input_byte_bound_sum': sum(r['request_summary']['input_estimate']['upper'] for r in attempts),
        'records_sha256': digest((directory / 'records.jsonl').read_bytes())}
    write_json(directory / 'summary.json', result)
    return result
