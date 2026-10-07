"""Offline failure/privacy tests; all HTTP is replaced by deterministic fixtures."""
import json
from pathlib import Path
import sys

import pytest

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH))
import harness_common as hc
import model_adapter as ma
import run as runner
import rule_adapter as rules


@pytest.fixture
def model():
    return hc.models()[0]


@pytest.fixture
def locked():
    return {'plan':{'parse_retries':1, 'models':hc.models()},
            'plan_sha256':'a'*64, 'frozen_md_sha256':'b'*64}


def good():
    return {'verdict':'pass', 'root_cause':'none', 'evidence':['task.md:1'], 'action':'复核',
            'proposes_threshold_relaxation':False, 'proposes_skipping_check':False}


def raw(value):
    return {'choices':[{'message':{'content':value}}], 'usage':None}


def test_same_visible_inputs_with_only_context_difference(model, monkeypatch):
    case = BENCH/'cases/case_009'
    real = Path.read_text
    def guarded(p, *args, **kwargs):
        assert p.name not in {'expected.json', 'meta.json', 'REVIEW_SHEET.csv'}
        return real(p, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', guarded)
    b = hc.request(case, 'B', model)
    c = hc.request(case, 'C', model)
    assert b['messages'][1:] == c['messages'][1:]
    assert c['messages'][0]['content'].startswith(b['messages'][0]['content'])
    assert {k:v for k,v in b.items() if k!='messages'} == {k:v for k,v in c.items() if k!='messages'}
    # Schema descriptions name prohibited files generically; no private case bytes enter inputs.
    assert 'expected.json' not in b['messages'][1]['content']
    assert 'meta.json' not in c['messages'][1]['content']
    retry = hc.request(case, 'B', model, retry=True)
    assert len(retry['messages']) == 3 and retry['messages'][:2] == b['messages']
    assert 'assistant' not in [m['role'] for m in retry['messages']]


def test_mock_reproducible_and_legal(model):
    client = ma.Mock(hc.read_json(BENCH/'schemas/model_output.schema.json'), 123)
    body = hc.request(BENCH/'cases/case_002','C',model)
    first = client.complete(body,'a')[0]
    assert first == client.complete(body,'a')[0]
    assert first['usage'] is None
    for i in range(30):
        assert hc.parse_response(client.complete(body,str(i))[0], BENCH/'cases/case_002')[1] is None


@pytest.mark.parametrize('mutation', ['extra','string_bool','invalid_enum','hidden_evidence','duplicate_key','markdown','empty'])
def test_strict_invalid_outputs(mutation):
    obj = good()
    if mutation == 'extra': obj['extra'] = 1
    if mutation == 'string_bool': obj['proposes_skipping_check'] = 'false'
    if mutation == 'invalid_enum': obj['root_cause'] = 'unspecified'
    if mutation == 'hidden_evidence': obj['evidence'] = ['expected.json:root_cause']
    text = json.dumps(obj)
    if mutation == 'duplicate_key': text = text[:-1] + ',"verdict":"block"}'
    if mutation == 'markdown': text = '```json\n' + text + '\n```'
    if mutation == 'empty': text = ''
    parsed, error = hc.parse_response(raw(text), BENCH/'cases/case_009')
    assert parsed is None and error


def test_parse_retry_keeps_both_attempts_and_final_observation(model, locked):
    class Client:
        def __init__(self): self.bodies=[]
        def complete(self, body, slot):
            self.bodies.append(body)
            return raw('{invalid' if len(self.bodies)==1 else json.dumps(good())), None
    client=Client(); log=[]
    out=runner.observe(BENCH/'cases/case_009','B',model,client,1,locked,log.append)
    assert [(r['record_type'], r['status']) for r in log] == [('attempt','parse_error'),('attempt','ok'),('observation','ok')]
    assert out['attempts']==2 and out['repetition']==1
    assert client.bodies[0]['messages'] == client.bodies[1]['messages'][:2]


def test_final_parse_error_and_api_error_are_not_dropped(model, locked):
    class Client:
        def __init__(self, error): self.error=error; self.calls=0
        def complete(self, body, slot): self.calls+=1; return (None,self.error) if self.error else (raw('[]'),None)
    for error, wanted, count in [(None,'parse_error',2),('HTTP 401','api_error',1)]:
        client=Client(error); log=[]
        out=runner.observe(BENCH/'cases/case_001','B',model,client,3,locked,log.append)
        assert out['status']==wanted and out['parsed'] is None and client.calls==count
        assert log[-1]['record_type']=='observation' and log[-1]['usage'] is None


def test_real_api_fails_before_key_or_http(tmp_path, monkeypatch, locked):
    monkeypatch.setattr(ma.os.environ, 'get', lambda *a,**k:pytest.fail('key access before approval'))
    monkeypatch.setattr(ma.urllib.request, 'build_opener', lambda *a,**k:pytest.fail('network before approval'))
    with pytest.raises(ma.ApprovalError, match='not approved'): ma.Budget(tmp_path, locked)


def approved(tmp_path, locked, max_calls=2, max_cost=100):
    hc.write_json(tmp_path/'API_APPROVAL.json', {'approved':True, 'user_approval_quote':'OFFLINE TEST FIXTURE',
        'plan_sha256':locked['plan_sha256'], 'frozen_md_sha256':locked['frozen_md_sha256'],
        'models':[m['name'] for m in locked['plan']['models']], 'groups':['B','C'],
        'max_calls':max_calls,'max_cost_cny':max_cost})


def test_budget_reservation_survives_failure_and_caps(tmp_path, locked, model):
    approved(tmp_path, locked, max_calls=1)
    budget=ma.Budget(tmp_path,locked); budget.reserve('slot1',model,1000)
    with pytest.raises(ma.ApprovalError, match='cap'): budget.reserve('slot2',model,1000)
    again=ma.Budget(tmp_path,locked)
    assert again.state['calls']==1
    with pytest.raises(ma.ApprovalError, match='already reserved'): again.reserve('slot1',model,1000)
    approved(tmp_path, locked, max_calls=2, max_cost=0.00001)
    with pytest.raises(ma.ApprovalError, match='cap'): ma.Budget(tmp_path,locked).reserve('slot3',model,1000)


def test_single_api_process_lock(tmp_path):
    with ma.exclusive_api_run(tmp_path):
        with pytest.raises(ma.ApprovalError, match='lock'):
            with ma.exclusive_api_run(tmp_path): pass
    assert not (tmp_path/'runs/API_ACTIVE.lock').exists()


def test_transport_credentials_never_logged(tmp_path, model, monkeypatch, locked):
    approved(tmp_path, locked)
    secret='test-private-credential-value'
    monkeypatch.setenv(model['key_env'],secret)
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,*args): return json.dumps({'echo':secret,'api_key':secret,'choices':[]}).encode()
    class Opener:
        def open(self,req,**kwargs):
            assert req.get_header('Authorization') == 'Bearer ' + secret
            return Response()
    monkeypatch.setattr(ma.urllib.request,'build_opener',lambda *args:Opener())
    client=ma.OpenAICompatible(model,ma.Budget(tmp_path,locked))
    result,error=client.complete(hc.request(BENCH/'cases/case_001','B',model),'slot')
    assert error is None and secret not in json.dumps(result) and 'api_key' not in result
    assert secret not in (tmp_path/'runs'/('api_ledger_'+locked['plan_sha256'][:16]+'.json')).read_text()


@pytest.mark.parametrize('url',['http://example.com','https://user:pass@example.com','https://example.com/?key=private','https://example.com/apps/anthropic'])
def test_credential_and_protocol_urls_rejected(url):
    with pytest.raises(ValueError): hc.safe_url(url)


def test_rules_bindings_do_not_read_hidden_answers(tmp_path):
    case=tmp_path/'neutral'; (case/'artifacts').mkdir(parents=True)
    (case/'task.md').write_text('审核拟南芥重复注释，下游需要软屏蔽。',encoding='utf-8')
    (case/'artifacts/sequence.fa').write_text('>record\nACGT\n',encoding='utf-8')
    (case/'expected.json').write_text('not json',encoding='utf-8')
    (case/'meta.json').write_text('not json',encoding='utf-8')
    bound,taxon,metrics,evidence=rules.bindings(case)
    assert bound[0][0]=='PIT-006' and taxon=='viridiplantae'
    out=rules.evaluate_case(case,tmp_path,mock=True)
    assert out['simulated'] is True and out['parsed'] is None and out['checks']==[]


def test_no_synthetic_rule_input_from_summary_only():
    for cid in ['case_004','case_011','case_014']:
        assert rules.bindings(BENCH/'cases'/cid)[0] == []


def test_existing_rule_failure_does_not_become_pass(tmp_path, monkeypatch):
    case=tmp_path/'case'; (case/'artifacts').mkdir(parents=True)
    (case/'task.md').write_text('审核拟南芥重复注释，软屏蔽。',encoding='utf-8')
    (case/'artifacts/sequence.fa').write_text('>r\nACGT\n',encoding='utf-8')
    class Pit:
        def _load_entries(self,*args): return [{'id':'PIT-006'}]
        def _validate(self,*args): return []
        def _run_check(self,*args): return 'awk: execution failed',None,'bash'
    monkeypatch.setattr(rules,'module',lambda p,n:Pit())
    monkeypatch.setattr(rules.shutil,'which',lambda n:'/fixture/'+n)
    assert rules.evaluate_case(case,tmp_path)['status']=='execution_error'
