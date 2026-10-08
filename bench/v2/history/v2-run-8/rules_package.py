"""Export eight public cases and byte-identical original rules, no private case files."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from bench.v2.runtime import V2, BENCH, REPO, digest, write_json
from bench.v2.plan import verify
from bench.v2.import_rules import EXPORT
from transfer import manifest, files, verify as transport_verify


def make(root=V2):
    locked = verify(root)
    payload = {}
    for name in EXPORT:
        payload[name] = (root / name if name == EXPORT[0] else BENCH / name).read_bytes()
    for name, sha in locked['plan']['rule_sources'].items():
        data = (REPO / name).read_bytes().replace(b'\r\n', b'\n')
        if digest(data) != sha:
            raise ValueError('original rule snapshot differs')
        payload['original_rules/' + name] = data
    cases = [c for c in locked['plan']['cases'] if c['case_id'].startswith('new_')]
    for c in cases:
        for name in c['public_files']:
            payload['cases/' + c['case_id'] + '/' + name] = (root / 'cases' / c['case_id'] / name).read_bytes()
    from bench.v2.runtime import canonical
    payload['SERVER_PLAN.json'] = canonical({'format': 2, 'plan_sha256': locked['plan_sha256'],
        'frozen_md_sha256': locked['frozen_md_sha256'], 'cases': cases, 'repetitions': 3,
        'rule_sources': locked['plan']['rule_sources'], 'adapter_files': {n: digest(payload[n]) for n in EXPORT},
        'output_root': 'bench_transfer/v2_rules_run_1/bundle', 'no_model_calls': True})
    payload['README.txt'] = ('服务器在 ~/AssemblyGenomics-Skill/bench 下：\n'
        'python -m zipfile -e v2/rules_package.zip v2/rules_package\n'
        'python v2/rules_package/server/run_rules.py\n'
        '回传 bench_transfer/v2_rules_run_1/bundle 整目录。\n'
        '原规则随包携带，记录原始身份；不依赖仓库其它布局，不含答案、meta、key或模型配置。\n').encode('utf-8')
    target = root / 'rules_package'
    if target.exists():
        transport_verify(target)
        if {n: p.read_bytes() for n, p in files(target).items() if n not in ('MANIFEST.json', 'MANIFEST.sha256')} != payload:
            raise ValueError('existing package differs; preserve it before registering a revision')
    else:
        for name, data in payload.items():
            p = target / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        manifest(target)
    archive_path = root / 'rules_package.zip'
    with ZipFile(archive_path, 'w', ZIP_DEFLATED) as archive:
        for name, path in files(target).items():
            info = ZipInfo(name, (2026, 10, 7, 0, 0, 0)); info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    receipt = {'status': 'pass', 'plan_sha256': locked['plan_sha256'],
        'archive_sha256': digest(archive_path.read_bytes()), 'archive_bytes': archive_path.stat().st_size,
        **transport_verify(target), 'case_count': len(cases), 'observations': len(cases) * 3, 'api_calls': 0}
    write_json(root / 'RULES_PACKAGE.json', receipt)
    print('PASS: 8 public cases, 24 A slots; ' + str(archive_path))
    return receipt


if __name__ == '__main__':
    make()
