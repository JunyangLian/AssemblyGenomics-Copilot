"""Standalone Linux A runner; fixed output under bench, original rules only."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
import platform
import shutil
import subprocess
import time
from transfer import manifest, verify, sha256, write_json
from visible_input import packet
from rule_adapter import evaluate_case


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def versions():
    result = {'python': sys.version, 'platform': platform.platform()}
    for tool in ('bash', 'awk', 'samtools', 'diamond'):
        p = shutil.which(tool)
        if not p:
            result[tool] = {'available': False}; continue
        try:
            r = subprocess.run([p, '--version'], capture_output=True, encoding='utf-8', errors='replace', timeout=10)
            text = (r.stdout + r.stderr).splitlines()[:3]
        except Exception as exc:
            text = [type(exc).__name__]
        result[tool] = {'available': True, 'path': p, 'version_output': text}
    return result


def execute(package=PACKAGE, bench=None):
    package = package.resolve(strict=True)
    verify(package)
    plan = json.loads((package / 'SERVER_PLAN.json').read_bytes())
    bench = (bench or package.parents[1]).resolve(strict=True)
    out = (bench / plan['output_root']).resolve()
    allowed = (bench / 'bench_transfer').resolve()
    if allowed not in out.parents or package == out or package in out.parents:
        raise ValueError('output must stay under bench/bench_transfer outside input package')
    if any(p.is_symlink() for p in (out, *out.parents)):
        raise ValueError('symlink output forbidden')
    repo = package / 'original_rules'
    for name, sha in plan['rule_sources'].items():
        if sha256(repo / name) != sha:
            raise ValueError('original rule identity differs: ' + name)
    for name, sha in plan['adapter_files'].items():
        if sha256(package / name) != sha:
            raise ValueError('adapter identity differs')
    for c in plan['cases']:
        case = package / 'cases' / c['case_id']
        if any(sha256(case / n) != s for n, s in c['public_files'].items()):
            raise ValueError('public file identity differs')
        if hashlib.sha256(canonical(packet(case))).hexdigest() != c['visible_payload_sha256']:
            raise ValueError('public serialized packet differs')
    out.mkdir(parents=True, exist_ok=True)
    permitted = {'records.jsonl', 'versions.json', 'identity.json', 'STATUS.json', 'run.log', 'MANIFEST.json', 'MANIFEST.sha256'}
    if any(p.name not in permitted or not p.is_file() for p in out.iterdir()):
        raise ValueError('unexpected file in fixed output directory; choose a clean output path')
    rid = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%dT%H%M%S%f+0800') + '_rules_A_' + plan['frozen_md_sha256'][:12]
    rows = []
    with (out / 'records.jsonl').open('wb') as stream:
        for c in plan['cases']:
            for repeat in range(1, 4):
                start = time.perf_counter()
                try:
                    result = evaluate_case(package / 'cases' / c['case_id'], repo)
                except Exception as exc:
                    result = {'status': 'execution_error', 'parsed': None, 'checks': [], 'error': type(exc).__name__}
                row = {'record_type': 'observation', 'mode': 'rules', 'simulated': False, 'group': 'A', 'model': 'rules',
                    'case_id': c['case_id'], 'repetition': repeat, 'run_id': rid, 'plan_sha256': plan['plan_sha256'],
                    'frozen_md_sha256': plan['frozen_md_sha256'], 'request_summary': {'visible_payload_sha256': c['visible_payload_sha256']},
                    'usage': None, 'usage_source': 'not_applicable', 'elapsed_seconds': time.perf_counter() - start, **result}
                stream.write(canonical(row)); stream.flush(); rows.append(row)
    write_json(out / 'versions.json', versions())
    write_json(out / 'identity.json', {'plan_sha256': plan['plan_sha256'], 'frozen_md_sha256': plan['frozen_md_sha256'],
        'rule_sources': plan['rule_sources'], 'adapter_files': plan['adapter_files'], 'input_manifest_sha256': sha256(package / 'MANIFEST.json')})
    status = {'status': 'complete', 'run_id': rid, 'plan_sha256': plan['plan_sha256'], 'frozen_md_sha256': plan['frozen_md_sha256'],
              'observations': len(rows), 'counts': dict(Counter(r['status'] for r in rows)), 'api_calls': 0}
    write_json(out / 'STATUS.json', status); (out / 'run.log').write_bytes(canonical(status)); manifest(out)
    print('COMPLETE: ' + str(len(rows)) + ' A observations; 0 API calls; ' + str(status['counts']))
    print('Bundle: ' + str(out)); print('MANIFEST.json SHA-256: ' + sha256(out / 'MANIFEST.json'))
    return status


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--bench-root', type=Path)
    args = p.parse_args(); execute(bench=args.bench_root)
