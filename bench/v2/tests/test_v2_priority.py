"""Paused models retain results and cannot receive paid requests."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from collections import Counter
import pytest
from bench.v2.runtime import V2,read_json,write_json
from bench.v2.credential_recovery import registered,duplicate_allowed,slot


def test_priority_retains_both_deferred_models_and_only_opens_four_429_queues():
    from bench.v2.plan import verify
    from bench.v2.resume import parent_records,rows
    locked=verify();doc,allowed=registered(V2,locked)
    assert len(allowed)==271
    assert not any(k[0] in ('GLM-5.3','Kimi-K2.6') for k in allowed)
    carried=[r for r in parent_records(V2,locked) if r['record_type']=='observation']
    assert len(carried)==375
    parked=[r for r in carried if r['model'] in ('GLM-5.3','Kimi-K2.6')]
    assert Counter(r['model'] for r in parked)=={'GLM-5.3':31,'Kimi-K2.6':39}
    assert all(r.get('reused_from') for r in parked)
    original=[r for r in rows(V2/'history/v2-run-8/resume_records.jsonl') if r['record_type']=='observation']
    assert len(original)==376  # source never trimmed to four models
    assert Counter(r['status'] for r in carried)=={'ok':316,'api_error':37,'parse_error':20,'interrupted':2}
    key=('MiniMax-M3','B','new_019',2)
    assert key in allowed
    semantic='MiniMax-M3:B:new_019:2:0'
    assert duplicate_allowed(doc,allowed,'v2-run-7',semantic)
    assert duplicate_allowed(doc,allowed,'v2-run-8',semantic)
    assert not duplicate_allowed(doc,allowed,'v2-run-9',semantic)
    assert not duplicate_allowed(doc,allowed,'v2-run-7','MiniMax-M3:B:new_019:1:0')


def test_api_priority_never_creates_clients_or_calls_for_deferred_models(tmp_path,monkeypatch):
    from bench.v2 import parallel
    names=['a','b','c','d','parked1','parked2'];active=names[:4]
    plan={'models':[{'name':n} for n in names],'groups':['B'],'cases':[{'case_id':'case'}],
        'mock_seed':1,'execution':{'max_workers':4,'active_model_names':active}}
    locked={'plan':plan,'plan_sha256':'p','frozen_md_sha256':'f'}
    dirs={}
    for n in names:
        p=tmp_path/'runs'/n;p.mkdir(parents=True);(p/'records.jsonl').write_bytes(b'');dirs['B',n]=p
    # A parked result already present must survive unchanged.
    parked={'record_type':'observation','mode':'api','model':'parked1','group':'B',
        'case_id':'case','repetition':1,'status':'ok','plan_sha256':'p','frozen_md_sha256':'f'}
    from bench.v2.runtime import canonical
    (dirs['B','parked1']/'records.jsonl').write_bytes(canonical(parked))
    original=(dirs['B','parked1']/'records.jsonl').read_bytes()
    write_json(tmp_path/'API_RUNS.json',{'runs':['runs/'+n for n in names]})
    monkeypatch.setattr(parallel,'prepare_api',lambda *args:(dirs,{slot(parked):parked},set()))
    clients=[];calls=[]
    def client(model,*args):clients.append(model['name']);return object()
    monkeypatch.setattr(parallel,'OpenAICompatible',client)
    def observe(case,group,model,client,rep,lock,emit,root):
        calls.append((model['name'],rep));emit({**parked,'model':model['name'],'repetition':rep})
        return {'status':'ok'}
    parallel.execute('api',tmp_path,locked,None,{},lambda *args:'unused',observe)
    assert set(clients)==set(active) and len(calls)==12
    assert not any(n.startswith('parked') for n,_ in calls)
    assert (dirs['B','parked1']/'records.jsonl').read_bytes()==original
    assert (dirs['B','parked2']/'records.jsonl').read_bytes()==b''
