"""Reproduce transported subsets, never rescan original large server sources."""
import hashlib
import json
import platform
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode())


def run():
    package = Path(__file__).resolve().parent
    sys.path.insert(0, str(package))
    try:
        import jsonschema
    except ImportError:
        print('MISSING: jsonschema. Install in this Python environment: python -m pip install "jsonschema>=4.18,<5"')
        raise SystemExit(2)
    from importlib.metadata import version
    from bench.newsource_validation import cases
    inputs = json.loads((package / 'PACKAGE_INPUTS.json').read_bytes())
    for name, digest in inputs['files'].items():
        path = package / name
        if not path.is_file() or sha(path.read_bytes()) != digest:
            raise ValueError('package file differs: ' + name)
    cases.verify_protocol_lock()
    selected = cases.old.read_json(cases.DIRECTORY / 'selection/SOURCE_SUBSETS.json')
    packets = cases.generate(selected)
    cases.validate(packets, selected)
    reference = cases.old.read_json(cases.DIRECTORY / 'CASE_MANIFEST.json')
    actual = {cid + '/' + name: sha(data) for cid, files in packets.items() for name, data in files.items()}
    differences = sorted(n for n in set(actual) | set(reference['files']) if actual.get(n) != reference['files'].get(n))
    if differences:
        raise ValueError('generation differs from Windows: ' + str(differences))
    output = package.parent / 'bench_transfer/newsource_validation_cases_r1/bundle'
    for cid, files in packets.items():
        for name, data in files.items():
            target = output / 'cases' / cid / name
            cases.immutable(target, data)
    write(output / 'RECEIPT.json', {'status': 'pass', 'cases': 12, 'differences': 0,
          'api_calls': 0, 'original_source_rescans': 0, 'answers': 'draft; not approved',
          'scope': 'generation from source-backed transported subsets; not independent re-extraction',
          'python': sys.version, 'platform': platform.platform(), 'jsonschema': version('jsonschema'),
          'reference_case_manifest_sha256': sha((cases.DIRECTORY / 'CASE_MANIFEST.json').read_bytes()),
          'protocol_lock_sha256': sha((cases.DIRECTORY / 'PROTOCOL_LOCK.json').read_bytes()),
          'subset_sha256': sha((cases.DIRECTORY / 'selection/SOURCE_SUBSETS.json').read_bytes()),
          'package_inputs_sha256': sha((package / 'PACKAGE_INPUTS.json').read_bytes())})
    files = {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob('*'))
             if p.is_file() and p.name not in ('MANIFEST.json', 'MANIFEST.sha256')}
    write(output / 'MANIFEST.json', {'algorithm': 'sha256', 'files': files})
    entries = {**files, 'MANIFEST.json': sha((output / 'MANIFEST.json').read_bytes())}
    (output / 'MANIFEST.sha256').write_bytes(''.join(f'{digest}  {name}\n' for name, digest in sorted(entries.items())).encode())
    print('PASS: 12 cases, 0 differences; tool versions and SHA manifest recorded')
    print('Bundle: ' + str(output))
    print('MANIFEST.json SHA-256: ' + entries['MANIFEST.json'])
    print('No API calls or original-source hash rescans; answers remain draft')
    return output


if __name__ == '__main__':
    run()
