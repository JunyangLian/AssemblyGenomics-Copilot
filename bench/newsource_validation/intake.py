"""Verify a new-source transport once; never infer gold or API authorization."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

DIRECTORY = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def signature(path):
    stat = path.stat()
    return {'size_bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}


def safe_file(root, name):
    if not isinstance(name, str):
        raise ValueError('unsafe transport path')
    part = PurePosixPath(name)
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name or
            part.is_absolute() or '..' in part.parts or part.as_posix() != name):
        raise ValueError('unsafe transport path')
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink() or not path.is_file():
        raise ValueError('transport file missing or escapes root: ' + name)
    return path


def verify(bundle, receipt_path=DIRECTORY / 'SOURCE_RECEIPT.json'):
    bundle = Path(bundle).resolve(strict=True)
    if not (bundle / 'MANIFEST.json').exists() and (bundle / 'bundle').is_dir():
        bundle = bundle / 'bundle'
    manifest_bytes = (bundle / 'MANIFEST.json').read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = json.loads(manifest_bytes)
    if manifest['format'] != 'v3-source-prepare-1':
        raise ValueError('unexpected transport format')
    entries = manifest['files']
    names = [entry['path'] for entry in entries]
    if len(set(names)) != len(names):
        raise ValueError('duplicate transport entries')
    paths = {name: safe_file(bundle, name) for name in names}
    actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    if actual != set(names) | {'MANIFEST.json', 'MANIFEST.sha256'}:
        raise ValueError('unregistered or absent transport files')
    sums = (bundle / 'MANIFEST.sha256').read_text(encoding='utf-8').splitlines()
    expected_sums = {f'{entry["sha256"]}  {entry["path"]}' for entry in entries}
    expected_sums.add(f'{manifest_hash}  MANIFEST.json')
    if len(sums) != len(expected_sums) or set(sums) != expected_sums:
        raise ValueError('SHA sidecar disagrees with manifest')
    signatures = {name: signature(path) for name, path in paths.items()}
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_bytes())
        if (previous['bundle_path'] != str(bundle) or previous['transport_manifest_sha256'] != manifest_hash or
                previous['verified_signatures'] != signatures):
            raise ValueError('transport identity changed; preserve receipt and choose a new intake version')
        print('CACHED: six source groups; original transport not rehashed; 0 API calls')
        return previous
    for entry in entries:
        path = paths[entry['path']]
        if path.stat().st_size != entry['size_bytes'] or sha(path) != entry['sha256']:
            raise ValueError('transport checksum mismatch: ' + entry['path'])
    config = json.loads((DIRECTORY / 'server/prepare_config.json').read_bytes())
    selection = json.loads(paths['SELECTION.json'].read_bytes())
    if (selection['files'] != config['files'] or selection['source_root'] != config['source_root'] or
            selection['spec_version'] != config['spec_version'] or selection['source_scope'] != 'T3'):
        raise ValueError('server selection differs from requested source scope')
    for name in ('prepare_config.json', 'prepare_sources.py'):
        if paths['scripts/' + name].read_bytes() != (DIRECTORY / 'server' / name).read_bytes():
            raise ValueError('server preparation code/config differs: ' + name)
    status = json.loads(paths['STATUS.json'].read_bytes())
    if (status['status'] != 'complete' or status['gaps'] or status['required_files'] != 12 or
            status['api_calls'] != 0 or status['analysis_runs'] != 0):
        raise ValueError('server preparation incomplete or out of scope')
    wanted = {(r['source_group'], r['kind']): r for r in config['files']}
    received = {}
    hashes = {entry['path']: entry['sha256'] for entry in entries}
    for record in status['sources']:
        key = record['source_group'], record['kind']
        if key in received or key not in wanted:
            raise ValueError('unexpected or duplicate source identity')
        item = wanted[key]
        if (record['package_path'] != 'sources/' + item['filename'] or
                record['source_path'] != item['recorded_origin'] or
                record['species'] != item['species'] or record['clade'] != item['clade'] or
                record['sha256'] != hashes[record['package_path']] or
                record.get('inspection_error') or not record.get('inspection')):
            raise ValueError('source record contradicts transport/request')
        if paths[record['package_path']].stat().st_size != record['copy_signature']['size_bytes']:
            raise ValueError('source size differs from copy receipt')
        received[key] = record
    if set(received) != set(wanted):
        raise ValueError('required source pairs absent')
    result = {'status': 'verified_transport_only', 'bundle_path': str(bundle),
              'transport_manifest_sha256': manifest_hash, 'verified_signatures': signatures,
              'sources': status['sources'], 'source_groups': sorted({r[0] for r in wanted}),
              'source_files': 12, 'source_bytes': sum(paths[r['package_path']].stat().st_size for r in status['sources']),
              'server_tools': json.loads(paths['TOOL_VERSIONS.json'].read_bytes()),
              'server_scope': status['inspection_scope'], 'api_calls': 0,
              'original_server_hash_rescans': 0, 'local_transport_hash_passes': 1,
              'hash_policy': 'one local transport hash pass; unchanged path/size/mtime receipt reuse',
              'answers_confirmed': False, 'answers_frozen': False, 'api_call_authorized': False,
              'new_gff_or_faa_features_examined': False}
    receipt_path.write_bytes((json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode())
    print(f'PASS: {len(result["source_groups"])} groups; 12 source files; {result["source_bytes"]:,} bytes; '
          'transport SHA verified; no gold or API approval')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    verify(parser.parse_args().bundle)
