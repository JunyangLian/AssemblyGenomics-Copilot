"""Second-key recovery must preserve failures and never reopen successful slots."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import pytest
from bench.v2.credential_recovery import eligible, registered
from bench.v2.runtime import V2, canonical, digest, read_json, write_json
from bench.v2.concurrent_budget import ConcurrentBudget
from bench.v2.adapter import ApprovalError


def source_rows():
    rows=[]
    for rep,status,error in [(1,'api_error','HTTP 429'),(2,'api_error','transport/response failure: TimeoutError'),
                             (3,'parse_error','JSON/schema/evidence filename validation failed'),(4,'ok',None)]:
        base={'model':'model','group':'B','case_id':'case','repetition':rep}
        rows += [{**base,'record_type':'attempt','called':True,'error':error},
                 {**base,'record_type':'observation','status':status}]
    return rows


def fixture_registration(tmp_path):
    rows=source_rows(); failure=rows[1]
    write_json(tmp_path/'CREDENTIAL_RECOVERY.json',{'user_authorized':True,
        'budget_authorization_quote':'fixture explicit approval','parent_version':'old',
        'parent_plan_sha256':'parent','frozen_md_sha256':'f',
        'reason_filter':'HTTP 429 only; no QC-answer selection','automatic_network_retries':0,
        'recovery_observations':1,'slots':[{k:failure[k] for k in ('model','group','case_id','repetition')}
           | {'old_observation_sha256':digest(canonical(failure))}]})
    (tmp_path/'source.jsonl').write_bytes(b''.join(canonical(r) for r in rows))
    locked={'plan_sha256':'current','frozen_md_sha256':'f','plan':{'version':'new','parent_plan_sha256':'parent',
        'credential_recovery':{'file':'CREDENTIAL_RECOVERY.json','sha256':digest((tmp_path/'CREDENTIAL_RECOVERY.json').read_bytes())},
        'resume':{'parent_version':'old','records':'source.jsonl','records_sha256':digest((tmp_path/'source.jsonl').read_bytes())}}}
    return locked


def test_only_final_called_429_is_eligible_not_timeout_parse_or_success():
    rows=source_rows()
    assert set(eligible(rows))=={('model','B','case',1)}
    rows.insert(1,{**rows[0],'error':None})
    assert eligible(rows)=={}  # use final attempt, not an earlier intermediate failure


def test_recovery_requires_explicit_authorization_and_all_only_429(tmp_path):
    locked=fixture_registration(tmp_path)
    assert registered(tmp_path,locked)[1]=={('model','B','case',1)}
    doc=read_json(tmp_path/'CREDENTIAL_RECOVERY.json'); doc['budget_authorization_quote']=None
    write_json(tmp_path/'CREDENTIAL_RECOVERY.json',doc)
    locked['plan']['credential_recovery']['sha256']=digest((tmp_path/'CREDENTIAL_RECOVERY.json').read_bytes())
    with pytest.raises(ValueError,match='authorization'): registered(tmp_path,locked)
    doc['budget_authorization_quote']='fixture'; doc['slots'][0]['repetition']=2
    write_json(tmp_path/'CREDENTIAL_RECOVERY.json',doc)
    locked['plan']['credential_recovery']['sha256']=digest((tmp_path/'CREDENTIAL_RECOVERY.json').read_bytes())
    with pytest.raises(ValueError,match='all and only'): registered(tmp_path,locked)


def test_one_new_reservation_allowed_only_for_registered_parent_429(tmp_path,monkeypatch):
    locked=fixture_registration(tmp_path)
    monkeypatch.setattr('bench.v2.concurrent_budget.approval',lambda *args:{
        'max_calls':5,'max_input_tokens':1000000,'max_output_tokens':100000})
    write_json(tmp_path/'runs/API_LEDGER.json',{'calls':2,'input_reserved':200,'output_reserved':16384,
        'slots':[{'slot':'old:model:B:case:1:0'},{'slot':'old:model:B:case:4:0'}]})
    budget=ConcurrentBudget(tmp_path,locked)
    body={'messages':[{'role':'user','content':'fixture'}],'max_tokens':8192}
    budget.reserve('model:B:case:1:0',body)
    assert read_json(budget.path)['calls']==3  # old call retained, no refund
    with pytest.raises(ApprovalError,match='already reserved'): budget.reserve('model:B:case:1:0',body)
    with pytest.raises(ApprovalError,match='already reserved'): budget.reserve('model:B:case:4:0',body)
    budget.reserve('model:B:case:1:1',body)
    assert read_json(budget.path)['calls']==4


def test_actual_recovery_retains_original864_and_only_defers623_429():
    from bench.v2.plan import verify
    from bench.v2.resume import parent_records,rows
    locked=verify()
    old=rows(V2/'history/v2-run-7/resume_records.jsonl')
    original=[r for r in old if r['record_type']=='observation']
    assert len(original)==864 and len(eligible(old))==623
    assert sum(r['status']=='ok' for r in original)==202
    archived=rows(V2/'history/v2-run-8/resume_records.jsonl')
    carried=[r for r in archived if r['record_type']=='observation' and r.get('reused_from')]
    assert len(carried)==241
    assert sum(r['status']=='ok' for r in carried)==202
    assert sum(r['status']=='api_error' for r in carried)==24
    assert sum(r['status']=='parse_error' for r in carried)==13
    assert sum(r['status']=='interrupted' for r in carried)==2


def test_increased_budget_requires_exact_registered_recovery_caps(tmp_path):
    from bench.v2.plan import verify
    from bench.v2.adapter import approval
    locked=verify()
    recovery_file=locked['plan']['credential_recovery']['file']
    for name in (recovery_file,'MOCK_REPORT.json','API_APPROVAL.json'):
        (tmp_path/name).write_bytes((V2/name).read_bytes())
    doc=read_json(tmp_path/recovery_file)
    if doc.get('inherited_approval'):
        inherited=doc['inherited_approval']['file'];p=tmp_path/inherited;p.parent.mkdir(parents=True)
        p.write_bytes((V2/inherited).read_bytes())
    write_json(tmp_path/'MOCK_REPORT.json',{'status':'pass','plan_sha256':locked['plan_sha256'],'fixture_only':True})
    a=read_json(tmp_path/'API_APPROVAL.json')
    a['mock_report_sha256']=digest((tmp_path/'MOCK_REPORT.json').read_bytes())
    write_json(tmp_path/'API_APPROVAL.json',a)
    assert approval(tmp_path,locked)['max_calls']==2636
    a=read_json(tmp_path/'API_APPROVAL.json');a['max_calls']+=1
    write_json(tmp_path/'API_APPROVAL.json',a)
    with pytest.raises(ApprovalError,match='explicitly approved'):approval(tmp_path,locked)
    a['max_calls']=2636;a['user_credential_recovery_authorization_quote']=None
    write_json(tmp_path/'API_APPROVAL.json',a)
    with pytest.raises(ApprovalError,match='explicitly approved'):approval(tmp_path,locked)
    # A large cap without any recovery registration stays forbidden.
    other={**locked,'plan':{**locked['plan']}}
    other['plan'].pop('credential_recovery')
    with pytest.raises(ApprovalError,match='preregistered slots'):approval(tmp_path,other)


def test_new_429_stops_dispatch_preserving_unattempted_recovery_jobs(tmp_path,monkeypatch):
    from bench.v2 import parallel
    models=[{'name':'a'},{'name':'b'}]
    plan={'models':models,'groups':['B'],'cases':[{'case_id':'case1'},{'case_id':'case2'}],
        'mock_seed':1,'execution':{'max_workers':2},'credential_recovery':{'file':'fixture'}}
    locked={'plan':plan,'plan_sha256':'current','frozen_md_sha256':'f'}
    directories={}
    for m in models:
        directory=tmp_path/'runs'/m['name']; directory.mkdir(parents=True)
        (directory/'records.jsonl').write_bytes(b'');directories['B',m['name']]=directory
    write_json(tmp_path/'API_RUNS.json',{'runs':['runs/a','runs/b']})
    monkeypatch.setattr(parallel,'prepare_api',lambda *args:(directories,{},set()))
    monkeypatch.setattr(parallel,'OpenAICompatible',lambda *args:object())
    called=[]
    def observe(case,group,model,client,repeat,lock,emit,root):
        called.append((model['name'],case.name,repeat))
        row={'record_type':'observation','mode':'api','model':model['name'],'group':group,
             'case_id':case.name,'repetition':repeat,'status':'api_error','error':'HTTP 429',
             'plan_sha256':'current','frozen_md_sha256':'f'}
        emit(row); return row
    parallel.execute('api',tmp_path,locked,None,{},lambda *args:'unused',observe)
    status=read_json(tmp_path/'runs/SCHEDULER_STATUS.json')
    assert (tmp_path/'runs/STOP_AFTER_CURRENT_REQUEST').exists()
    assert 1<=len(called)<=2
    assert status['pending']+status['completed']==12
    assert status['pending']>=10 and status['active']==[] and status['stop_requested'] is True
