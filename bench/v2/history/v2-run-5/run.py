"""V2 local mock/B/C2 runner. Only public packets reach clients."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone, timedelta
import time
from bench.v2.runtime import V2, REPO, canonical, digest, read_json, write_json, request, summary, parse_response, packet, redact
from bench.v2.plan import verify
from bench.v2.adapter import Mock, Budget, OpenAICompatible, ApprovalError, approval, exclusive
from rule_adapter import evaluate_case
from bench.v2.resume import prepare_api, rows as read_rows


def run_id(model, group, frozen):
    return datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%dT%H%M%S%f+0800') + '_' + model + '_' + group + '_' + frozen[:12]


def observe(case, group, model, client, repeat, locked, emit, root=V2):
    final = None
    for attempt in range(locked['plan']['parse_retries'] + 1):
        body = request(case, group, model, root, retry=attempt > 0)
        info = summary(case, body, root)
        slot = ':'.join([model['name'], group, case.name, str(repeat), str(attempt)])
        start = time.perf_counter()
        try:
            raw, error = client.complete(body, slot)
            called = True
        except ApprovalError as exc:
            raw, error, called = None, str(exc), False
        parsed, parsing = parse_response(raw, case, root) if error is None else (None, None)
        status = ('resource_error' if not called else 'api_error') if error else ('parse_error' if parsing else 'ok')
        # The provider's pinned metadata maps this exact display name to this exact ID.
        registered_identities = {body['model'], model['name'], *model.get('accepted_response_ids', [])}
        identity_mismatch = isinstance(raw, dict) and raw.get('model') and raw['model'] not in registered_identities and not isinstance(client, Mock)
        if identity_mismatch:
            status, parsed, error = 'identity_error', None, 'returned model differs from registered request ID; pause this model'
        record = {'record_type': 'attempt', 'case_id': case.name, 'group': group, 'model': model['name'],
            'repetition': repeat, 'attempt': attempt, 'retry': attempt > 0, 'called': called,
            'mode': 'mock' if isinstance(client, Mock) else 'api', 'plan_sha256': locked['plan_sha256'],
            'frozen_md_sha256': locked['frozen_md_sha256'], 'request_summary': info, 'response': raw,
            'parsed': parsed, 'status': status, 'error': error or parsing,
            'usage': raw.get('usage') if isinstance(raw, dict) else None,
            'usage_source': 'provider' if isinstance(raw, dict) and raw.get('usage') else 'unavailable',
            'elapsed_seconds': time.perf_counter() - start, 'effective_parameters': None,
            'effective_parameters_source': 'not reported; requested protocol only; thinking default unknown'}
        emit(redact(record)); final = {**record, 'record_type': 'observation', 'attempts': attempt + 1}
        if status != 'parse_error':
            break
    emit(redact(final)); return final


def execute(mode='mock', root=V2):
    locked = verify(root)
    if mode == 'api':
        approval(root, locked)
    with exclusive(root) if mode == 'api' else nullcontext():
        budget = Budget(root, locked) if mode == 'api' else None
        schema = read_json(root / 'schemas/model_output.schema.json')
        paths, paused_models, existing = [], set(), {}
        directories = {}
        if mode == 'api':
            directories, existing, paused_models = prepare_api(root, locked, run_id)
        for group in (['A', 'B', 'C2'] if mode == 'mock' else ['B', 'C2']):
            for model in ([{'name': 'rules'}] if group == 'A' else locked['plan']['models']):
                if mode == 'api':
                    directory = directories[group, model['name']]; rid = directory.name
                    rows = read_rows(directory / 'records.jsonl')
                else:
                    rid = run_id('mock-' + model['name'], group, locked['frozen_md_sha256'])
                    directory = root / 'runs' / rid; directory.mkdir(parents=True, exist_ok=False)
                    rows = []
                client = None
                with (directory / 'records.jsonl').open('ab' if mode == 'api' else 'xb') as stream:
                    def emit(row):
                        row['run_id'] = rid; stream.write(canonical(row)); stream.flush(); rows.append(row)
                    for c in locked['plan']['cases']:
                        case = root / 'cases' / c['case_id']
                        for repeat in range(1, 4):
                            if (model['name'], group, case.name, repeat) in existing:
                                continue
                            if mode == 'api' and (root / 'runs/STOP_AFTER_CURRENT_REQUEST').exists():
                                print('API queue paused after current request; durable index and reservations retained', flush=True)
                                return paths
                            if group == 'A':
                                emit({'record_type': 'observation', 'mode': 'mock', 'group': 'A', 'model': 'rules',
                                    'case_id': case.name, 'repetition': repeat, 'plan_sha256': locked['plan_sha256'],
                                    'frozen_md_sha256': locked['frozen_md_sha256'], 'usage': None, 'usage_source': 'not_applicable',
                                    'elapsed_seconds': 0, 'request_summary': {'visible_payload_sha256': c['visible_payload_sha256']},
                                    **evaluate_case(case, REPO, mock=True)})
                            elif model['name'] in paused_models:
                                emit({'record_type': 'observation', 'mode': mode, 'group': group, 'model': model['name'],
                                    'case_id': case.name, 'repetition': repeat, 'plan_sha256': locked['plan_sha256'],
                                    'frozen_md_sha256': locked['frozen_md_sha256'], 'status': 'identity_paused',
                                    'parsed': None, 'usage': None, 'attempts': 0, 'error': 'prior model identity mismatch'})
                            else:
                                if client is None:
                                    client = Mock(schema, locked['plan']['mock_seed']) if mode == 'mock' else OpenAICompatible(model, budget)
                                result = observe(case, group, model, client, repeat, locked, emit, root)
                                if result['status'] == 'identity_error':
                                    paused_models.add(model['name'])
                attempts = [r for r in rows if r['record_type'] == 'attempt' and r['called']]
                observations = [r for r in rows if r['record_type'] == 'observation']
                write_json(directory / 'summary.json', {'mode': mode, 'run_id': rid, 'group': group, 'model': model['name'],
                    'plan_sha256': locked['plan_sha256'], 'frozen_md_sha256': locked['frozen_md_sha256'],
                    'observations': len(observations), 'calls': len(attempts), 'api_calls': len(attempts) if mode == 'api' else 0,
                    'calls_reused_from_parent': sum(bool(r.get('reused_from')) for r in attempts),
                    'calls_executed_this_plan': sum(not r.get('reused_from') for r in attempts),
                    'parse_errors': sum(r['status'] == 'parse_error' for r in observations),
                    'input_proxy_sum': sum(r['request_summary']['input_estimate']['proxy'] for r in attempts),
                    'input_byte_bound_sum': sum(r['request_summary']['input_estimate']['upper'] for r in attempts),
                    'records_sha256': digest((directory / 'records.jsonl').read_bytes())})
                paths.append(directory.relative_to(root).as_posix())
                print(f'{mode} {group} {model["name"]}: {len(observations)} observations; {len(attempts)} calls', flush=True)
        write_json(root / ('MOCK_RUNS.json' if mode == 'mock' else 'API_RUNS.json'),
                   {'mode': mode, 'plan_sha256': locked['plan_sha256'], 'runs': paths})
        return paths


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--mode', choices=['mock', 'api'], default='mock')
    args = p.parse_args(); execute(args.mode)
