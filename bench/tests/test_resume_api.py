"""Resume decisions must not silently resend or discard requests."""
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from resume_api import decision,collect
from harness_common import write_json,canonical,request,summary,digest,models
from seal_api import api_paths


def test_completed_and_reserved_slots_not_resent():
    key=('model','B','case_001',1)
    budget=SimpleNamespace(locked={'plan':{'slot_namespace':'old'}},state={'slots':['old:model:B:case_001:1:1']})
    assert decision(key,{}, {key:{}},budget)==('done',None)
    first={'status':'parse_error','attempt':0}
    assert decision(key,{key+(0,):first},{},budget)==('interrupted',1)
    budget.state['slots']=[]
    assert decision(key,{key+(0,):first},{},budget)==('send',1)
    first={'status':'api_error','attempt':0}
    assert decision(key,{key+(0,):first},{},budget)==('finalize',first)


def test_inherited_record_tamper_blocks_resume(tmp_path):
    p=tmp_path/'runs/parent/records.jsonl';p.parent.mkdir(parents=True);p.write_bytes(b'{}\n')
    locked={'plan':{'resume_sources':[{'path':'runs/parent/records.jsonl','sha256':digest(p.read_bytes())}],
        'parent_plan_sha256':'old','models':[],'cases':[]},'plan_sha256':'new'}
    p.write_bytes(b'changed\n')
    with pytest.raises(ValueError,match='changed'):collect(tmp_path,locked)


def test_api_receipt_excludes_mock_and_unadmitted_history(tmp_path):
    names=[]
    for name,mode,sha in [('mock','mock','current'),('api','api','parent'),('infra','api','old')]:
        p=tmp_path/'runs'/name/'records.jsonl';p.parent.mkdir(parents=True)
        p.write_bytes(canonical({'mode':mode,'plan_sha256':sha}));names.append(p.relative_to(tmp_path).as_posix())
    assert api_paths(tmp_path,names,{'current','parent'})==['runs/api/records.jsonl']
