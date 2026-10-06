"""Pack only replay dependencies, accepted receipt, shared context and input hashes."""
import json
from pathlib import Path
import shutil
import zipfile
from build_cases import BENCH, DEFAULT_RECEIPT
from transfer import manifest
from inject.common import digest, json_bytes


def main():
    output=BENCH/'reproduction_package'
    output.mkdir(exist_ok=True)
    selected=['build_cases.py','visible_input.py','transfer.py','CASE_INPUTS.json',
              'context/skill_context.md','context/build_record.json','server/reproduce_cases.py']
    selected += [p.relative_to(BENCH).as_posix() for p in sorted((BENCH/'inject').glob('*.py'))]
    allowed=set(selected+['server/source_receipt.json','PACKAGE.json','MANIFEST.json','MANIFEST.sha256'])
    extra=[p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file() and p.relative_to(output).as_posix() not in allowed]
    if extra: raise ValueError('unexpected files in replay staging directory: ' + ', '.join(extra))
    for relative in selected:
        target=output/relative; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(BENCH/relative,target)
    target=output/'server/source_receipt.json'; shutil.copyfile(DEFAULT_RECEIPT,target)
    (output/'PACKAGE.json').write_bytes(json_bytes({'purpose':'stage2 cross-platform byte replay; not group A',
        'source_manifest_sha256':json.loads((BENCH/'CASE_INPUTS.json').read_text(encoding='utf-8'))['source_manifest_sha256'],
        'contains_api_keys':False,'contains_received_source_bundle':False,'contains_case_directory':False}))
    manifest(output)
    archive=BENCH/'reproduction_package.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as handle:
        for p in sorted(output.rglob('*')):
            if not p.is_file(): continue
            info=zipfile.ZipInfo(p.relative_to(output).as_posix(),date_time=(2020,1,1,0,0,0))
            info.external_attr=0o644 << 16; info.compress_type=zipfile.ZIP_STORED
            handle.writestr(info,p.read_bytes())
    print('Replay package:',archive,'bytes:',archive.stat().st_size,'SHA-256:',digest(archive.read_bytes()))


if __name__=='__main__': main()
