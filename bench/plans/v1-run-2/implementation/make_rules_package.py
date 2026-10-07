"""Export only public inputs and rule-adapter code; never answers or credentials."""
from __future__ import annotations

import shutil
from zipfile import ZipFile, ZIP_DEFLATED

from harness_common import BENCH, digest, canonical, write_json
from run_plan import verify
from transfer import manifest
from visible_input import packet

EXPORT = ['server/run_rules.py', 'rule_adapter.py', 'transfer.py', 'visible_input.py']


def make(root=BENCH):
    locked = verify(root)
    target = root / 'rules_package'
    if target.exists():
        raise ValueError('rules_package already exists; preserve it or choose a new run plan version')
    target.mkdir()
    for name in EXPORT:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, dest)
    cases = []
    for row in locked['plan']['cases']:
        for name in row['public_files']:
            dest = target / 'cases' / row['case_id'] / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / 'cases' / row['case_id'] / name, dest)
        cases.append({**row, 'visible_payload_sha256':digest(canonical(packet(root / 'cases' / row['case_id'])))})
    write_json(target / 'SERVER_PLAN.json', {
        'format':1, 'plan_sha256':locked['plan_sha256'], 'frozen_md_sha256':locked['frozen_md_sha256'],
        'cases':cases, 'repetitions':3, 'rule_sources':locked['plan']['rule_sources'],
        'adapter_files':{n:digest((target / n).read_bytes()) for n in EXPORT},
        'output_root':'bench_transfer/v1_rules_run_1/bundle', 'no_model_calls':True})
    (target / 'README.txt').write_bytes(('在服务器 bench 下：\n'
        'python -m zipfile -e rules_package.zip rules_package\n'
        'python rules_package/server/run_rules.py\n'
        '回传 bench_transfer/v1_rules_run_1/bundle 整目录。\n'
        '只调用仓库原有规则，无模型/API/key/expected/meta。\n').encode('utf-8'))
    manifest(target)
    with ZipFile(root / 'rules_package.zip', 'w', ZIP_DEFLATED) as archive:
        for p in sorted(target.rglob('*')):
            if p.is_file():
                archive.write(p, p.relative_to(target).as_posix())
    return {'package':str(target), 'zip':str(root / 'rules_package.zip'),
            'manifest_sha256':digest((target / 'MANIFEST.json').read_bytes())}


if __name__ == '__main__':
    print(make())
