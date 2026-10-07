"""Offline roundtrip uses a mocked rule executor, never pretends to run Linux rules."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest

BENCH=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BENCH))
import harness_common as hc
import import_rules
from make_rules_package import EXPORT
from transfer import manifest
from visible_input import packet, visible_files


@pytest.fixture
def roundtrip(tmp_path,monkeypatch):
    monkeypatch.setattr(sys,'dont_write_bytecode',True)
    bench=tmp_path/'repo/bench'; package=bench/'rules_package'
    package.mkdir(parents=True); (bench.parent/'scripts').mkdir()
    (bench.parent/'scripts/run_pitfall_checks.py').write_text('# offline fixture only\n')
    for name in EXPORT:
        for root in [bench,package]:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(BENCH/name,target)
    (bench/'schemas').mkdir();shutil.copyfile(BENCH/'schemas/model_output.schema.json',bench/'schemas/model_output.schema.json')
    case=BENCH/'cases/case_011'
    public={p.relative_to(case).as_posix():hc.digest(p.read_bytes()) for p in visible_files(case)}
    for root in [bench,package]:
        for name in public:
            target=root/'cases'/case.name/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(case/name,target)
    locked={'plan_sha256':'a'*64,'frozen_md_sha256':'b'*64,
            'plan':{'cases':[{'case_id':case.name,'public_files':public}],'rule_sources':{}}}
    plan={'format':1,'plan_sha256':locked['plan_sha256'],'frozen_md_sha256':locked['frozen_md_sha256'],
          'cases':[{'case_id':case.name,'public_files':public,'visible_payload_sha256':hc.digest(hc.canonical(packet(case)))}],
          'repetitions':3,'rule_sources':{},'adapter_files':{n:hc.digest((package/n).read_bytes()) for n in EXPORT},
          'output_root':'bench_transfer/offline_fixture/bundle','no_model_calls':True}
    hc.write_json(package/'SERVER_PLAN.json',plan);manifest(package)
    spec=importlib.util.spec_from_file_location('bench_server_rules_fixture',package/'server/run_rules.py')
    server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
    monkeypatch.setattr(server,'versions',lambda:{'python':'OFFLINE TEST FIXTURE'})
    monkeypatch.setattr(server,'evaluate_case',lambda *args:{'status':'not_covered','parsed':None,'checks':[],'error':None})
    server.execute(package,bench)
    monkeypatch.setattr(import_rules,'verify_plan',lambda root:locked)
    return bench,bench/plan['output_root'],locked


def test_server_roundtrip_idempotent_import(roundtrip):
    bench,bundle,locked=roundtrip
    result=import_rules.accept(bundle,bench)
    assert result['observations']==3 and result['counts']=={'not_covered':3}
    assert import_rules.accept(bundle,bench)==result
    assert not list((bench/'rules_package').rglob('expected.json'))
    assert not list((bench/'rules_package').rglob('meta.json'))


@pytest.mark.parametrize('mutation',['duplicate','payload','identity','simulated'])
def test_server_semantic_tamper_rejected_even_with_new_manifest(roundtrip,mutation):
    bench,bundle,locked=roundtrip
    path=bundle/'records.jsonl';rows=[json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    if mutation=='duplicate':rows[1]=rows[0]
    if mutation=='payload':rows[0]['request_summary']['visible_payload_sha256']='c'*64
    if mutation=='identity':rows[0]['plan_sha256']='c'*64
    if mutation=='simulated':rows[0]['simulated']=True
    path.write_bytes(b''.join(hc.canonical(r) for r in rows));manifest(bundle)
    with pytest.raises(ValueError):import_rules.accept(bundle,bench)


def test_transport_byte_tamper_rejected(roundtrip):
    bench,bundle,locked=roundtrip
    p=bundle/'records.jsonl';p.write_bytes(p.read_bytes()+b'changed\n')
    with pytest.raises(ValueError,match='SHA-256'):import_rules.accept(bundle,bench)


def use_parent_plan(bench,bundle,locked):
    locked['plan']['rule_mapping']={'PIT-006':{'verdict':'rollback','root_cause':'masking_mode_error'}}
    parent_path=bench/'plans/v1-run-1/RUN_PLAN.json'
    hc.write_json(parent_path,locked['plan'])
    sha=hc.digest(parent_path.read_bytes())
    locked['plan']['rules_parent_plan_sha256']=sha
    for name in ['STATUS.json','identity.json']:
        data=hc.read_json(bundle/name);data['plan_sha256']=sha;hc.write_json(bundle/name,data)
    path=bundle/'records.jsonl';rows=[json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    for row in rows:row['plan_sha256']=sha
    path.write_bytes(b''.join(hc.canonical(row) for row in rows));manifest(bundle)
    return parent_path


def test_same_rules_and_public_inputs_admit_original_server_plan(roundtrip):
    bench,bundle,locked=roundtrip
    use_parent_plan(bench,bundle,locked)
    assert import_rules.accept(bundle,bench)['observations']==3


def test_original_server_plan_archive_tamper_rejected(roundtrip):
    bench,bundle,locked=roundtrip
    path=use_parent_plan(bench,bundle,locked)
    path.write_bytes(path.read_bytes()+b'changed\n')
    with pytest.raises(ValueError,match='archive'):import_rules.accept(bundle,bench)
