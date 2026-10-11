"""Build a fixed-byte cross-platform reproduction archive, with no large sources."""
import io
from pathlib import Path
import zipfile

from bench.newsource_validation import cases


def package():
    cases.build()
    lock = cases.verify_protocol_lock()
    root = cases.DIRECTORY.parent.parent
    content = {n: (root / n).read_bytes() for n in lock['files']}
    content.update({'bench/newsource_validation/' + n: (cases.DIRECTORY / n).read_bytes() for n in (
        'PROTOCOL_LOCK.json', 'SOURCE_RECEIPT.json', 'selection/SOURCE_SUBSETS.json', 'CASE_MANIFEST.json')})
    content['reproduce_cases.py'] = (cases.DIRECTORY / 'server/reproduce_cases.py').read_bytes()
    content['requirements.txt'] = b'jsonschema>=4.18,<5\n'
    content['PACKAGE_INPUTS.json'] = cases.old.canonical({'files': {n: cases.old.digest(b) for n, b in content.items()},
                                                        'api_calls': 0, 'scope': 'transported real subsets, draft gold'})
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as stream:
        for name, data in sorted(content.items()):
            info = zipfile.ZipInfo('newsource_reproduction/' + name, (2026, 10, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            stream.writestr(info, data)
    target = cases.DIRECTORY / 'reproduction_package.zip'
    cases.immutable(target, archive.getvalue())
    cases.old.write_json(cases.DIRECTORY / 'REPRODUCTION_PACKAGE_RECEIPT.json', {
        'archive_sha256': cases.old.digest(target.read_bytes()), 'archive_bytes': target.stat().st_size,
        'files': {n: cases.old.digest(b) for n, b in content.items()}, 'answers': 'draft', 'api_calls': 0,
        'large_originals_included': False, 'includes_jsonschema': False,
        'server_command': 'python newsource_reproduction/reproduce_cases.py'})
    print('PACKAGE: ' + str(target))
    return target


if __name__ == '__main__':
    package()
