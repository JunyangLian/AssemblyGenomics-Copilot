"""Verify a received v3 T3 bundle before any source can be used locally."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify(directory, config_path=None, receipt_path=None):
    directory = Path(directory).resolve(strict=True)
    if not (directory / 'MANIFEST.json').is_file():
        directory = (directory / 'bundle').resolve(strict=True)
    config = json.loads(Path(config_path or ROOT / 'server/prepare_config.json').read_bytes())
    manifest = json.loads((directory / 'MANIFEST.json').read_bytes())
    if manifest['format'] != config['spec_version']:
        raise ValueError('unexpected bundle format')
    names = set()
    recorded = {}
    for item in manifest['files']:
        name = item['path']
        path = Path(name)
        if path.is_absolute() or '\\' in name or any(p in ('.', '..') for p in name.split('/')):
            raise ValueError('invalid manifest path')
        target = (directory / path).resolve(strict=True)
        try:
            target.relative_to(directory)
        except ValueError:
            raise ValueError('manifest path escapes bundle')
        if name in names or not target.is_file():
            raise ValueError('duplicate/non-file manifest entry')
        names.add(name)
        if target.stat().st_size != item['size_bytes'] or sha(target) != item['sha256']:
            raise ValueError('transport checksum/size mismatch: ' + name)
        recorded[name] = item['sha256']
    present = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    if present != names | {'MANIFEST.json', 'MANIFEST.sha256'}:
        raise ValueError('unlisted or missing bundle payload')
    manifest_sha = sha(directory / 'MANIFEST.json')
    lines = (directory / 'MANIFEST.sha256').read_text(encoding='utf-8').splitlines()
    checksums = {}
    for line in lines:
        value, name = line.split('  ', 1)
        if name in checksums:
            raise ValueError('duplicate SHA list entry')
        checksums[name] = value
    if checksums != {**recorded, 'MANIFEST.json': manifest_sha}:
        raise ValueError('SHA list differs from manifest')
    status = json.loads((directory / 'STATUS.json').read_bytes())
    expected = {(f['source_group'], f['kind']): f for f in config['files']}
    records = {(s['source_group'], s['kind']): s for s in status['sources']}
    if (status['status'] != 'complete' or status['gaps'] or
        len(records) != len(status['sources']) or set(records) != set(expected) or
        status['required_files'] != len(expected) or status['source_scope'] != 'T3' or
        set(status['source_groups']) != {k[0] for k in expected}):
        raise ValueError('bundle incomplete or differs from approved T3 selection')
    selection = json.loads((directory / 'SELECTION.json').read_bytes())
    if selection['files'] != config['files'] or selection['source_scope'] != 'T3':
        raise ValueError('selection differs from local source config')
    for key, s in records.items():
        f = expected[key]
        if (s['package_path'] != 'sources/' + f['filename'] or
            s['sha256'] != recorded.get(s['package_path']) or
            s['species'] != f['species'] or s['clade'] != f['clade'] or
            s.get('inspection_error') or not s.get('inspection')):
            raise ValueError('source receipt identity/inspection mismatch')
        record_path = 'records/' + key[0] + '_' + key[1] + '.json'
        if json.loads((directory / record_path).read_bytes()) != s:
            raise ValueError('per-source receipt differs from status')
    receipt = {'status': 'verified_transport_and_format', 'bundle_path': str(directory),
               'manifest_sha256': manifest_sha, 'verified_payload_files': len(names),
               'source_files': len(records), 'source_groups': sorted({k[0] for k in expected}),
               'config_sha256': sha(Path(config_path or ROOT / 'server/prepare_config.json')),
               'api_calls': 0, 'analysis_runs': 0, 'sources': status['sources'],
               'historical_report_notice': status['historical_report_notice'],
               'quality_scope': 'transport/gzip/file format only; no cases built, answers assigned or baseline PASS inferred'}
    if receipt_path:
        target = Path(receipt_path)
        if target.exists() and json.loads(target.read_bytes()) != receipt:
            raise ValueError('receipt already exists for different intake; preserve it and use a new receipt path')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8'))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.directory, receipt_path=ROOT / 'SOURCE_RECEIPT.json')
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print('BLOCKED: ' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(2)
    print('VERIFIED: ' + str(result['source_files']) + ' T3 sources; ' +
          str(len(result['source_groups'])) + ' groups; 0 API calls')
    print('Receipt: ' + str(ROOT / 'SOURCE_RECEIPT.json'))
