"""Pure-Python Linux replay; no rules, models, credentials or original source scans."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import platform
import sys
import traceback

BENCH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BENCH))
from inject.common import Sources, digest, json_bytes
from transfer import manifest
from v2.build_cases import build, context_bytes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, default=BENCH / 'bench_transfer/v1_prepare_t1t3_r3/bundle')
    parser.add_argument('--receipt', type=Path, default=BENCH / 'v2/server/source_receipt.json')
    parser.add_argument('--output-root', type=Path, default=BENCH / 'bench_transfer/v2_cases_reproduction')
    args = parser.parse_args()
    output = args.output_root.resolve()
    allowed = (BENCH / 'bench_transfer').resolve()
    if allowed not in output.parents or output == allowed:
        raise SystemExit('output must be a dedicated directory under bench/bench_transfer')
    if output in args.bundle.resolve().parents or args.bundle.resolve() in output.parents or output == args.bundle.resolve():
        raise SystemExit('output cannot overlap source bundle')
    bundle = output / 'bundle'; bundle.mkdir(parents=True, exist_ok=True)
    report = {'status':'fail', 'model_calls':0, 'answers_frozen':False, 'original_source_hash_rescans':0}
    lines = []
    try:
        package = json.loads((BENCH / 'v2/server/PACKAGE_CONTENTS.json').read_bytes())
        for row in package['files']:
            relative = Path(row['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('package contains invalid relative path')
            path = BENCH / relative
            if path.is_symlink() or path.stat().st_size != row['size_bytes'] or digest(path.read_bytes()) != row['sha256']:
                raise ValueError('transferred replay file differs: ' + row['path'])
        reference = json.loads((BENCH / 'v2/CASE_INPUTS.json').read_bytes())
        actual = build(Sources(args.bundle, args.receipt), bundle / 'cases')
        (bundle / 'REPRODUCED_INPUTS.json').write_bytes(json_bytes(actual))
        errors = []
        if actual != reference:
            previous = {r['case_id']:r for r in reference['cases']}
            for row in actual['cases']:
                if row != previous.get(row['case_id']): errors.append(row['case_id'] + ': reconstruction hash/label differs')
            if not errors: errors.append('roster, source or context identity differs')
        if (BENCH / 'v2/context/skill_context.md').read_bytes() != context_bytes(): errors.append('C2 bytes differ')
        report.update({'status':'fail' if errors else 'pass', 'case_count':len(actual['cases']), 'errors':errors,
                       'source_manifest_sha256':actual['source_manifest_sha256'], 'context_sha256':actual['context_sha256'],
                       'comparison':'Every task/artifact/expected/label byte hash plus portable metadata hash. Only accepted-bundle absolute prefix is normalized; source origin paths and all other metadata are retained.'})
        lines.append(f"{report['status'].upper()}: {len(actual['cases'])} cases, {len(errors)} differences")
        lines.extend(errors)
    except Exception as error:
        report['errors'] = [str(error)]; lines.append(traceback.format_exc())
    files = [BENCH / 'v2/build_cases.py', BENCH / 'v2/__init__.py', BENCH / 'visible_input.py', BENCH / 'transfer.py',
             BENCH / 'inject/common.py', BENCH / 'inject/pressure.py', Path(__file__).resolve(),
             *sorted((BENCH / 'v2/inject').glob('*.py'))]
    versions = {'python':platform.python_version(), 'platform':platform.platform(), 'external_tools':'not invoked; Python only',
                'code_sha256':{p.relative_to(BENCH).as_posix():digest(p.read_bytes()) for p in files}}
    (bundle / 'versions.json').write_bytes(json_bytes(versions))
    (bundle / 'RESULT.json').write_bytes(json_bytes(report))
    (bundle / 'reproduction.log').write_bytes(('\n'.join(lines) + '\n').encode())
    manifest(bundle)
    print('\n'.join(lines)); print('Bundle:', bundle)
    print('MANIFEST.json SHA-256:', digest((bundle / 'MANIFEST.json').read_bytes()))
    print('No API calls, A rules, or original-source hash rescans.')
    raise SystemExit(0 if report['status'] == 'pass' else 1)


if __name__ == '__main__': main()
