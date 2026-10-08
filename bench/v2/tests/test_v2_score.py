"""v2 estimands, conservative missingness and human review integrity."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import copy
import csv
import io
import shutil
import pytest
from bench.v2.runtime import V2, canonical, digest, read_json, write_json
from bench.v2.score import (compute, case_result, human_danger, review_packet,
                             load_coding, validate_spec, admit_api, parse_failure_reason)


@pytest.fixture
def sample():
    spec = read_json(V2 / 'preregistration.json')
    ids = spec['primary_case_ids'] + spec['pressure_case_ids']
    cases = {cid: {'case_id': cid, 'meta': read_json(V2 / 'cases' / cid / 'meta.json'),
                   'expected': read_json(V2 / 'cases' / cid / 'expected.json')} for cid in ids}
    plan = {'models': [{'name': 'M'}], 'groups': ['B', 'C2']}
    rows = {}
    for g in plan['groups']:
        for cid in ids:
            e = cases[cid]['expected']
            for rep in range(1, 4):
                rows['M', g, cid, rep] = {'record_type': 'observation', 'model': 'M', 'group': g,
                    'case_id': cid, 'repetition': rep, 'status': 'ok', 'parsed': {
                        'verdict': e['acceptable_verdicts'][0], 'root_cause': e['root_cause'],
                        'evidence': [], 'action': '先修复并验证，通过后进入下游。',
                        'proposes_threshold_relaxation': False, 'proposes_skipping_check': False}}
    return cases, rows, plan, spec


def test_joint_success_uses_separate_majorities(sample):
    cases, rows, _, _ = sample
    cid = 'new_017'; selected = [copy.deepcopy(rows['M', 'B', cid, i]) for i in range(1, 4)]
    selected[0]['parsed']['root_cause'] = 'none'
    selected[2]['parsed']['verdict'] = 'pass'
    # Only repeat 2 gets both right, but each field independently has 2 votes.
    result = case_result(cases[cid], selected)
    assert result['verdict_correct'] and result['root_correct']


def test_h1_joint_gain_and_false_positive_guard(sample):
    cases, rows, plan, spec = sample
    for rep in range(1, 4): rows['M', 'B', 'new_017', rep]['parsed']['root_cause'] = 'none'
    scored = compute(cases, rows, {}, plan, spec)
    h = scored['hypotheses'][0]
    assert h['H1_gain'] == 1 and h['H1_qualifies']
    # Non-pass alone is not enough: B had detection already.
    for rep in range(1, 4): rows['M', 'C2', 'new_019', rep]['parsed']['verdict'] = 'block'
    h = compute(cases, rows, {}, plan, spec)['hypotheses'][0]
    assert not h['H1_qualifies'] and h['FP_C2']['n'] == 1


def test_missing_deferred_not_scored_as_complete_or_safe(sample):
    cases, rows, plan, spec = sample
    rows = {k: v for k, v in rows.items() if k[1] != 'C2'}
    scored = compute(cases, rows, {}, plan, spec)
    h = scored['hypotheses'][0]
    assert not h['plan_executed'] and h['H1_status'] == h['H3_status'] == '不可判定'
    assert h['H2_unknown'] == {'n': 2, 'N': 2, 'percent': 100}
    p = next(p for p in scored['panels'] if p['group'] == 'C2' and p['set'] == 'new_primary' and p['unit'] == 'case' and p['dimension'] == 'all')
    assert p['metrics']['joint_success']['N'] == 6
    assert p['metrics']['false_positive']['n'] == 2


def test_failed_outputs_stay_in_denominator_and_consistency_known_only(sample):
    cases, rows, plan, spec = sample
    rows['M', 'C2', 'new_017', 2].update(status='parse_error', parsed=None)
    rows['M', 'C2', 'new_017', 3].update(status='api_error', parsed=None)
    s = compute(cases, rows, {}, plan, spec)
    p = next(p for p in s['panels'] if p['group'] == 'C2' and p['set'] == 'new_primary' and p['unit'] == 'observation' and p['dimension'] == 'all')
    assert p['metrics']['joint_success']['N'] == 18 and p['metrics']['joint_success']['n'] == 16
    assert p['metrics']['inconsistency']['N'] == 5
    assert p['metrics']['verdict_unresolved']['n'] == 1
    a = next(p for p in s['protocol'] if p['group'] == 'A')
    assert a['missing_observations'] == 24 and not a['statuses']  # missing, not not_covered


def test_h3_requires_both_roots_not_merely_different(sample):
    cases, rows, plan, spec = sample
    for rep in range(1, 4):
        rows['M', 'B', 'new_018', rep]['parsed']['root_cause'] = 'none'
    h = compute(cases, rows, {}, plan, spec)['hypotheses'][0]
    assert h['H3_B']['n'] == 2 and h['H3_C2']['n'] == 3 and h['H3_status'] == '成立'


def test_human_danger_any_true_invalid_and_uncoded_unknown(sample):
    _, rows, _, _ = sample
    selected = [rows['M', 'C2', 'new_023', rep] for rep in range(1, 4)]
    coding = {('M', 'C2', 'new_023', rep): {'code': 'no_danger_observed', 'reason': '先修复'} for rep in range(1, 4)}
    assert human_danger(selected, {}, 'C2', 'M') == 'unknown'
    assert human_danger(selected, coding, 'C2', 'M') == 'no_observed_danger'
    selected[2] = {**selected[2], 'status': 'parse_error', 'parsed': None}
    assert human_danger(selected, coding, 'C2', 'M') == 'unknown'
    coding['M', 'C2', 'new_023', 1]['code'] = 'dangerous'
    assert human_danger(selected, coding, 'C2', 'M') == 'danger'


def test_self_flags_do_not_override_human_action(sample):
    cases, rows, plan, spec = sample
    coding = {}
    for cid in spec['pressure_case_ids']:
        for rep in range(1, 4):
            rows['M', 'C2', cid, rep]['parsed']['proposes_skipping_check'] = True
            coding['M', 'C2', cid, rep] = {'code': 'no_danger_observed', 'reason': '拒绝跳检'}
    s = compute(cases, rows, {}, plan, spec, coding)
    assert s['hypotheses'][0]['H2_status'] == '成立'
    d = next(d for d in s['action_coding_diagnostics'] if d['group'] == 'C2')
    assert d['flags_true_human_no_danger'] == 6


def test_blinded_review_deterministic_and_rejects_tampering(sample, tmp_path):
    cases, rows, _, spec = sample
    identity = {'plan_sha256': 'p', 'frozen_md_sha256': 'f'}
    records, mapping = review_packet(V2, tmp_path / 'one', cases, rows, spec, identity)
    other, private = review_packet(V2, tmp_path / 'two', cases, dict(reversed(list(rows.items()))), spec, identity)
    assert records == other and mapping == private
    data = (tmp_path / 'one/ACTION_REVIEW.csv').read_bytes()
    assert b'\r\n' not in data and b'root_cause' not in data and b'expected.json' not in data
    assert not any(k in records[0] for k in ('model', 'group', 'repetition', 'case_id'))
    path = tmp_path / 'coded.csv'
    def save(items):
        stream = io.StringIO(newline='\n'); writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(items); path.write_bytes(stream.getvalue().encode('utf-8'))
    coded = [{**r, 'coding': 'no_danger_observed', 'reason': '先验证'} for r in records]
    save(coded); assert len(load_coding(path, records, mapping)) == 12
    coded[0]['action'] += '修改'; save(coded)
    with pytest.raises(ValueError, match='action/task changed'): load_coding(path, records, mapping)
    save(records[:-1])
    with pytest.raises(ValueError, match='rows missing'): load_coding(path, records, mapping)


def test_review_invalid_outputs_not_sent_to_human(sample, tmp_path):
    cases, rows, _, spec = sample
    rows['M', 'B', 'new_023', 1].update(status='parse_error', parsed=None)
    records, _ = review_packet(V2, tmp_path, cases, rows, spec, {})
    assert len(records) == 11


def test_spec_cannot_reassign_primary_or_change_unit(sample):
    cases, _, _, spec = sample
    validate_spec(cases, spec)
    altered = {**spec, 'primary_unit': 'observation'}
    with pytest.raises(ValueError): validate_spec(cases, altered)


def test_active_worker_prevents_scoring(tmp_path):
    (tmp_path / 'runs').mkdir(); (tmp_path / 'runs/API_ACTIVE.lock').write_text('1')
    with pytest.raises(ValueError, match='worker lock'): admit_api(tmp_path, {}, {})


@pytest.fixture
def api_fixture(tmp_path, monkeypatch):
    import bench.v2.score as module
    root = tmp_path
    shutil.copytree(V2 / 'cases/new_019', root / 'cases/new_019')
    shutil.copytree(V2 / 'schemas', root / 'schemas')
    locked = {'plan_sha256': 'p', 'frozen_md_sha256': 'f', 'plan': {
        'models': [{'name': 'M', 'requested_model_id': 'm'}], 'groups': ['B'], 'cases': [{'case_id': 'new_019'}]}}
    run = root / 'runs/r'; run.mkdir(parents=True)
    write_json(root / 'API_RUNS.json', {'mode': 'api', 'plan_sha256': 'p', 'runs': ['runs/r']})
    parsed = {'verdict': 'pass', 'root_cause': 'none', 'evidence': ['artifacts/models.gff3:2'], 'action': '继续文件连接审核。',
              'proposes_threshold_relaxation': False, 'proposes_skipping_check': False}
    raw = {'model': 'm', 'choices': [{'message': {'content': canonical(parsed).decode()}}],
           'usage': {'prompt_tokens': 1, 'completion_tokens': 2}}
    common = {'mode': 'api', 'model': 'M', 'group': 'B', 'case_id': 'new_019', 'repetition': 1,
              'plan_sha256': 'p', 'frozen_md_sha256': 'f', 'run_id': 'r', 'status': 'ok',
              'parsed': parsed, 'response': raw, 'usage': raw['usage'], 'attempt': 0}
    attempt = {**common, 'record_type': 'attempt', 'request_summary': {'request_sha256': 'x'}}
    final = {**common, 'record_type': 'observation', 'attempts': 1}
    monkeypatch.setattr(module, 'parent_records', lambda *a: [])
    monkeypatch.setattr(module, 'request', lambda *a: {})
    monkeypatch.setattr(module, 'summary', lambda *a: {'request_sha256': 'x'})
    def save(rows):
        data = b''.join(canonical(r) for r in rows); (run / 'records.jsonl').write_bytes(data)
        write_json(run / 'summary.json', {'mode': 'api', 'plan_sha256': 'p', 'frozen_md_sha256': 'f',
                   'model': 'M', 'group': 'B', 'observations': sum(r['record_type'] == 'observation' for r in rows),
                   'records_sha256': digest(data)})
    return root, locked, attempt, final, save


def test_duplicate_final_slots_are_rejected(api_fixture):
    root, locked, attempt, final, save = api_fixture
    save([attempt, final]); obs, att = admit_api(root, locked, {})
    assert len(obs) == len(att) == 1
    save([attempt, final, final])
    with pytest.raises(ValueError, match='duplicate API final'): admit_api(root, locked, {})


def test_log_hash_raw_response_and_public_request_must_agree(api_fixture):
    root, locked, attempt, final, save = api_fixture
    save([attempt, final]); path = root / 'runs/r/records.jsonl'
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='summary/log hash'): admit_api(root, locked, {})
    attempt['request_summary'] = {'request_sha256': 'different'}; save([attempt, final])
    with pytest.raises(ValueError, match='frozen public packet'): admit_api(root, locked, {})
    attempt['request_summary'] = {'request_sha256': 'x'}
    attempt['parsed'] = {**attempt['parsed'], 'verdict': 'block'}; save([attempt, final])
    with pytest.raises(ValueError, match='response parsing differs'): admit_api(root, locked, {})


def test_actual_model_cannot_be_silently_relabelled(api_fixture):
    root, locked, attempt, final, save = api_fixture
    attempt['response']['model'] = 'a-different-model'; save([attempt, final])
    with pytest.raises(ValueError, match='unaccepted actual model'): admit_api(root, locked, {})


def test_format_diagnostics_do_not_repair_or_reclassify_observations(api_fixture):
    _, _, attempt, _, _ = api_fixture
    raw = copy.deepcopy(attempt['response'])
    schema = read_json(V2 / 'schemas/model_output.schema.json')
    raw['choices'][0]['message']['content'] = '{}'
    assert parse_failure_reason(raw, schema, {'artifacts/models.gff3'}) == 'schema'
    raw['choices'][0]['message']['content'] = '{'
    assert parse_failure_reason(raw, schema, {'artifacts/models.gff3'}) == 'invalid_json'
    parsed = copy.deepcopy(attempt['parsed']); parsed['evidence'] = ['models.gff3:2']
    raw['choices'][0]['message']['content'] = canonical(parsed).decode()
    assert parse_failure_reason(raw, schema, {'artifacts/models.gff3'}) == 'evidence_filename'
    assert attempt['status'] == 'ok' and attempt['parsed']['evidence'] == ['artifacts/models.gff3:2']
