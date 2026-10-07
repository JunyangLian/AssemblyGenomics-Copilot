"""Local B/C harness and clearly simulated A transport, guarded by locked plans."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import time
from contextlib import nullcontext

from harness_common import BENCH, canonical, read_json, request, summary, parse_response, redact, write_json
from model_adapter import Mock, OpenAICompatible, Budget, exclusive_api_run, approval
from rule_adapter import evaluate_case
from run_plan import verify


def run_id(model, group, frozen):
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%dT%H%M%S%f+0800')
    return stamp + '_' + model + '_' + group + '_' + frozen[:12]


def observe(case, group, model, client, repeat, locked, emit, root=BENCH):
    final = None
    for attempt in range(locked['plan']['parse_retries'] + 1):
        body = request(case, group, model, root, retry=attempt > 0)
        request_info = summary(case, body, root)
        slot = ':'.join([model['name'], group, case.name, str(repeat), str(attempt)])
        start = time.perf_counter()
        raw, error = client.complete(body, slot)
        elapsed = time.perf_counter() - start
        parsed, parsing = parse_response(raw, case, root) if error is None else (None, None)
        status = 'api_error' if error else ('parse_error' if parsing else 'ok')
        usage = raw.get('usage') if isinstance(raw, dict) else None
        record = {'record_type':'attempt', 'case_id':case.name, 'repetition':repeat, 'attempt':attempt,
                  'group':group, 'model':model['name'], 'mode':'mock' if isinstance(client, Mock) else 'api',
                  'plan_sha256':locked['plan_sha256'], 'frozen_md_sha256':locked['frozen_md_sha256'],
                  'request_summary':request_info, 'response':raw, 'parsed':parsed, 'status':status,
                  'error':error or parsing, 'usage':usage, 'usage_source':'provider' if usage else 'unavailable',
                  'effective_parameters':None, 'effective_parameters_source':'provider not reported; requested parameters in request_summary',
                  'elapsed_seconds':elapsed, 'retry':attempt > 0}
        emit(redact(record))
        final = {**record, 'record_type':'observation', 'attempts':attempt + 1}
        if status in ('ok', 'api_error'):
            break
    emit(redact(final))
    return final


def execute_unlocked(root=BENCH, mode='mock'):
    locked = verify(root)
    # Fail before creating logs if real approval is missing.
    budget = Budget(root, locked) if mode == 'api' else None
    paths = []
    schema = read_json(root / 'schemas/model_output.schema.json')
    groups = ['A','B','C'] if mode == 'mock' else ['B','C']
    for group in groups:
        choices = [{'name':'rules'}] if group == 'A' else locked['plan']['models']
        for model in choices:
            rid = run_id(('mock-' if mode == 'mock' else '') + model['name'], group, locked['frozen_md_sha256'])
            directory = root / 'runs' / rid
            directory.mkdir(parents=True, exist_ok=False)
            records = []
            with (directory / 'records.jsonl').open('xb') as stream:
                def emit(row):
                    row['run_id'] = rid
                    stream.write(canonical(row)); stream.flush(); records.append(row)
                if group != 'A':
                    client = Mock(schema, locked['plan']['mock_seed']) if mode == 'mock' else OpenAICompatible(model, budget)
                for row in locked['plan']['cases']:
                    case = root / 'cases' / row['case_id']
                    for repeat in range(1, locked['plan']['repetitions'] + 1):
                        if group == 'A':
                            emit({'record_type':'observation', 'mode':'mock', 'simulated':True, 'case_id':case.name,
                                  'repetition':repeat, 'group':'A', 'model':'rules', 'run_id':rid,
                                  'plan_sha256':locked['plan_sha256'], 'frozen_md_sha256':locked['frozen_md_sha256'],
                                  'request_summary':{'visible_payload_sha256':__import__('harness_common').digest(canonical(__import__('visible_input').packet(case)))},
                                  'usage':None, 'usage_source':'not_applicable', 'elapsed_seconds':0,
                                  **evaluate_case(case, root.parent, mock=True)})
                        else:
                            observe(case, group, model, client, repeat, locked, emit, root)
            attempts = [r for r in records if r['record_type']=='attempt']
            observations = [r for r in records if r['record_type']=='observation']
            write_json(directory / 'summary.json', {'run_id':rid, 'mode':mode, 'group':group, 'model':model['name'],
                'plan_sha256':locked['plan_sha256'], 'frozen_md_sha256':locked['frozen_md_sha256'],
                'observations':len(observations), 'calls':len(attempts), 'api_calls':len(attempts) if mode=='api' else 0,
                'parse_errors':sum(r['status']=='parse_error' for r in observations),
                'input_token_estimate_sum':sum(r['request_summary']['input_estimate']['proxy'] for r in attempts),
                'input_token_upper_sum':sum(r['request_summary']['input_estimate']['upper'] for r in attempts),
                'average_initial_input_proxy':sum(r['request_summary']['input_estimate']['proxy'] for r in attempts if r['attempt']==0) / max(1,len(observations)),
                'average_all_call_input_proxy':sum(r['request_summary']['input_estimate']['proxy'] for r in attempts) / max(1,len(attempts)),
                'output_tokens_provider':sum(r['usage']['completion_tokens'] for r in attempts if r.get('usage') and 'completion_tokens' in r['usage']) if attempts and all(r.get('usage') for r in attempts) else None,
                'usage_warning':'mock usage unavailable; estimates are not provider billed tokens' if mode=='mock' else 'missing provider usage remains null'})
            paths.append(directory.relative_to(root).as_posix())
            print(f'{mode} {group} {model["name"]}: {len(observations)} observations, {len(attempts)} calls')
    write_json(root / ('MOCK_RUNS.json' if mode=='mock' else 'API_RUNS.json'),
               {'mode':mode, 'plan_sha256':locked['plan_sha256'], 'runs':paths})
    return paths


def execute(root=BENCH, mode='mock'):
    locked = verify(root)
    if mode == 'api':
        approval(root, locked)
    with exclusive_api_run(root) if mode == 'api' else nullcontext():
        return execute_unlocked(root, mode)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--mode', choices=['mock','api'], default='mock')
    args = parser.parse_args()
    execute(mode=args.mode)
