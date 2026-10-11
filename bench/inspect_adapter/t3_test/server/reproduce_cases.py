"""Reproduce T3 packets from transported real subsets; no original-source scan."""
from __future__ import annotations

import importlib.util
import platform
from pathlib import Path
import sys


def run():
    package=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('t3_packets',package/'t3_packets.py')
    builder=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.DIRECTORY=package/'t3_test'
    builder.RECEIPT=package/'source_receipt.json'
    reference=builder.read_json(builder.DIRECTORY/'CASE_MANIFEST.json')
    subsets=builder.read_json(builder.DIRECTORY/'selection/SOURCE_SUBSETS.json')
    if builder.digest(builder.RECEIPT.read_bytes())!=reference['source_receipt_sha256']:
        raise ValueError('transported source receipt differs')
    packets=builder.generate(subsets)
    builder.validate(packets)
    actual={cid+'/'+name:builder.digest(data) for cid,files in packets.items() for name,data in files.items()}
    if actual!=reference['files']:
        raise ValueError('case bytes differ: '+str(sorted(k for k in set(actual)|set(reference['files'])
            if actual.get(k)!=reference['files'].get(k))))
    # In the distributed zip, this script is at bench/t3_reproduction/.
    output=package.parent/'bench_transfer/inspect_t3_cases_reproduction/bundle'
    for cid,files in packets.items():
        for name,data in files.items():
            target=output/'cases'/cid/name
            if target.exists() and target.read_bytes()!=data:
                raise ValueError('existing result differs; preserve it before another version')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
    builder.write_json(output/'RECEIPT.json',{'status':'pass','cases':14,'differences':0,
        'python':sys.version.split()[0],'platform':platform.platform(),'api_calls':0,
        'source_rescans':0,'answers':'draft, not frozen','builder_sha256':builder.digest((package/'t3_packets.py').read_bytes()),
        'source_subset_sha256':builder.digest((builder.DIRECTORY/'selection/SOURCE_SUBSETS.json').read_bytes()),
        'reference_case_manifest_sha256':builder.digest((builder.DIRECTORY/'CASE_MANIFEST.json').read_bytes())})
    entries={p.relative_to(output).as_posix():builder.digest(p.read_bytes()) for p in sorted(output.rglob('*'))
             if p.is_file() and p.name!='MANIFEST.json'}
    builder.write_json(output/'MANIFEST.json',{'algorithm':'sha256','files':entries})
    print('PASS: 14 draft cases, 0 differences; no API or original-source rescans')
    print('Bundle: '+str(output))
    print('MANIFEST.json SHA-256: '+builder.digest((output/'MANIFEST.json').read_bytes()))
    return output


if __name__=='__main__':
    run()
