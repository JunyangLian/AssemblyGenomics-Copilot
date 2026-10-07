"""Lock v2 public inputs, implementation and proposed transport independently of v1."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import re
import yaml
from bench.v2.runtime import (V2, BENCH, REPO, SYSTEM, REPAIR, canonical, digest,
                              read_json, write_json, safe_url, visible_files, packet, rules)
from bench.v2.freeze import verify as frozen_verify, ROSTER
from rule_adapter import RULE_MAP

IMPLEMENTATION = ['runtime.py', 'plan.py', 'adapter.py', 'run.py', 'mock_report.py',
                  'rules_package.py', 'import_rules.py', 'server/run_rules.py', 'models.yaml']
SHARED = ['harness_common.py', 'model_adapter.py', 'rule_adapter.py', 'visible_input.py', 'transfer.py']


def models(root=V2):
    doc = yaml.safe_load((root / 'models.yaml').read_text(encoding='utf-8'))
    if set(doc) != {'models'}:
        raise ValueError('model configuration cannot contain credentials or unregistered fields')
    result = doc['models']
    original_names = read_json(root / 'MODEL_AUTHORIZATION.json')['authorized_model_names']
    names = original_names
    provider_file = 'PROVIDER_MODELS.json'
    amendment_path = root / 'MODEL_ROSTER_REVISION.json'
    if amendment_path.exists():
        amendment = read_json(amendment_path)
        if (amendment.get('user_authorized') is not True or not amendment.get('user_quote')
            or amendment.get('previous_model_names') != original_names
            or amendment.get('frozen_md_sha256') != digest((root / 'FROZEN.md').read_bytes())
            or amendment.get('preregistration_sha256') != digest((root / 'preregistration.json').read_bytes())
            or amendment.get('post_start') is not True
            or amendment.get('thresholds_changed') is not False
            or amendment.get('provider_metadata_file') != 'PROVIDER_MODELS_ROSTER2.json'):
            raise ValueError('invalid explicit roster amendment; frozen authorization cannot be overwritten')
        names = amendment['model_names']
        if (set(original_names) - set(names) != {'Kimi-K2.6'}
            or set(names) - set(original_names) != {'GLM-5.3'} or len(names) != 5):
            raise ValueError('only the human-requested Kimi to GLM substitution is authorized')
        provider_file = amendment['provider_metadata_file']
    vision_path = root / 'VISION_MODEL_REVISION.json'
    vision = read_json(vision_path) if vision_path.exists() else None
    if vision:
        if (vision.get('user_authorized') is not True or not vision.get('user_quote')
            or vision.get('previous_model_names') != names
            or vision.get('frozen_md_sha256') != digest((root / 'FROZEN.md').read_bytes())
            or vision.get('preregistration_sha256') != digest((root / 'preregistration.json').read_bytes())
            or vision.get('post_start') is not True or vision.get('thresholds_changed') is not False
            or vision.get('provider_metadata_file') != 'PROVIDER_MODELS_VISION.json'
            or vision.get('request_model_id') != 'deepseek-v4-flash-vision'
            or vision.get('accepted_response_ids') != ['deepseek-v4-flash-vision', 'DeepSeek-V4-Flash-Vision', 'dsv4-flash-vision']):
            raise ValueError('invalid explicit Vision replacement; no implicit model or alias fallback')
        replacements = ['DeepSeek-V4-Flash-Vision' if n == 'DeepSeek-V4-Flash-0731' else n for n in names]
        if vision.get('model_names') != replacements:
            raise ValueError('only the human-requested Flash Vision replacement is authorized')
        names, provider_file = replacements, vision['provider_metadata_file']
    # The authorization stores the display names as strings.
    if [m['name'] for m in result] != names:
        raise ValueError('model roster differs from human authorization')
    provider = read_json(root / provider_file)
    if provider['source'] != 'https://discovery-api.intern-ai.org.cn/v1/models':
        raise ValueError('provider mapping must come from the authorized model-list endpoint')
    official = {m['name']: m['id'] for m in provider['models']}
    for m in result:
        fields = {'name', 'requested_model_id', 'base_url', 'key_env', 'parameters', 'thinking_status', 'price'}
        if vision and m['name'] == 'DeepSeek-V4-Flash-Vision':
            fields.add('accepted_response_ids')
            if m.get('accepted_response_ids') != vision['accepted_response_ids']:
                raise ValueError('Vision response identities differ from explicit human replacement')
        if set(m) != fields:
            raise ValueError('unsupported configuration field; keys must stay in environment')
        if m['requested_model_id'] != official.get(m['name']):
            raise ValueError('request ID does not match exact official display-name mapping')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', m['name']):
            raise ValueError('invalid model ID')
        if safe_url(m['base_url']) != 'https://discovery-api.intern-ai.org.cn/v1':
            raise ValueError('endpoint differs from authorized endpoint')
        if m['key_env'] != 'INTERN_DISCOVERY_API_KEY':
            raise ValueError('unregistered key environment name')
        if m['parameters'] != {'temperature': 0, 'max_tokens': 8192}:
            raise ValueError('parameters differ from proposed common protocol')
        if m['thinking_status'] != 'provider_default_unknown' or m['price'] is not None:
            raise ValueError('provider thinking and price require a registered plan revision')
    return result


def public_cases(root=V2):
    return [{'case_id': n, 'public_files': {p.relative_to(root / 'cases' / n).as_posix():
            digest(p.read_bytes()) for p in visible_files(root / 'cases' / n)},
            'visible_payload_sha256': digest(canonical(packet(root / 'cases' / n)))} for n in ROSTER]


def prepare(root=V2):
    if (root / 'RUN_PLAN.json').exists():
        return verify(root)
    frozen_verify(root)
    from bench.v2.import_rules import reuse_identity
    plan = {'version': 'v2-run-1', 'frozen_md_sha256': digest((root / 'FROZEN.md').read_bytes()),
            'models': models(root), 'groups': ['B', 'C2'], 'repetitions': 3, 'parse_retries': 1,
            'mock_seed': 20261007, 'system_prompt': SYSTEM, 'repair_prompt': REPAIR,
            'cases': public_cases(root), 'rule_sources': rules(), 'rule_mapping': RULE_MAP,
            'a_reuse': reuse_identity(root),
            'implementation': {n: digest((root / n).read_bytes()) for n in IMPLEMENTATION},
            'shared_implementation': {n: digest((BENCH / n).read_bytes()) for n in SHARED},
            'provider_policy': {'live_parameters_review_pending': True, 'thinking': 'provider_default_unknown',
                'model_ids': 'user supplied, no authenticated probe', 'no_parameter_or_alias_fallback': True,
                'timeout_seconds': 300, 'network_retries': 0, 'response_limit_bytes': 16777216},
            'input_policy': 'task.md + artifacts only; identical C2 for all models; no tools or private metadata',
            'analysis': 'frozen preregistration.json; mock excluded; majority case is primary; failures retained',
            'api_budget': 'separate API_APPROVAL.json required; cumulative v2 runs/API_LEDGER.json; no v1 reset'}
    write_json(root / 'RUN_PLAN.json', plan)
    (root / 'RUN_PLAN.sha256').write_bytes((digest(canonical(plan)) + '\n').encode('ascii'))
    return verify(root)


def verify(root=V2):
    frozen_verify(root)
    path = root / 'RUN_PLAN.json'
    data, plan = path.read_bytes(), read_json(path)
    if data != canonical(plan) or digest(data) != (root / 'RUN_PLAN.sha256').read_text().strip():
        raise ValueError('v2 run plan hash mismatch')
    if digest((root / 'FROZEN.md').read_bytes()) != plan['frozen_md_sha256']:
        raise ValueError('v2 frozen identity mismatch')
    for names, base in [('implementation', root), ('shared_implementation', BENCH)]:
        for name, expected in plan[names].items():
            if digest((base / name).read_bytes()) != expected:
                raise ValueError('implementation changed after plan lock: ' + name)
    if models(root) != plan['models'] or public_cases(root) != plan['cases']:
        raise ValueError('configuration or public cases changed after lock')
    if rules() != plan['rule_sources'] or RULE_MAP != plan['rule_mapping']:
        raise ValueError('original rules or mapping changed')
    from bench.v2.import_rules import reuse_identity
    if reuse_identity(root) != plan['a_reuse']:
        raise ValueError('v1 A reuse provenance changed')
    return {'plan': plan, 'plan_sha256': digest(data), 'frozen_md_sha256': plan['frozen_md_sha256']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--create', action='store_true')
    args = p.parse_args(); result = prepare() if args.create else verify()
    print('PASS: ' + result['plan']['version'] + '; SHA-256: ' + result['plan_sha256'])
