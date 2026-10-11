"""Real-source joins, narrow mutations, answer isolation and native limit regression."""
import copy
import json
from pathlib import Path

import pytest
from bench.inspect_adapter import t3_packets as p, t3_task as task
from bench.inspect_adapter.readonly import PublicFiles


@pytest.fixture(scope='module')
def selected():
    return p.read_json(p.DIRECTORY/'selection/SOURCE_SUBSETS.json')


def test_real_source_pairs_remain_draft_with_complete_provenance(selected):
    packets=p.generate(selected)
    actual=p.validate(packets)
    assert len(actual)==14
    assert len({v['source_group'] for v in actual.values()})==7
    assert all(v['visible_bytes']<=30000 for v in actual.values())
    for cid,files in packets.items():
        expected=json.loads(files['expected.json']);meta=json.loads(files['meta.json'])
        assert not expected['user_approved'] and expected['independent_review_status']=='pending'
        assert meta['synthetic'] and len(meta['source_files'])==2
        assert all(len(s['sha256'])==64 and s['source_origin'].startswith('/home/') for s in meta['source_files'])
        assert not any(b'\r' in value for value in files.values())
    for i in range(1,8):
        a,b=[packets[f't3_{2*i-1+offset:03d}'] for offset in (0,1)]
        assert all(a[n]==b[n] for n in ('task.md','artifacts/proteins.faa','artifacts/record_counts.json'))
        assert a['artifacts/models.gff3']!=b['artifacts/models.gff3']


def test_no_new_rule_or_upstream_cause_inference(selected):
    for clade,mode in p.ASSIGNMENT:
        source=selected[clade]
        assert not any(p.relations(source['rows'],source['proteins']).values())
        altered,detail=p.change(source['rows'],source['proteins'],mode)
        assert p.surface(altered,source['proteins'])==p.surface(source['rows'],source['proteins'])
        if mode=='protein':
            a=[p.attributes(r) for r in source['rows'] if r[2]=='CDS']
            b=[p.attributes(r) for r in altered if r[2]=='CDS']
            assert all(x['ID']==y['ID'] and x.get('Name')==y.get('Name') for x,y in zip(a,b))
            assert p.relations(altered,source['proteins'])['missing_sequence_lines']
        elif mode=='parent':
            assert p.relations(altered,source['proteins'])['unresolved_parent_lines']
        else:
            assert p.relations(altered,source['proteins'])['incompatible_parent_lines']


def test_partial_and_multi_segment_are_valid_within_declared_contract(selected):
    rows=copy.deepcopy(selected['fungi']['rows'])
    assert len([r for r in rows if r[2]=='CDS'])>len(selected['fungi']['proteins'])
    for row in rows:
        if 'partial=' not in row[8]:
            row[8]+=';partial=true'
    assert not any(p.relations(rows,selected['fungi']['proteins']).values())


def test_faa_duplicate_and_missing_sequences_rejected():
    with pytest.raises(ValueError,match='duplicate'):
        p.fasta_records('>XP_1.1\nAA\n>XP_1.1\nBB\n')
    with pytest.raises(ValueError,match='empty FAA'):
        p.fasta_records('>XP_1.1\n')


def test_validation_catches_wrong_cause_and_nonexisting_evidence(selected):
    packets=p.generate(selected)
    expected=json.loads(packets['t3_002']['expected.json'])
    expected['acceptable_decisions'][0]['root_cause']='gff_hierarchy_error'
    packets['t3_002']['expected.json']=p.canonical(expected)
    with pytest.raises(ValueError,match='labels disagree'):
        p.validate(packets)
    packets=p.generate(selected)
    expected=json.loads(packets['t3_001']['expected.json'])
    expected['key_evidence'][0]['acceptable_pointers']=['artifacts/models.gff3:99999']
    packets['t3_001']['expected.json']=p.canonical(expected)
    with pytest.raises(ValueError,match='missing evidence line'):
        p.validate(packets)


def test_model_messages_do_not_read_answers_or_metadata(monkeypatch):
    public=PublicFiles(p.DIRECTORY/'cases/t3_002')
    original=Path.read_bytes
    def guard(path):
        if path.name in {'expected.json','meta.json','SOURCE_SUBSETS.json'}:
            raise AssertionError('private input read')
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',guard)
    for condition in task.CONDITIONS:
        text=json.dumps(task.messages(public,condition),ensure_ascii=False)
        assert 't3_002' not in text and 'T3P1' not in text
        assert 'expected.json' not in text and 'meta.json' not in text
    with pytest.raises(ValueError,match='whitelist'):
        public.text('expected.json')


def test_structured_scorer_requires_an_allowed_complete_combination():
    target={'acceptable_decisions':[{'verdict':'pass','observed_defect':'none','root_cause':'none'},
        {'verdict':'block','observed_defect':'gff_faa_link_missing','root_cause':'id_mismatch'}]}
    mixed={'verdict':'pass','observed_defect':'gff_faa_link_missing','root_cause':'id_mismatch'}
    score=task.label_values(mixed,target)
    assert score['root_correct']==score['verdict_correct']==1
    assert score['decision_joint_correct']==0


def test_extra_public_file_is_rejected(tmp_path,monkeypatch,selected):
    packets=p.generate(selected)
    for cid,files in packets.items():
        for name,data in files.items():
            path=tmp_path/'cases'/cid/name
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    p.write_json(tmp_path/'CASE_MANIFEST.json',{'files':{cid+'/'+name:p.digest(data)
        for cid,files in packets.items() for name,data in files.items()}})
    (tmp_path/'cases/t3_001/artifacts/extra.txt').write_bytes(b'Unexpected public record\n')
    monkeypatch.setattr(task,'DIRECTORY',tmp_path)
    with pytest.raises(ValueError,match='unexpected case file'):
        task.checked_cases()


def test_frozen_prepare_cannot_overwrite_selection_or_schemas(tmp_path,monkeypatch):
    (tmp_path/'FROZEN.json').write_bytes(b'{}\n')
    monkeypatch.setattr(p,'DIRECTORY',tmp_path)
    for method in (p.prepare,p.extract,p.build):
        with pytest.raises(ValueError,match='frozen'):
            method()


def test_plan_budget_and_analysis_cannot_be_interpreted_as_authorization(tmp_path,monkeypatch):
    plan=p.read_json(p.DIRECTORY/'PLAN.draft.json')
    assert plan['planned_observations']==14*2*3
    assert plan['max_http_requests_proposed']==42*(1+6)
    assert plan['max_output_token_reservation_proposed']==42*(2048+5*512+2048)
    assert not plan['api_call_authorized'] and not plan['answers_frozen']
    assert plan['cost_cny'] is None and plan['analysis']['primary_unit']=='case'
    (tmp_path/'FROZEN.json').write_bytes(b'{}\n')
    monkeypatch.setattr(task,'DIRECTORY',tmp_path)
    with pytest.raises(ValueError,match='frozen'):
        task.prepare_plan()


def test_native_multi_tool_rounds_reach_final_and_old_cap_does_not(tmp_path):
    log,calls=task.run_probe('tools',tmp_path/'new',task.CASE_IDS[:1])
    sample=log.samples[0]
    assert len(calls)==6 and calls[-1]['max_tokens']==2048
    assert sample.metadata['final_submission_scheduled'] and len(sample.messages)>16
    assert len([m for m in sample.messages if m.role=='tool'])==25
    assert next(iter(sample.scores.values())).value['valid_output']==1
    old,calls=task.run_probe('tools',tmp_path/'old',task.CASE_IDS[:1],message_limit=16)
    assert not old.samples[0].metadata.get('final_submission_scheduled')
    assert all(c['tools_enabled'] for c in calls)
