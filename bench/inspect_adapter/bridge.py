"""Network-free bridge from the archived v2 closeout to Inspect components.

Replay consumes final parsed observations, not original HTTP transcripts. It
does not retry, repair, invent completions or execute the historical A rules.
"""
from __future__ import annotations

import json
from pathlib import Path

from bench.v2.runtime import V2, canonical, digest, read_json, request

REFERENCE = V2 / 'reports/v2-run-10_four-models_human-reviewed/results.json'


def slot_id(group, model, case_id, repetition):
    return f'{group}:{model}:{case_id}:{repetition}'


def archive(path=REFERENCE):
    """Use a published report plus its manifest, never rescan source genomes."""
    path = Path(path).resolve()
    manifest = read_json(path.parent / 'MANIFEST.json')
    data = path.read_bytes()
    if manifest['files'][path.name] != digest(data):
        raise ValueError('archived report differs from its published manifest')
    report = json.loads(data)
    if report['frozen_md_sha256'] != digest((V2 / 'FROZEN.md').read_bytes()):
        raise ValueError('archived report has different frozen answers')
    for cid, case in report['cases'].items():
        if case['expected'] != read_json(V2 / 'cases' / cid / 'expected.json'):
            raise ValueError('archived answer differs from frozen case')
    return report


def final_rows(report):
    """Only the four retained models and A, with every planned repeat present."""
    rows = {}
    for group in report['scored']['groups']:
        for cid, case in group['cases'].items():
            reps = case['observations']
            if sorted(r['repetition'] for r in reps) != [1, 2, 3]:
                raise ValueError('archive lacks a planned repetition')
            for row in reps:
                if row['case_id'] != cid:
                    raise ValueError('archive case identity mismatch')
                key = slot_id(group['group'], group['model'], cid, row['repetition'])
                if key in rows:
                    raise ValueError('duplicate historical observation')
                if row['status'] not in {'ok', 'api_error', 'parse_error', 'interrupted', 'not_covered'}:
                    raise ValueError('unexpected historical status')
                if (row['status'] == 'ok') != isinstance(row['parsed'], dict):
                    raise ValueError('status/parsed contradiction')
                rows[key] = {**row, 'group': group['group'], 'model': group['model']}
    return rows


def public_messages(case_id, group, model, plan=None):
    """Reuse the original input whitelist. No expected/meta/review data here."""
    plan = plan or read_json(V2 / 'RUN_PLAN.json')
    config = next((m for m in plan['models'] if m['name'] == model), None)
    if group == 'A':
        config = {'name': 'rules', 'parameters': {}}
        group = 'B'  # A replay displays the public task; it does not call rules.
    if config is None:
        raise ValueError('unregistered model identity')
    return request(V2 / 'cases' / case_id, group, config)['messages']


def evaluate_output(status, content, case_id, expected):
    """Independent per-observation labels; invalid slots stay in denominators."""
    from bench.v2.runtime import parse_response
    parsed = None
    if status == 'ok':
        parsed, error = parse_response(
            {'choices': [{'message': {'content': content}}]}, V2 / 'cases' / case_id, V2)
        if error:
            raise ValueError('valid replay output failed the legacy parser')
    elif content:
        raise ValueError('failure must not acquire a completion during replay')
    verdict_ok = bool(parsed and parsed['verdict'] in expected['acceptable_verdicts'])
    root_ok = bool(parsed and parsed['root_cause'] == expected['root_cause'])
    return parsed, {'verdict_correct': int(verdict_ok), 'root_correct': int(root_ok),
                    'joint_correct': int(verdict_ok and root_ok), 'valid_output': int(parsed is not None)}


def make_task(report=None):
    """A real Inspect Task with a replay Solver and deterministic Scorer."""
    from inspect_ai import Task
    from inspect_ai.dataset import Sample, MemoryDataset
    from inspect_ai.model import ChatMessageSystem, ChatMessageUser, ModelOutput
    from inspect_ai.scorer import Score, scorer, mean
    from inspect_ai.solver import solver

    report = report or archive()
    rows = final_rows(report)
    plan = read_json(V2 / 'RUN_PLAN.json')
    samples = []
    prompt_cache = {}
    for key, row in rows.items():
        cid = row['case_id']
        identity = (cid, row['group'], row['model'])
        if identity not in prompt_cache:
            prompt_cache[identity] = public_messages(*identity, plan)
        messages = [ChatMessageSystem(content=m['content']) if m['role'] == 'system'
                    else ChatMessageUser(content=m['content']) for m in prompt_cache[identity]]
        samples.append(Sample(
            id=key, input=messages,
            target=canonical(report['cases'][cid]['expected']).decode('utf-8'),
            metadata={'case_id': cid, 'group': row['group'], 'historical_model': row['model'],
                      'historical_repetition': row['repetition'], 'historical_status': row['status']}))

    @solver
    def replay_final_observation():
        async def solve(state, generate):
            # generate is deliberately never called; mockllm is only a label.
            row = rows[str(state.sample_id)]
            content = canonical(row['parsed']).decode('utf-8') if row['status'] == 'ok' else ''
            state.output = ModelOutput.from_content('mockllm/model', content)
            state.completed = True
            return state
        return solve

    @scorer(metrics={key: [mean()] for key in
                     ('verdict_correct', 'root_correct', 'joint_correct', 'valid_output')})
    def genomic_qc_labels():
        async def score(state, target):
            parsed, labels = evaluate_output(
                state.metadata['historical_status'], state.output.completion,
                state.metadata['case_id'], json.loads(target.text))
            return Score(value=labels, answer=json.dumps(parsed, ensure_ascii=False),
                         explanation='Offline historical parsed-output replay; no new inference.',
                         metadata={'historical_status': state.metadata['historical_status']})
        return score

    return Task(name='assemblygenomics_v2_offline_replay', version='1',
                dataset=MemoryDataset(samples), solver=replay_final_observation(),
                scorer=genomic_qc_labels(), epochs=1,
                metadata={'mode': 'offline_parsed_observation_replay', 'provider_calls': 0,
                          'historical_repetitions': 3,
                          'reference_report_sha256': digest(REFERENCE.read_bytes())})
