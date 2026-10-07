"""Second-round Linux A execution. Standalone package, public inputs only."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from transfer import manifest, verify, write_json, sha256
from visible_input import packet
from rule_adapter import evaluate_case


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def versions():
    result = {'python':sys.version, 'platform':platform.platform()}
    for name in ['bash', 'awk', 'samtools', 'diamond']:
        path = shutil.which(name)
        if not path:
            result[name] = {'available':False}
            continue
        try:
            proc = subprocess.run([path, '--version'], capture_output=True, encoding='utf-8', errors='replace', timeout=10)
            text = (proc.stdout + proc.stderr).splitlines()[:3]
        except Exception as exc:
            text = [type(exc).__name__]
        result[name] = {'available':True, 'path':path, 'version_output':text}
    return result


def execute(package=PACKAGE, bench=None):
    verify(package)
    plan = json.loads((package / 'SERVER_PLAN.json').read_text(encoding='utf-8'))
    bench = bench or package.parent
    bench = bench.resolve(strict=True)
    repo = bench.parent
    if not (repo / 'scripts/run_pitfall_checks.py').is_file():
        raise ValueError('run package must be inside the server repository bench directory')
    out = (bench / plan['output_root']).resolve()
    allowed = (bench / 'bench_transfer').resolve()
    if allowed not in out.parents or package == out or package in out.parents:
        raise ValueError('output must stay inside bench/bench_transfer and outside input package')
    if any(p.is_symlink() for p in [out, *out.parents]):
        raise ValueError('symlink output path forbidden')
    out.mkdir(parents=True, exist_ok=True)
    gaps = []
    for name, expected in plan['rule_sources'].items():
        p = repo / name
        if not p.is_file() or hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest() != expected:
            gaps.append('rule source identity differs: ' + name)
    for name, expected in plan['adapter_files'].items():
        if sha256(package / name) != expected:
            gaps.append('adapter identity differs: ' + name)
    for row in plan['cases']:
        case = package / 'cases' / row['case_id']
        for name, expected in row['public_files'].items():
            if sha256(case / name) != expected:
                gaps.append('public input identity differs: ' + row['case_id'] + '/' + name)
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%dT%H%M%S%f+0800')
    rid = stamp + '_rules_A_' + plan['frozen_md_sha256'][:12]
    rows = []
    # Fixed output files are replaced on repeat execution, never append stale observations.
    with (out / 'records.jsonl').open('wb') as stream:
        if not gaps:
            for row in plan['cases']:
                case = package / 'cases' / row['case_id']
                payload_sha = hashlib.sha256(canonical(packet(case))).hexdigest()
                if payload_sha != row['visible_payload_sha256']:
                    raise ValueError('serialized public payload differs')
                for repeat in range(1, plan['repetitions'] + 1):
                    start = time.perf_counter()
                    try:
                        result = evaluate_case(case, repo)
                    except Exception as exc:
                        result = {'status':'execution_error', 'parsed':None, 'checks':[], 'error':type(exc).__name__}
                    record = {'record_type':'observation', 'mode':'rules', 'simulated':False, 'case_id':case.name,
                              'repetition':repeat, 'group':'A', 'model':'rules', 'run_id':rid,
                              'plan_sha256':plan['plan_sha256'], 'frozen_md_sha256':plan['frozen_md_sha256'],
                              'request_summary':{'visible_payload_sha256':payload_sha},
                              'usage':None, 'usage_source':'not_applicable', 'elapsed_seconds':time.perf_counter()-start,
                              **result}
                    stream.write(canonical(record)); stream.flush(); rows.append(record)
    write_json(out / 'versions.json', versions())
    write_json(out / 'identity.json', {'plan_sha256':plan['plan_sha256'], 'frozen_md_sha256':plan['frozen_md_sha256'],
                                     'rule_sources':plan['rule_sources'], 'adapter_files':plan['adapter_files'],
                                     'input_manifest_sha256':sha256(package / 'MANIFEST.json')})
    status = {'status':'blocked' if gaps else 'complete', 'gaps':gaps, 'observations':len(rows),
              'counts':dict(Counter(r['status'] for r in rows)), 'run_id':rid,
              'plan_sha256':plan['plan_sha256'], 'frozen_md_sha256':plan['frozen_md_sha256'], 'api_calls':0}
    write_json(out / 'STATUS.json', status)
    (out / 'run.log').write_bytes((json.dumps(status, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8'))
    manifest(out)
    print(f'{status["status"].upper()}: {len(rows)} A observations; 0 API calls; {status["counts"]}')
    print('Bundle: ' + str(out))
    print('MANIFEST.json SHA-256: ' + sha256(out / 'MANIFEST.json'))
    for gap in gaps:
        print('GAP ' + gap)
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--bench-root', type=Path)
    args = parser.parse_args()
    execute(bench=args.bench_root)
