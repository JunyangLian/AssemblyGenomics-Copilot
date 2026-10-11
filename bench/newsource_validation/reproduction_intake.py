"""Verify returned case bytes and Linux receipt; never authorize a gold freeze."""
import argparse
import json
from pathlib import Path
import re

from bench.newsource_validation import cases
from bench.newsource_validation.intake import safe_file

DIRECTORY = cases.DIRECTORY


def verify(directory):
    root = Path(directory).resolve(strict=True)
    if (root / 'bundle').is_dir():
        root = root / 'bundle'
    cases.verify_protocol_lock()
    manifest_bytes = (root / 'MANIFEST.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get('algorithm') != 'sha256' or not isinstance(manifest.get('files'), dict):
        raise ValueError('unrecognized transport manifest')
    declared = manifest['files']
    for name, sha in declared.items():
        if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha):
            raise ValueError('invalid transport digest')
        safe_file(root, name)
    inventory = set()
    for path in root.rglob('*'):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('transport inventory link or escape')
        if path.is_file():
            inventory.add(path.relative_to(root).as_posix())
    if inventory != set(declared) | {'MANIFEST.json', 'MANIFEST.sha256'}:
        raise ValueError('transport inventory differs from manifest')
    mh = cases.old.digest(manifest_bytes)
    expected_sums = {f'{sha}  {name}' for name, sha in declared.items()} | {f'{mh}  MANIFEST.json'}
    sums = (root / 'MANIFEST.sha256').read_text(encoding='utf-8').splitlines()
    if len(sums) != len(expected_sums) or set(sums) != expected_sums:
        raise ValueError('SHA sidecar disagrees with manifest')
    payloads = {name: (root / name).read_bytes() for name in declared}
    if {name: cases.old.digest(data) for name, data in payloads.items()} != declared:
        raise ValueError('payload SHA differs from transport manifest')
    reference_path = DIRECTORY / 'CASE_MANIFEST.json'
    reference = cases.old.read_json(reference_path)
    wanted = {'cases/' + n: sha for n, sha in reference['files'].items()}
    if len(wanted) != 72 or set(declared) != set(wanted) | {'RECEIPT.json'}:
        raise ValueError('returned case inventory differs from twelve-case reference')
    for name, sha in wanted.items():
        local = (DIRECTORY / name).read_bytes()
        if cases.old.digest(local) != sha or declared[name] != sha or payloads[name] != local:
            raise ValueError('Linux/Windows reference bytes differ: ' + name)
    receipt = json.loads(payloads['RECEIPT.json'])
    for key, value in {'status': 'pass', 'cases': 12, 'differences': 0, 'api_calls': 0,
                       'original_source_rescans': 0, 'answers': 'draft; not approved'}.items():
        if receipt.get(key) != value:
            raise ValueError('unexpected server receipt: ' + key)
    package = cases.old.read_json(DIRECTORY / 'REPRODUCTION_PACKAGE_RECEIPT.json')
    identities = {'reference_case_manifest_sha256': cases.old.digest(reference_path.read_bytes()),
                  'protocol_lock_sha256': cases.old.digest((DIRECTORY / 'PROTOCOL_LOCK.json').read_bytes()),
                  'subset_sha256': cases.old.digest((DIRECTORY / 'selection/SOURCE_SUBSETS.json').read_bytes()),
                  'package_inputs_sha256': package['files']['PACKAGE_INPUTS.json']}
    if any(receipt.get(k) != v for k, v in identities.items()):
        raise ValueError('server package/protocol/subset/reference identity differs')
    if not str(receipt.get('platform', '')).startswith('Linux-') or not receipt.get('python') or not receipt.get('jsonschema'):
        raise ValueError('Linux runtime/tool version receipt missing')
    return {'status': 'verified_linux_windows_parity', 'case_count': 12, 'case_files': 72,
            'transport_payloads': 73, 'differences': 0, 'bundle_path': str(root),
            'transport_manifest_sha256': mh, 'server_receipt_sha256': declared['RECEIPT.json'],
            'server_receipt': receipt, 'local_reference_sha256': identities['reference_case_manifest_sha256'],
            'api_calls': 0, 'original_source_rescans': 0, 'answer_approval': False, 'answers_frozen': False,
            'scope': 'transported real subsets generate identical cases; not independent raw-source re-extraction',
            'runtime_provenance': 'user-executed server receipt; not remote host attestation',
            'initial_transport_hash_passes': 1}


def save(directory):
    result = verify(directory)
    cases.immutable(DIRECTORY / 'LINUX_REPRODUCTION.json', cases.old.canonical(result))
    print('PASS: Linux/Windows 12 cases, 72 identical files, 73 verified payloads; 0 API calls; no gold approval')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    save(parser.parse_args().directory)
