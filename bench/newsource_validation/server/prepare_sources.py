"""Standalone T3 intake: exact copies, one-pass source SHA, resumable receipts.

No network, external commands, credentials, annotation runs or benchmark answers.
Python 3.9+; run from the server repository's bench directory.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys

VERSION = 'v3-source-prepare-1'


def data(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_bytes(data(value))
    temp.replace(path)


def signature(path):
    s = path.stat()
    return {'size_bytes': s.st_size, 'mtime_ns': s.st_mtime_ns}


def within(path, root):
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError('path escapes configured root: ' + str(path))
    return path


def inspect_copy(path, kind):
    # Read copied gzip to its EOF, including checksum/trailer verification.
    counts = Counter()
    in_fasta = False
    have_header = False
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as stream:
        for row, raw in enumerate(stream, 1):
            line = raw.rstrip('\r\n')
            if not line:
                continue
            if kind == 'gff':
                if line == '##FASTA':
                    in_fasta = True
                if line.startswith('#') or in_fasta:
                    continue
                columns = line.split('\t')
                if len(columns) != 9:
                    raise ValueError('GFF requires 9 columns at row ' + str(row))
                start, end = int(columns[3]), int(columns[4])
                if start < 1 or end < start:
                    raise ValueError('GFF coordinate format at row ' + str(row))
                counts['feature_rows'] += 1
                counts[columns[2] + '_rows'] += 1
            elif line.startswith('>'):
                if not line[1:].strip():
                    raise ValueError('empty FAA header')
                counts['protein_records'] += 1
                have_header = True
            else:
                if not have_header:
                    raise ValueError('FAA sequence before first header')
                counts['residues'] += len(''.join(line.split()))
    required = 'feature_rows' if kind == 'gff' else 'protein_records'
    if not counts[required]:
        raise ValueError('no ' + required + ' in copied input')
    return dict(counts)


def collect(item, source_root, bundle):
    name = item['filename']
    acc, kind = item['source_group'], item['kind']
    if (Path(name).name != name or '/' in name or '\\' in name or
        not name.startswith(acc + '_') or kind not in ('gff', 'faa') or
        not name.endswith('.gff.gz' if kind == 'gff' else '.faa.gz')):
        raise ValueError('invalid source filename/kind')
    source = within((source_root / name).resolve(), source_root)
    if not source.is_file():
        raise ValueError('source missing: ' + str(source))
    target = within((bundle / 'sources' / name).resolve(), bundle)
    receipt = bundle / 'records' / (acc + '_' + kind + '.json')
    source_sig = signature(source)
    reused = False
    if receipt.exists():
        record = json.loads(receipt.read_bytes())
        if (record['source_path'] != str(source) or record['source_signature'] != source_sig or
            not target.is_file() or record['copy_signature'] != signature(target)):
            raise ValueError('cached source/copy identity changed; choose a new --output-root, preserve old bundle')
        if any(record.get(k) != item[k] for k in ('source_group', 'species', 'clade', 'kind')):
            raise ValueError('cached selection changed; choose a new --output-root')
        reused = True
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + '.partial')
        checksum = hashlib.sha256()
        try:
            with source.open('rb') as src, temp.open('wb') as dst:
                for chunk in iter(lambda: src.read(1024 * 1024), b''):
                    checksum.update(chunk)
                    dst.write(chunk)
            if signature(source) != source_sig:
                raise ValueError('source changed during copy; choose a new output bundle after source stabilizes')
            temp.replace(target)
        finally:
            if temp.exists():
                temp.unlink()
        record = {k: item[k] for k in ('source_group', 'species', 'clade', 'kind')}
        record.update(source_path=str(source), source_signature=source_sig,
                      package_path=target.relative_to(bundle).as_posix(),
                      copy_signature=signature(target), sha256=checksum.hexdigest(),
                      recorded_historical_size_bytes=item['recorded_size_bytes'],
                      copy_method='whole original gzip bytes; SHA while copying source once',
                      source_hash_policy='repeat reuses receipt after path/size/mtime checks; no source rescan')
        try:
            record['inspection'] = inspect_copy(target, kind)
        except (ValueError, OSError, EOFError, UnicodeError) as exc:
            record['inspection_error'] = type(exc).__name__ + ': ' + str(exc)
        write_json(receipt, record)
    if record.get('inspection_error'):
        raise ValueError('copied input failed integrity/format check: ' + record['inspection_error'])
    return record, reused


def execute(config_path, bench_root, output_root=None):
    config_path = Path(config_path).resolve(strict=True)
    config = json.loads(config_path.read_bytes())
    if config['spec_version'] != VERSION or config['source_scope'] != 'T3':
        raise ValueError('unsupported source preparation config')
    items = config['files']
    identities = [(x['source_group'], x['kind']) for x in items]
    grouped = {}
    for item in items:
        grouped.setdefault(item['source_group'], []).append(item['kind'])
    if (not items or len(set(identities)) != len(identities) or
        any(sorted(kinds) != ['faa', 'gff'] for kinds in grouped.values())):
        raise ValueError('selection requires exactly one GFF and FAA for each group')
    source_root = Path(config['source_root']).expanduser().resolve()
    bench_root = Path(bench_root).expanduser().resolve(strict=True)
    chosen = Path(output_root or config['output_root']).expanduser()
    out = within((bench_root / chosen).resolve(), (bench_root / 'bench_transfer').resolve())
    bundle = out / 'bundle'
    bundle.mkdir(parents=True, exist_ok=True)
    identity = {'spec_version': VERSION, 'source_scope': 'T3',
                'source_root': str(source_root), 'files': items}
    identity_path = bundle / 'SELECTION.json'
    if identity_path.exists() and json.loads(identity_path.read_bytes()) != identity:
        raise ValueError('selection/source root changed; choose a new --output-root')
    write_json(identity_path, identity)
    script = Path(__file__).resolve()
    scripts = bundle / 'scripts'
    scripts.mkdir(exist_ok=True)
    shutil.copyfile(script, scripts / 'prepare_sources.py')
    write_json(scripts / 'prepare_config.json', config)
    write_json(bundle / 'TOOL_VERSIONS.json', {'python': sys.version, 'platform': platform.platform(),
               'implementation': platform.python_implementation(), 'gzip': 'Python standard library',
               'external_tools_used': [], 'script_version': VERSION})
    sources, gaps, reused_count = [], [], 0
    for item in items:
        try:
            record, reused = collect(item, source_root, bundle)
            sources.append(record)
            reused_count += int(reused)
        except (ValueError, OSError, EOFError, UnicodeError, KeyError) as exc:
            gaps.append({'source_group': item['source_group'], 'kind': item['kind'],
                         'filename': item['filename'], 'reason': type(exc).__name__ + ': ' + str(exc)})
    complete = len(sources) == len(items) and not gaps
    status = {'status': 'complete' if complete else 'blocked', 'spec_version': VERSION,
              'source_scope': 'T3', 'source_groups': list(grouped), 'required_files': len(items),
              'sources': sources, 'gaps': gaps, 'cached_files_reused': reused_count,
              'api_calls': 0, 'analysis_runs': 0, 'other_original_source_hash_scans': 0,
              'historical_report_notice': config.get('historical_report_notice', ''),
              'inspection_scope': 'gzip and file format/record counts only; not QC gold or genome-quality validation',
              'cached_integrity_policy': 'reuse recorded checksum/inspection when source and copy signatures unchanged; local receiver verifies transport SHA'}
    write_json(bundle / 'STATUS.json', status)
    logs = bundle / 'logs'; logs.mkdir(exist_ok=True)
    (logs / 'prepare.log').write_bytes((status['status'].upper() + ': ' + str(len(sources)) +
        '/' + str(len(items)) + ' files; ' + str(len(gaps)) + ' required gaps; 0 API calls; 0 analysis runs\n' +
        '\n'.join('GAP ' + g['filename'] + ': ' + g['reason'] for g in gaps) + '\n').encode('utf-8'))
    # Source digests come from their copy receipt, never re-read originals.
    cached = {s['package_path']: s['sha256'] for s in sources}
    for receipt in (bundle / 'records').glob('*.json'):
        doc = json.loads(receipt.read_bytes())
        copy = bundle / doc['package_path']
        if copy.is_file() and signature(copy) == doc['copy_signature']:
            cached.setdefault(doc['package_path'], doc['sha256'])
    entries = []
    for path in sorted(bundle.rglob('*')):
        if not path.is_file() or path.name in ('MANIFEST.json', 'MANIFEST.sha256'):
            continue
        rel = path.relative_to(bundle).as_posix()
        entries.append({'path': rel, 'size_bytes': path.stat().st_size,
                        'sha256': cached[rel] if rel in cached else hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(bundle / 'MANIFEST.json', {'format': VERSION, 'files': entries})
    manifest_sha = hashlib.sha256((bundle / 'MANIFEST.json').read_bytes()).hexdigest()
    lines = [e['sha256'] + '  ' + e['path'] for e in entries] + [manifest_sha + '  MANIFEST.json']
    (bundle / 'MANIFEST.sha256').write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
    print(status['status'].upper() + ': ' + str(len(sources)) + '/' + str(len(items)) +
          ' files; ' + str(len(grouped)) + ' groups; ' + str(len(gaps)) + ' required gaps', flush=True)
    print('Bundle: ' + str(bundle), flush=True)
    print('MANIFEST.json SHA-256: ' + manifest_sha, flush=True)
    print('Cached reuse: ' + str(reused_count) + '; 0 API calls; 0 analysis runs', flush=True)
    for gap in gaps:
        print('GAP ' + gap['filename'] + ': ' + gap['reason'], flush=True)
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('prepare_config.json'))
    parser.add_argument('--bench-root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    try:
        result = execute(args.config, args.bench_root, args.output_root)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print('BLOCKED: ' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(2)
    sys.exit(0 if result['status'] == 'complete' else 2)
