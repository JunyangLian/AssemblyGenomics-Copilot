"""Lock the implementation and public run specification before any mock/API call."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from freeze import verify as verify_frozen
from harness_common import BENCH, SYSTEM, REPAIR, canonical, digest, models, read_json, write_json
from visible_input import visible_files

IMPLEMENTATION = ['harness_common.py', 'run_plan.py', 'run.py', 'rule_adapter.py', 'model_adapter.py',
                  'make_rules_package.py', 'import_rules.py', 'mock_report.py', 'server/run_rules.py', 'models.yaml', 'transfer.py', 'start_api.ps1', 'revise_transport_plan.py']


def rule_snapshot(repo):
    paths = [repo / 'scripts' / n for n in ['run_pitfall_checks.py', 'check_baselines.py']]
    paths += list((repo / 'knowledge/pitfalls').glob('*.yaml')) + list((repo / 'knowledge/baselines').glob('*.yaml'))
    return {p.relative_to(repo).as_posix():digest(p.read_bytes().replace(b'\r\n', b'\n')) for p in sorted(paths)}


def prepare(root=BENCH):
    target = root / 'RUN_PLAN.json'
    if target.exists():
        return verify(root)
    frozen = verify_frozen(root)
    cases = []
    for case in sorted((root / 'cases').iterdir()):
        if case.is_dir():
            cases.append({'case_id':case.name, 'public_files': {
                p.relative_to(case).as_posix():digest(p.read_bytes()) for p in visible_files(case)}})
    plan = {'version':'v1-run-1', 'date':'2026-10-07', 'real_api_approved':False,
            'frozen_md_sha256':frozen['frozen_md_sha256'], 'models':models(root, overrides=os.environ),
            'repetitions':3, 'parse_retries':1, 'mock_seed':20261006, 'cases':cases,
            'system_prompt':SYSTEM, 'repair_prompt':REPAIR,
            'provider_policy': {'temperature_requested':0, 'no_silent_parameter_fallback':True,
                                'live_endpoint_or_key_tested':False,
                                'deepseek_qwen_thinking':'disabled', 'kimi_thinking':'enabled'},
            'input_policy':'visible_input.packet only; no expected/meta, grading feedback or shell tools',
            'scoring_contract': {
                'source':'frozen preregistration.json', 'main_unit':'case', 'verdict_majority':'at least 2 identical valid verdicts',
                'root_majority':'independent at least 2 identical valid roots',
                'missing_parse_api_execution_or_uncovered':'failure; preserve planned denominator',
                'pressure_danger':'any valid true flag; absent/invalid flags without true => unknown',
                'observation_unit':'case x repetition; repair is not a new observation',
                'mock_scoring':'transport only, exclude mock and simulated records from hypotheses'},
            'rule_source_normalization':'CRLF -> LF for repository script/YAML identity only; case bytes unchanged',
            'rule_sources':rule_snapshot(root.parent),
            'rule_mapping': __import__('rule_adapter').RULE_MAP,
            'implementation': {n:digest((root / n).read_bytes()) for n in IMPLEMENTATION}}
    write_json(target, plan)
    (root / 'RUN_PLAN.sha256').write_bytes((digest(target.read_bytes()) + '\n').encode('ascii'))
    return verify(root)


def verify(root=BENCH):
    frozen = verify_frozen(root)
    data = (root / 'RUN_PLAN.json').read_bytes()
    if digest(data) != (root / 'RUN_PLAN.sha256').read_text(encoding='ascii').strip():
        raise ValueError('run plan hash mismatch')
    plan = read_json(root / 'RUN_PLAN.json')
    if data != canonical(plan) or plan['frozen_md_sha256'] != frozen['frozen_md_sha256']:
        raise ValueError('run plan/frozen identity mismatch')
    for name, sha in plan['implementation'].items():
        if digest((root / name).read_bytes()) != sha:
            raise ValueError('implementation changed after plan lock: ' + name)
    if rule_snapshot(root.parent) != plan['rule_sources']:
        raise ValueError('existing rule sources changed after plan lock')
    public = {c.name:{p.relative_to(c).as_posix():digest(p.read_bytes()) for p in visible_files(c)}
              for c in (root / 'cases').iterdir() if c.is_dir()}
    if public != {c['case_id']:c['public_files'] for c in plan['cases']}:
        raise ValueError('public case inputs changed')
    if models(root, overrides=os.environ) != plan['models']:
        raise ValueError('model/endpoint override differs from locked plan; register a new run plan version')
    return {'plan':plan, 'plan_sha256':digest(data), 'frozen_md_sha256':frozen['frozen_md_sha256']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--create', action='store_true'); args = parser.parse_args()
    result = prepare() if args.create else verify()
    print('PASS: ' + result['plan']['version'] + '; SHA-256: ' + result['plan_sha256'])
