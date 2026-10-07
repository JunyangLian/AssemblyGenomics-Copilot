"""Build a minimal package of exactly the already registered original A rules."""
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
from harness_common import BENCH, read_json, digest
from run_plan import verify as verify_plan
from transfer import manifest, verify


def build(root=BENCH):
    locked=verify_plan(root)
    package=root/'rules_package';verify(package)
    plan=read_json(package/'SERVER_PLAN.json')
    if plan['rule_sources']!=locked['plan']['rule_sources'] or plan['cases']!=[
            {**c,'visible_payload_sha256':next(r['visible_payload_sha256'] for r in plan['cases'] if r['case_id']==c['case_id'])}
            for c in locked['plan']['cases']]:
        raise ValueError('original package differs from approved inputs/rules')
    support=root/'rules_support'
    if support.exists(): raise ValueError('support already exists; preserve it')
    support.mkdir()
    for name,expected in plan['rule_sources'].items():
        data=(root.parent/name).read_bytes().replace(b'\r\n',b'\n')
        if digest(data)!=expected: raise ValueError('original source changed: '+name)
        dest=support/'original_rules'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    shutil.copyfile(root/'server/run_rules_support.py',support/'run.py')
    (support/'README.txt').write_bytes(('在服务器bench下：\n'
        'python -m zipfile -e server/rules_support.zip rules_support\n'
        'python rules_support/run.py\n'
        '需要已经解压的rules_package/；原规则副本和运行目录都只在bench内。\n'
        '最终回传bench_transfer/v1_rules_run_1/bundle整个目录。\n').encode('utf-8'))
    manifest(support);receipt=verify(support)
    with ZipFile(root/'rules_support.zip','w',ZIP_DEFLATED) as z:
        for p in sorted(support.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(support).as_posix())
    print(f'SUPPORT: {len(plan["rule_sources"])} unchanged original rule sources; {receipt["verified_bytes"]} bytes; 0 API calls')
    return support


if __name__=='__main__': build()
