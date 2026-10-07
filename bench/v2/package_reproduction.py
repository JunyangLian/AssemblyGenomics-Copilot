"""Build a fixed whitelist replay zip with a content manifest. Never package runs."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import zipfile

V2 = Path(__file__).resolve().parent
BENCH = V2.parent
sys.path.insert(0, str(BENCH))
from inject.common import digest, json_bytes
from visible_input import visible_files


def package():
    required = ['FROZEN.md', 'FROZEN.json', 'context/skill_context.md', 'inject/__init__.py',
                'inject/common.py', 'inject/pressure.py', 'visible_input.py', 'transfer.py',
                'v2/__init__.py', 'v2/build_cases.py', 'v2/CASE_INPUTS.json',
                'v2/context/skill_context.md', 'v2/context/addendum.md', 'v2/server/reproduce_cases.py']
    required += [p.relative_to(BENCH).as_posix() for p in sorted((V2 / 'inject').glob('*.py'))]
    for i in range(1,17):
        case = BENCH / 'cases' / f'case_{i:03}'
        required += [p.relative_to(BENCH).as_posix() for p in [*visible_files(case), case / 'meta.json', case / 'expected.json']]
    receipt = BENCH / 'v1_prepare_t1t3_r3/verified.json'
    contents = {name:(BENCH / name).read_bytes() for name in sorted(set(required))}
    contents['v2/server/source_receipt.json'] = receipt.read_bytes()
    result = {'benchmark_version':'v2', 'source_bundle_included':False,
              'server_existing_bundle':'bench_transfer/v1_prepare_t1t3_r3/bundle', 'model_calls':0,
              'files':[{'path':name, 'sha256':digest(data), 'size_bytes':len(data)} for name,data in sorted(contents.items())]}
    contents['v2/server/PACKAGE_CONTENTS.json'] = json_bytes(result)
    target = V2 / 'reproduction_package.zip'
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name,data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(2026,10,7,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    result.update({'package_sha256':digest(target.read_bytes()), 'package_size_bytes':target.stat().st_size})
    (V2 / 'server/PACKAGE_RECEIPT.json').write_bytes(json_bytes(result))
    print(f'PACKAGE: {len(contents)} files; {target.stat().st_size} bytes; SHA-256 {result["package_sha256"]}')


if __name__ == '__main__': package()
