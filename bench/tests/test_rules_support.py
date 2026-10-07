"""Offline tests for layout only; never run Linux biological checks on Windows."""
import importlib.util
from pathlib import Path
import shutil
import sys

import pytest

BENCH=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BENCH))
from harness_common import read_json
from transfer import manifest,verify
from server import run_rules_support as support


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    bench=tmp_path/'data_only/bench';bench.mkdir(parents=True)
    package=bench/'rules_package';shutil.copytree(BENCH/'rules_package',package)
    base=bench/'rules_support';base.mkdir()
    shutil.copyfile(BENCH/'server/run_rules_support.py',base/'run.py')
    plan=read_json(package/'SERVER_PLAN.json')
    for name in plan['rule_sources']:
        p=base/'original_rules'/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes((BENCH.parent/name).read_bytes().replace(b'\r\n',b'\n'))
    manifest(base)
    spec=importlib.util.spec_from_file_location('offline_original_server_support',package/'server/run_rules.py')
    server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
    monkeypatch.setattr(server,'versions',lambda:{'python':'OFFLINE FIXTURE'})
    monkeypatch.setattr(server,'evaluate_case',lambda *args:{'status':'not_covered','parsed':None,'checks':[],'error':None})
    monkeypatch.setattr(support,'load_server',lambda p:server)
    return bench,base,plan


def test_data_only_parent_and_repeat_execution(fixture):
    bench,base,plan=fixture
    assert not (bench.parent/'scripts').exists()
    for _ in range(2):
        out,status=support.execute(base)
        assert out==bench/'bench_transfer/v1_rules_run_1/bundle'
        assert status['observations']==48 and status['counts']=={'not_covered':48}
        assert verify(out)['verified_files']>0
        assert verify(base)['verified_files']==len(plan['rule_sources'])+1
        layout=read_json(out/'execution_layout.json')
        assert layout['original_rule_sources']==plan['rule_sources'] and not layout['verdict_mapping_changed']


def test_changed_original_rule_is_rejected_even_with_fresh_transport_manifest(fixture,monkeypatch):
    bench,base,plan=fixture
    p=base/'original_rules/scripts/run_pitfall_checks.py';p.write_bytes(p.read_bytes()+b'\n# altered\n')
    manifest(base)
    monkeypatch.setattr(support,'load_server',lambda p:pytest.fail('executor reached after altered source'))
    with pytest.raises(ValueError,match='source identity differs'):support.execute(base)


def test_extra_baseline_rule_rejected(fixture,monkeypatch):
    bench,base,plan=fixture
    p=base/'original_rules/knowledge/baselines/extra.yaml';p.write_bytes(b'extra: true\n');manifest(base)
    monkeypatch.setattr(support,'load_server',lambda p:pytest.fail('executor reached after new rule'))
    with pytest.raises(ValueError,match='source set differs'):support.execute(base)
