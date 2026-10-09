"""Run Inspect offline, then compare all v2 case and stratified scores."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from importlib.metadata import version
from pathlib import Path

from bench.inspect_adapter.bridge import (REFERENCE, archive, final_rows, make_task,
                                  evaluate_output, slot_id)
from bench.v2.runtime import V2, canonical, digest, read_json, write_json


def verify_parity(report, log):
    """Reconstruct only from Inspect log outputs, then use frozen aggregation."""
    from bench.v2.score import compute, apply_followup_scope
    source = final_rows(report)
    samples = {str(s.id): s for s in log.samples}
    if len(samples) != len(log.samples) or set(samples) != set(source):
        raise ValueError('Inspect discarded/duplicated a planned observation')
    observations = {}
    for key, original in source.items():
        sample = samples[key]
        if sample.error is not None:
            raise ValueError('Inspect execution failed; do not silently omit a slot')
        metadata = sample.metadata
        wanted = {'case_id': original['case_id'], 'group': original['group'],
                  'historical_model': original['model'],
                  'historical_repetition': original['repetition'],
                  'historical_status': original['status']}
        if metadata != wanted:
            raise ValueError('Inspect metadata changed the historical slot')
        parsed, labels = evaluate_output(original['status'], sample.output.completion,
                                        original['case_id'], report['cases'][original['case_id']]['expected'])
        if parsed != original['parsed']:
            raise ValueError('Inspect changed a historical parsed answer')
        scores = list(sample.scores.values())
        if len(scores) != 1 or scores[0].value != labels:
            raise ValueError('Inspect per-observation scorer disagrees')
        slot = (original['model'], original['group'], original['case_id'], original['repetition'])
        observations[slot] = {**original, 'parsed': parsed}
    coding = {tuple(k.split('|')[:3]) + (int(k.split('|')[3]),): v
              for k, v in report['human_coding'].items()}
    computed = compute(report['cases'], observations, {}, read_json(V2 / 'RUN_PLAN.json'),
                       report['preregistration'], coding)
    computed, _ = apply_followup_scope(computed, report['followup_scope'], report['preregistration'])
    # Token/timing/HTTP diagnostics cannot be inferred from parsed observations.
    # The original report remains their authoritative record.
    mismatches = []
    for section in ('panels', 'mixed_pairs', 'action_coding_diagnostics', 'hypotheses'):
        if computed[section] != report['scored'][section]:
            mismatches.append(section)
    checked_cases = 0
    for actual, expected in zip(computed['groups'], report['scored']['groups']):
        if (actual['group'], actual['model']) != (expected['group'], expected['model']):
            mismatches.append('group_identity')
        for cid, result in actual['cases'].items():
            checked_cases += 1
            for key, value in result.items():
                if key != 'observations' and value != expected['cases'][cid][key]:
                    mismatches.append(f'{actual["group"]}:{actual["model"]}:{cid}:{key}')
    if mismatches:
        raise ValueError('parity failed: ' + ', '.join(mismatches[:15]))
    return {'status': 'pass', 'provider_calls': 0, 'actual_inference_tokens': 0,
            'cost': 0, 'historical_cases': len(report['cases']),
            'replayed_observations': len(source), 'group_case_checks': checked_cases,
            'stratified_panels_checked': len(computed['panels']),
            'mixed_pair_panels_checked': len(computed['mixed_pairs']),
            'historical_status_counts': dict(Counter(r['status'] for r in source.values())),
            'per_observation_scorer_checked': len(samples),
            'majority_policy': 'legacy v2: verdict and root independently need 2/3',
            'excluded_from_parity': ['HTTP attempts', 'token usage', 'timing',
                                     'retired-model audit', 'global original-roster H1 status'],
            'limitations': ['replays archived final parsed outputs, not raw HTTP responses',
                            'aggregation reuses unchanged legacy functions; not an independent scoring implementation',
                            'no new model evidence or biological validation'],
            'inspect_ai_version': version('inspect-ai'),
            'reference_report': REFERENCE.relative_to(V2.parent.parent).as_posix(),
            'reference_report_sha256': digest(REFERENCE.read_bytes())}


def execute(output):
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log
    output = Path(output).resolve()
    allowed = Path(__file__).resolve().parent / 'work'
    if output != allowed and allowed not in output.parents:
        raise ValueError('output must stay inside bench/inspect_adapter/work')
    output.mkdir(parents=True, exist_ok=True)
    report = archive()
    logs = inspect_eval(make_task(report), model='mockllm/model', log_dir=str(output / 'logs'),
                        display='none', log_format='json', max_samples=8)
    if len(logs) != 1 or logs[0].status != 'success':
        raise ValueError('Inspect replay did not complete')
    log = read_eval_log(logs[0].location)
    result = verify_parity(report, log)
    result['inspect_log'] = str(Path(logs[0].location).relative_to(output))
    write_json(output / 'PARITY.json', result)
    print(f"PASS: {result['replayed_observations']} observations; "
          f"{result['stratified_panels_checked']} panels; 0 provider calls")
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'work/v2_replay')
    execute(parser.parse_args().output)
