"""Accept a transferred Linux replay against the local draft; no model or rule calls."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

V2 = Path(__file__).resolve().parent
BENCH = V2.parent
sys.path.insert(0, str(BENCH))
from inject.common import digest, json_bytes
from transfer import verify
from v2.build_cases import snapshot


def read(path):
    return json.loads(Path(path).read_bytes())


def inspect(bundle, expected_manifest):
    bundle = Path(bundle).resolve(strict=True)
    proof = verify(bundle)
    if proof['manifest_sha256'] != expected_manifest:
        raise ValueError('transfer manifest differs from user-reported server hash')
    reference = read(V2 / 'CASE_INPUTS.json')
    if read(bundle / 'REPRODUCED_INPUTS.json') != reference:
        raise ValueError('server reconstruction reference differs from local draft')
    result = read(bundle / 'RESULT.json')
    required = {'status':'pass', 'errors':[], 'case_count':len(reference['cases']),
                'model_calls':0, 'answers_frozen':False, 'original_source_hash_rescans':0,
                'context_sha256':reference['context_sha256'],
                'source_manifest_sha256':reference['source_manifest_sha256']}
    if any(result.get(k) != v for k,v in required.items()):
        raise ValueError('server result is incomplete or incompatible')
    versions = read(bundle / 'versions.json')
    if not versions.get('platform', '').startswith('Linux-'):
        raise ValueError('reproduction was not reported from Linux')
    code = ['v2/build_cases.py', 'v2/__init__.py', 'visible_input.py', 'transfer.py',
            'inject/common.py', 'inject/pressure.py', 'v2/server/reproduce_cases.py',
            *[p.relative_to(BENCH).as_posix() for p in sorted((V2 / 'inject').glob('*.py'))]]
    expected_code = {name:digest((BENCH / name).read_bytes()) for name in code}
    if versions.get('code_sha256') != expected_code:
        raise ValueError('server reconstruction code differs from local code')
    allowed = {'MANIFEST.json','MANIFEST.sha256','RESULT.json','versions.json','reproduction.log','REPRODUCED_INPUTS.json'}
    for row in reference['cases']:
        cid = row['case_id']
        server, local = bundle / 'cases' / cid, V2 / 'cases' / cid
        for field,value in snapshot(server).items():
            if value != row[field]:
                raise ValueError(cid + ': transferred payload differs: ' + field)
        for field,value in snapshot(local).items():
            if value != row[field]:
                raise ValueError(cid + ': local payload differs: ' + field)
        if cid.startswith('regression_') and (server / 'meta.json').read_bytes() != (local / 'meta.json').read_bytes():
            raise ValueError(cid + ': original regression metadata bytes differ')
        allowed.update('cases/' + cid + '/' + name for name in row['task_artifacts'])
        allowed.update('cases/' + cid + '/' + name for name in ('expected.json','meta.json','v2_labels.json'))
    actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    if actual != allowed:
        raise ValueError('unexpected or missing replay files')
    return {'benchmark_version':'v2', 'status':'pass', 'case_count':len(reference['cases']),
            'regression_count':16, 'new_count':8, 'bundle_path':bundle.as_posix(),
            'transport':proof, 'server_versions':versions,
            'local_reference_sha256':digest((V2 / 'CASE_INPUTS.json').read_bytes()),
            'context_sha256':reference['context_sha256'], 'source_manifest_sha256':reference['source_manifest_sha256'],
            'comparison':result['comparison'], 'linux_reproduction_status':'pass',
            'model_calls':0, 'answers_frozen':False, 'human_review_status':'pending',
            'original_source_hash_rescans':0}


def receipt_current():
    path = V2 / 'REPRODUCTION_VERIFIED.json'
    if not path.exists(): return False
    try:
        receipt = read(path)
        return (receipt['status'] == 'pass' and receipt['linux_reproduction_status'] == 'pass'
                and receipt['local_reference_sha256'] == digest((V2 / 'CASE_INPUTS.json').read_bytes())
                and all(digest((BENCH / name).read_bytes()) == value for name,value in receipt['server_versions']['code_sha256'].items()))
    except (OSError, KeyError, ValueError, TypeError):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--expected-manifest', required=True)
    args = parser.parse_args()
    receipt = inspect(args.bundle, args.expected_manifest)
    (V2 / 'REPRODUCTION_VERIFIED.json').write_bytes(json_bytes(receipt))
    print(f"ACCEPTED: {receipt['case_count']} cases; Linux/Windows 0 differences; {receipt['transport']['verified_files']} payload files; 0 model calls; answers not frozen")


if __name__ == '__main__': main()
