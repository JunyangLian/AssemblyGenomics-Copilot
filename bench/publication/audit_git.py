"""Read-only credential/publication checks; findings never print matched values."""
import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PATTERNS = [
    ('api_key_literal', re.compile(rb'(?<![A-Za-z0-9])sk-[A-Za-z0-9_.~-]{20,}')),
    ('aws_access_key_literal', re.compile(rb'\bAKIA[A-Z0-9]{16}\b')),
    ('private_key_header', re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
]
# Explicit noncredential test fixtures may be checked into test code.
TEST_PREFIXES = (b'sk-test-', b'sk-dummy-', b'sk-sentinel-', b'sk-not-real-', b'sk-not-a-real-')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


def scan(data, path, oid, findings, fixtures):
    for category, pattern in PATTERNS:
        for match in pattern.finditer(data):
            value = match.group()
            entry = {'path': path, 'object_sha1': oid, 'category': category,
                     'line': data[:match.start()].count(b'\n') + 1}
            if category == 'api_key_literal' and value.startswith(TEST_PREFIXES) and ('test' in path or path.endswith('.py')):
                fixtures.append(entry)
            else:
                findings.append(entry)


def execute(base):
    candidates = {}
    for line in git('rev-list', '--objects', base + '..HEAD').decode().splitlines():
        parts = line.split(' ', 1)
        candidates[parts[0]] = parts[1] if len(parts) == 2 else '(git object)'
    tracked = {}
    large = []
    for line in git('ls-tree', '-rl', 'HEAD').decode().splitlines():
        header, path = line.split('\t', 1)
        _, kind, oid, size = header.split()
        if kind == 'blob':
            candidates.setdefault(oid, path)
            tracked[path] = {'sha1': oid, 'size_bytes': int(size)}
            if int(size) >= 100_000_000:
                large.append({'path': path, 'size_bytes': int(size)})
    names = list(candidates)
    metadata = subprocess.run(['git', 'cat-file', '--batch-check'], cwd=REPO,
                              input=('\n'.join(names) + '\n').encode(), stdout=subprocess.PIPE, check=True).stdout.decode().splitlines()
    blobs = [line.split()[0] for line in metadata if len(line.split()) == 3 and line.split()[1] == 'blob']
    head_large = {entry['path'] for entry in large}
    for line in metadata:
        fields = line.split()
        if len(fields) == 3 and fields[1] == 'blob' and int(fields[2]) >= 100_000_000 and candidates[fields[0]] not in head_large:
            large.append({'path': candidates[fields[0]], 'object_sha1': fields[0], 'size_bytes': int(fields[2]), 'scope': 'unpublished_history'})
    stream = subprocess.run(['git', 'cat-file', '--batch'], cwd=REPO,
                            input=('\n'.join(blobs) + '\n').encode(), stdout=subprocess.PIPE, check=True).stdout
    source = io.BytesIO(stream)
    findings, fixtures = [], []
    for expected_oid in blobs:
        oid, kind, size = source.readline().decode().strip().split()
        assert oid == expected_oid and kind == 'blob'
        data = source.read(int(size))
        assert source.read(1) == b'\n'
        path = candidates[oid]
        scan(data, path, oid, findings, fixtures)
        if data.startswith(b'PK\x03\x04'):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for item in archive.infolist():
                    if not item.is_dir():
                        scan(archive.read(item), path + '!' + item.filename, oid, findings, fixtures)
        elif data.startswith(b'\x1f\x8b'):
            try:
                unpacked = gzip.decompress(data)
            except (EOFError, OSError):
                # Deliberately incomplete benchmark binary: scan only existing bytes.
                continue
            scan(unpacked, path + '!gzip', oid, findings, fixtures)
    sensitive_names = [path for path in tracked if re.search(r'(^|/)(\.env(?:\..*)?|id_rsa|credentials[^/]*|.*\.pem)$', path, re.I)]
    report = {'client_date': '2026-10-09', 'status': 'pass' if not findings and not large and not sensitive_names else 'blocked',
              'head_scanned': git('rev-parse', 'HEAD').decode().strip(), 'base': base,
              'unpublished_commits': int(git('rev-list', '--count', base + '..HEAD')),
              'tracked_files': len(tracked), 'unique_blobs_scanned': len(blobs),
              'credential_findings': findings, 'explicit_test_fixtures': fixtures,
              'sensitive_tracked_names': sensitive_names, 'github_oversize_blobs': large,
              'scope': 'HEAD tracked files and unpublished historical blobs, including ZIP/gzip contents; no environment variables or ignored local sources read',
              'limitations': 'pattern-based check, not a guarantee against every possible credential format',
              'tracked_tree_index_sha256': hashlib.sha256(json.dumps(tracked, sort_keys=True).encode()).hexdigest()}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='origin/main')
    parser.add_argument('--report', type=Path, default=Path(__file__).resolve().parent / 'work/security_audit.json')
    args = parser.parse_args()
    report = execute(args.base)
    target = args.report.resolve()
    if not target.is_relative_to(Path(__file__).resolve().parent / 'work'):
        raise ValueError('audit report must stay in bench/publication/work')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({key: report[key] for key in ('status', 'unpublished_commits', 'tracked_files', 'unique_blobs_scanned',
                                                  'credential_findings', 'explicit_test_fixtures', 'sensitive_tracked_names', 'github_oversize_blobs')}, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'pass' else 2)
