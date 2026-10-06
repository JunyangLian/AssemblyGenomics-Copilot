"""Second stage, offline Linux replay. Does not run A or any model."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import platform
import sys
import traceback
import zlib

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BENCH))
from build_cases import build
from inject.common import Sources, digest, json_bytes
from transfer import manifest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bundle',type=Path,default=BENCH/'bench_transfer/v1_prepare_t1t3_r3/bundle')
    parser.add_argument('--receipt',type=Path,default=BENCH/'server/source_receipt.json')
    parser.add_argument('--reference',type=Path,default=BENCH/'CASE_INPUTS.json')
    parser.add_argument('--output-root',type=Path,default=BENCH/'bench_transfer/v1_cases_reproduction')
    args=parser.parse_args()
    output=args.output_root.resolve()
    allowed=(BENCH/'bench_transfer').resolve()
    if allowed not in output.parents or output == allowed:
        raise SystemExit('output must be a dedicated directory under bench/bench_transfer')
    if args.bundle.resolve() in output.parents or output in args.bundle.resolve().parents:
        raise SystemExit('output cannot overlap source bundle')
    bundle=output/'bundle'; bundle.mkdir(parents=True,exist_ok=True)
    report={'status':'fail','model_calls':0,'answers_frozen':False,'original_source_hash_rescans':0}
    lines=[]
    try:
        src=Sources(args.bundle,args.receipt)
        reference=json.loads(args.reference.read_text(encoding='utf-8'))
        actual,_=build(src,bundle/'cases',BENCH/'context/skill_context.md')
        (bundle/'REPRODUCED_INPUTS.json').write_bytes(json_bytes(actual))
        errors=[]
        if actual != reference:
            if actual['source_manifest_sha256'] != reference['source_manifest_sha256']: errors.append('source manifest differs')
            if actual['context_sha256'] != reference['context_sha256']: errors.append('shared context differs')
            for original,current in zip(reference['cases'],actual['cases']):
                if original != current: errors.append(original['case_id'] + ': task/artifact/answer/label hash differs')
            if len(reference['cases']) != len(actual['cases']): errors.append('case count differs')
            if not errors: errors.append('input reference metadata differs')
        report.update({'status':'pass' if not errors else 'fail','errors':errors,'case_count':len(actual['cases']),
                       'source_manifest_sha256':actual['source_manifest_sha256'],'context_sha256':actual['context_sha256'],
                       'comparison':'Every task/artifact/expected byte hash and private label compared with Windows reference. Absolute local source paths in meta differ by host; source manifest, role and origin bindings retained.'})
        lines.append(f"{report['status'].upper()}: {len(actual['cases'])} cases, {len(errors)} differences")
        lines.extend(errors)
    except Exception as error:
        report['errors']=[str(error)]
        lines.append(traceback.format_exc())
    versions={'python':platform.python_version(),'platform':platform.platform(),
              'zlib_compiled':zlib.ZLIB_VERSION,'zlib_runtime':zlib.ZLIB_RUNTIME_VERSION,
              'external_tools':'not invoked; Python only'}
    code=[BENCH/'build_cases.py',BENCH/'visible_input.py',BENCH/'transfer.py',Path(__file__).resolve(),
          *sorted((BENCH/'inject').glob('*.py'))]
    versions['code_sha256']={p.relative_to(BENCH).as_posix():digest(p.read_bytes()) for p in code}
    (bundle/'versions.json').write_bytes(json_bytes(versions))
    (bundle/'RESULT.json').write_bytes(json_bytes(report))
    (bundle/'reproduction.log').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
    manifest(bundle)
    print('\n'.join(lines))
    print('Bundle:',bundle)
    print('MANIFEST.json SHA-256:',digest((bundle/'MANIFEST.json').read_bytes()))
    print('No API calls, A rules, or original-source hash rescans.')
    raise SystemExit(0 if report['status']=='pass' else 1)


if __name__=='__main__': main()
