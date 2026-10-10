"""Prepare and mock T1 regression tasks through native Inspect. No live entry point.

Legacy v2 answers/schema stay unchanged. This is a seen regression condition,
not a held-out test and not a re-scoring of earlier model runs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path

from bench.inspect_adapter import bridge, pilot
from bench.inspect_adapter.readonly import PublicFiles, inspect_tools
from bench.v2.runtime import V2, canonical, digest, packet, read_json, token_estimate, write_json

ROOT = Path(__file__).resolve().parent
DIRECTORY = ROOT / 't1_regression'
CONDITIONS = ('inline', 'tools')
CASE_IDS = tuple(sorted([f'regression_{i:03d}' for i in range(1, 17) if i != 13] +
                        ['new_017', 'new_018', 'new_021', 'new_022', 'new_023']))


def inventory():
    report = bridge.archive()
    rows = []
    for cid in CASE_IDS:
        case = V2 / 'cases' / cid
        meta = read_json(case / 'meta.json')
        cohorts = sorted({s['cohort'] for s in meta['source_files']})
        if len(cohorts) != 1 or not cohorts[0].startswith('T1_'):
            raise ValueError('T1 selection contains another source')
        row = {'case_id': cid, 'source_group': cohorts[0], 'stage': meta['stage'],
               'type': meta['type'], 'pair_id': meta.get('pair_id'),
               'expected_sha256': digest((case / 'expected.json').read_bytes()),
               'meta_sha256': digest((case / 'meta.json').read_bytes())}
        if read_json(case / 'expected.json') != report['cases'][cid]['expected']:
            raise ValueError('legacy answer changed')
        try:
            files = PublicFiles(case)
        except UnicodeDecodeError:
            if cid != 'regression_002':
                raise ValueError('unexpected nontext T1 case') from None
            row.update(status='not_supported', reason='binary gzip; existing tools accept UTF-8 only')
        else:
            row.update(status='eligible', reason='', public_manifest=files.manifest())
        rows.append(row)
    return rows


def messages(case_id, condition):
    """Only public bytes plus the shared, unchanged output schema enter messages."""
    if case_id not in CASE_IDS or case_id == 'regression_002' or condition not in CONDITIONS:
        raise ValueError('unsupported case or condition')
    files = PublicFiles(V2 / 'cases' / case_id)
    system = (DIRECTORY / 'system.txt').read_text(encoding='utf-8')
    schema = read_json(V2 / 'schemas/model_output.schema.json')
    if condition == 'tools':
        content = {'task': files.text('task.md'), 'files': files.manifest()}
    else:
        content = packet(V2 / 'cases' / case_id)
    return [{'role': 'system', 'content': system + '\n' + canonical(schema).decode('utf-8')},
            {'role': 'user', 'content': canonical(content).decode('utf-8')}]


def draft_plan():
    rows = inventory()
    eligible = [r['case_id'] for r in rows if r['status'] == 'eligible']
    base = pilot.draft_plan()
    repeats, rounds = 3, 5
    per_condition = len(eligible) * repeats
    output_cap = per_condition * (rounds * 512 + 2 * 2048)
    initial = {condition: {cid: token_estimate({'messages': messages(cid, condition)})
                           for cid in eligible} for condition in CONDITIONS}
    return {'version': 'inspect-t1-regression-draft-1', 'split': 'seen_regression',
            'legacy_answer_policy': 'exact v2 answer values/bytes and six-field output schema; no v3 conversion',
            'candidate_case_ids': list(CASE_IDS), 'case_ids': eligible, 'inventory': rows,
            'conditions': list(CONDITIONS), 'repetitions': repeats,
            'planned_observations': 2 * per_condition, 'case_counts': {'candidates': len(rows),
                'eligible': len(eligible), 'not_supported': len(rows) - len(eligible)},
            'source_case_counts': dict(Counter(r['source_group'] for r in rows)),
            'eligible_source_case_counts': dict(Counter(r['source_group'] for r in rows if r['status'] == 'eligible')),
            'model_id': base['model_id'], 'base_url': base['base_url'], 'key_env': base['key_env'],
            'temperature': 0, 'extra_body': {'enable_thinking': False},
            'evidence_rounds_max': rounds, 'evidence_max_tokens': 512, 'final_max_tokens': 2048,
            'max_http_requests_proposed': per_condition * (rounds + 2),
            'max_input_proxy_tokens_proposed': 2_000_000,
            'max_output_token_reservation_proposed': output_cap,
            'timeout_seconds': 60, 'concurrency': 1, 'automatic_retries': 0,
            'initial_input_estimates': initial,
            'price_snapshot_reference': base['price'],
            'proposed_uncached_reference_cost_cny': (2_000_000 * 3 + output_cap * 9) / 1_000_000,
            'api_call_authorized': False, 'new_answers_assigned': False,
            'causal_scope': 'information-access conditions; inline gives all public text, tools gives index then tools; input length differs',
            'grading_scope': 'legacy verdict/root/schema-filename labels; evidence semantics and action safety not automatically adjudicated',
            'source_hashes': {name: digest(path.read_bytes()) for name, path in {
                't1_regression.py': Path(__file__), 'readonly.py': ROOT / 'readonly.py',
                'bridge.py': ROOT / 'bridge.py', 'system.txt': DIRECTORY / 'system.txt',
                'final.txt': DIRECTORY / 'final.txt', 'v2/FROZEN.md': V2 / 'FROZEN.md',
                'v2/model_output.schema.json': V2 / 'schemas/model_output.schema.json',
                'legacy_report': bridge.REFERENCE}.items()}}


def save_draft(path, data):
    if path.exists() and path.read_bytes() != data:
        raise ValueError('existing draft differs; use a new version instead of overwrite')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def prepare():
    plan = draft_plan()
    save_draft(DIRECTORY / 'PLAN.draft.json', canonical(plan) + b'\n')
    targets = {cid: read_json(V2 / 'cases' / cid / 'expected.json') for cid in CASE_IDS}
    save_draft(DIRECTORY / 'LEGACY_TARGETS.json', canonical(targets) + b'\n')
    buffer = io.StringIO(newline='')
    names = ['case_id', 'source_group', 'stage', 'type', 'pair_id', 'status', 'reason', 'expected_sha256']
    writer = csv.DictWriter(buffer, fieldnames=names, lineterminator='\n', extrasaction='ignore')
    writer.writeheader()
    writer.writerows(plan['inventory'])
    save_draft(DIRECTORY / 'CASE_INVENTORY.csv', buffer.getvalue().encode('utf-8'))
    print(f"PREPARED: {len(CASE_IDS)} T1 candidates, {len(plan['case_ids'])} eligible; 0 API calls")
    return plan


def checked_plan():
    plan = read_json(DIRECTORY / 'PLAN.draft.json')
    if plan != draft_plan():
        raise ValueError('draft inputs, answers, implementation or prompts changed')
    targets = read_json(DIRECTORY / 'LEGACY_TARGETS.json')
    if targets != {cid: read_json(V2 / 'cases' / cid / 'expected.json') for cid in CASE_IDS}:
        raise ValueError('legacy target copy changed')
    return plan


def make_task(plan, condition):
    from inspect_ai import Task
    from inspect_ai.dataset import Sample
    from inspect_ai.model import ChatMessageSystem, ChatMessageUser
    from inspect_ai.scorer import Score, scorer, mean
    from inspect_ai.solver import solver, use_tools
    if condition not in CONDITIONS:
        raise ValueError('unregistered condition')
    public = {cid: PublicFiles(V2 / 'cases' / cid) for cid in plan['case_ids']}
    samples = []
    for cid in plan['case_ids']:
        target = canonical(read_json(V2 / 'cases' / cid / 'expected.json')).decode('utf-8')
        for rep in range(1, plan['repetitions'] + 1):
            samples.append(Sample(id=f'{cid}:r{rep}', input=[
                ChatMessageSystem(content=m['content']) if m['role'] == 'system'
                else ChatMessageUser(content=m['content']) for m in messages(cid, condition)],
                target=target, metadata={'case_id': cid, 'repetition': rep,
                    'split': 'seen_regression', 'condition': condition}))
    final = (DIRECTORY / 'final.txt').read_text(encoding='utf-8')

    @solver
    def collect_submit():
        async def solve(state, generate):
            if condition == 'tools':
                state = await use_tools(inspect_tools(public[state.metadata['case_id']]))(state, generate)
                for _ in range(plan['evidence_rounds_max']):
                    state = await generate(state, tool_calls='single', max_tokens=512,
                                           extra_body=plan['extra_body'])
                    if state.completed:
                        return state
                    if not state.output.message.tool_calls:
                        break
            state.tools = []
            state.tool_choice = 'none'
            state.messages.append(ChatMessageUser(content=final))
            state.metadata['final_submission_scheduled'] = True
            return await generate(state, tool_calls='none', max_tokens=2048,
                extra_body={**plan['extra_body'], 'response_format': {'type': 'json_object'}})
        return solve

    @scorer(metrics={name: [mean()] for name in
            ('verdict_correct', 'root_correct', 'joint_correct', 'valid_output')})
    def legacy_labels():
        async def score(state, target):
            try:
                parsed, values = bridge.evaluate_output('ok', state.output.completion,
                                                       state.metadata['case_id'], json.loads(target.text))
            except ValueError:
                parsed = None
                values = dict.fromkeys(('verdict_correct', 'root_correct', 'joint_correct', 'valid_output'), 0)
            return Score(value=values, answer=json.dumps(parsed, ensure_ascii=False),
                         explanation='Unchanged legacy labels; no evidence-semantic or action-safety adjudication.')
        return score
    return Task(name='t1_regression_' + condition, version=plan['version'], dataset=samples,
                solver=collect_submit(), scorer=legacy_labels(), epochs=1,
                turn_limit=6, time_limit=480, score_on_error=True, continue_on_fail=True,
                metadata={'split': 'seen_regression', 'legacy_answer_schema': True})


def mock():
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log
    from inspect_ai.model import GenerateConfig, ModelOutput, ChatMessageAssistant, get_model
    from inspect_ai.tool import ToolCall
    plan = checked_plan()
    calls, receipts = [], []
    for condition in CONDITIONS:
        def response(messages, tools, tool_choice, config):
            # Only visible messages influence scripted probes; no target/meta read.
            body = {'messages': [{'role': m.role, 'content': m.text} for m in messages],
                    'tools': [str(t) for t in tools]}
            calls.append({'condition': condition, 'input_proxy': token_estimate(body)['proxy'],
                          'output_reserved': config.max_tokens})
            content = json.loads(messages[1].text)
            if tools and not any(m.role == 'tool' for m in messages):
                path = next(f['path'] for f in content['files'] if f['path'].startswith('artifacts/'))
                return ModelOutput.from_message(ChatMessageAssistant(content='', tool_calls=[
                    ToolCall(id=f'fixture-read-{len(calls)}', function='read_file', arguments={'path': path}),
                    ToolCall(id=f'fixture-stat-{len(calls)}', function='file_stats', arguments={'path': path})]),
                    model='mockllm/model', stop_reason='tool_calls')
            if tools:
                return ModelOutput.from_content('mockllm/model', 'Offline evidence fixture complete.')
            return ModelOutput.from_content('mockllm/model', json.dumps({'verdict': 'pass', 'root_cause': 'none',
                'evidence': ['task.md:1'], 'action': 'Offline fixture only; not a biological recommendation.',
                'proposes_threshold_relaxation': False, 'proposes_skipping_check': False}))
        model = get_model('mockllm/model', custom_outputs=response, memoize=False,
                          config=GenerateConfig(temperature=0, max_tokens=2048, max_retries=0))
        output = ROOT / 'work/t1_regression_mock' / condition
        logs = inspect_eval(make_task(plan, condition), model=model, display='none',
            log_dir=str(output / 'logs'), log_format='json', max_samples=1, max_tasks=1,
            retry_on_error=0, max_retries=0)
        if len(logs) != 1 or logs[0].status != 'success':
            raise ValueError('native Inspect mock failed')
        log = read_eval_log(logs[0].location)
        wanted = {(cid, rep) for cid in plan['case_ids'] for rep in (1, 2, 3)}
        slots = [(s.metadata['case_id'], s.metadata['repetition']) for s in log.samples]
        if len(slots) != len(wanted) or set(slots) != wanted or any(s.error for s in log.samples):
            raise ValueError('mock omitted or repeated a planned slot')
        replies = [m for s in log.samples for m in s.messages if m.role == 'tool']
        if any(m.error for m in replies) or len(replies) != (2 * len(wanted) if condition == 'tools' else 0):
            raise ValueError('native tool fixture failed')
        if any(not s.metadata.get('final_submission_scheduled') or
               next(iter(s.scores.values())).value['valid_output'] != 1 for s in log.samples):
            raise ValueError('final legacy schema path failed')
        receipts.append({'condition': condition, 'samples': len(slots), 'actual_tool_calls': len(replies),
                         'schema_filename_valid': len(slots), 'errors': 0})
    result = {'status': 'pass', 'plan_sha256': digest((DIRECTORY / 'PLAN.draft.json').read_bytes()),
              'unique_eligible_cases': len(plan['case_ids']), 'candidate_case_coverage': '19/20',
              'provider_calls': 0, 'model_quality_measured': False, 'mock_responses_are_scripted': True,
              'conditions': receipts, 'native_mock_generate_calls': len(calls),
              'mock_input_proxy_sum': sum(c['input_proxy'] for c in calls),
              'mock_output_reservations': sum(c['output_reserved'] for c in calls),
              'mock_estimate_scope': 'text plus tool descriptions proxy; not provider usage or live call prediction',
              'not_supported': [r for r in plan['inventory'] if r['status'] == 'not_supported']}
    write_json(ROOT / 'work/t1_regression_mock/RECEIPT.json', result)
    print(f"PASS: {len(plan['case_ids'])} T1 cases, {sum(r['samples'] for r in receipts)} mock observations; 0 API calls")
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--prepare', action='store_true')
    choice.add_argument('--mock', action='store_true')
    args = parser.parse_args()
    prepare() if args.prepare else mock()
