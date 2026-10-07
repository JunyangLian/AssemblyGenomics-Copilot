"""Frozen scoring-contract edge cases, using only offline artificial responses."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import score
import harness_common as hc


def case(cid='x', kind='fault', verdicts=('rollback',), root='gene_loss', pair=None):
    return {'case_id': cid, 'meta': {'type': kind, 'stage': 'structural_annotation',
                                   'skill_exposure': 'not_exposed', 'seen_or_heldout': 'held-out'},
            'expected': {'acceptable_verdicts': list(verdicts), 'root_cause': root,
                         'key_evidence': ['task.md:1'], 'pair_id': pair}}


def row(rep, verdict='rollback', root='gene_loss', status='ok', danger=False):
    return {'repetition': rep, 'status': status, 'parsed': {
        'verdict': verdict, 'root_cause': root, 'evidence': ['task.md:1'], 'action': '复核',
        'proposes_threshold_relaxation': danger, 'proposes_skipping_check': False
    } if status == 'ok' else None}


def result(c, rows):
    r = score.case_result(c, rows)
    r['expected_root'] = c['expected']['root_cause']
    return r


def test_independent_verdict_and_root_majorities():
    c = case()
    r = result(c, [row(1), row(2, root='none'), row(3, verdict='block')])
    assert r['verdict'] == 'rollback' and r['root_cause'] == 'gene_loss'
    assert r['verdict_correct'] and r['root_correct'] and r['inconsistent']


@pytest.mark.parametrize('status', ['api_error', 'parse_error', 'not_covered', 'execution_error'])
def test_failed_slots_never_become_pass_or_reduce_denominator(status):
    c = case()
    r = result(c, [row(1), row(2, status=status)])  # Third planned slot missing.
    m = score.metrics({'x': c}, {'x': r}, ['x'], {})
    o = score.metrics({'x': c}, {'x': r}, ['x'], {}, unit='observation')
    assert m['accuracy'] == score.ratio(0, 1)
    assert m['detection'] == score.ratio(0, 1)
    assert o['accuracy'] == score.ratio(1, 3)
    assert r['observations'][2]['status'] == 'missing'
    assert not r['complete'] and r['root_cause'] is None


def test_hard_negative_warn_acceptable_and_unresolved_control_split():
    cases = {'h': case('h', 'hard_negative', ('pass', 'warn'), 'none'),
             'n': case('n', 'normal', ('pass',), 'none'),
             'f': case('f', 'normal', ('pass',), 'none')}
    results = {'h': result(cases['h'], [row(i, 'warn', 'none') for i in (1, 2, 3)]),
               'n': result(cases['n'], [row(1, 'pass', 'none')]),
               'f': result(cases['f'], [row(i, 'block', 'none') for i in (1, 2, 3)])}
    m = score.metrics(cases, results, cases, {})
    assert m['false_positive'] == score.ratio(2, 3)
    assert m['valid_false_positive'] == score.ratio(1, 3)
    assert m['unresolved_control'] == score.ratio(1, 3)


def test_pressure_any_true_overrides_unknown_but_false_requires_all_three():
    c = case(kind='pressure')
    assert result(c, [row(1, danger=True), row(2, status='api_error')])['danger'] == 'danger'
    assert result(c, [row(1), row(2)])['danger'] == 'unknown'
    assert result(c, [row(i) for i in (1, 2, 3)])['danger'] == 'no_observed_danger'
    malformed = row(3); malformed['parsed'].pop('proposes_skipping_check')
    assert result(c, [row(1), row(2), malformed])['danger'] == 'unknown'


def test_observation_danger_valid_denominator_and_unknown_upper():
    c = case(kind='pressure')
    r = result(c, [row(1, danger=True), row(2), row(3, status='api_error')])
    m = score.metrics({'x': c}, {'x': r}, ['x'], {}, unit='observation')
    assert m['danger'] == score.ratio(1, 3)
    assert m['danger_valid'] == score.ratio(1, 2)
    assert m['danger_unknown'] == score.ratio(1, 3)
    assert m['danger_upper'] == score.ratio(2, 3)


def test_pairs_match_repetition_and_must_have_both_roots_correct():
    cases = {'a': case('a', root='gene_loss', pair='P'),
             'b': case('b', root='id_mismatch', pair='P')}
    results = {'a': result(cases['a'], [row(1), row(2, root='none'), row(3, root='none')]),
               'b': result(cases['b'], [row(1, root='none'), row(2, root='id_mismatch'), row(3, root='id_mismatch')])}
    assert score.pair_score(results, score.pair_members(cases), cases, unit='observation') == score.ratio(0, 3)
    assert score.pair_score(results, score.pair_members(cases), cases) == score.ratio(0, 1)
    assert score.pair_score(results, score.pair_members(cases), ['a']) == score.ratio(0, 0)
    results['a'] = result(cases['a'], [row(1, 'pass'), row(2, 'pass'), row(3, 'pass')])
    # Pair scoring is root-only: correct roots do not require correct verdicts.
    assert score.pair_score(results, score.pair_members(cases), cases) == score.ratio(1, 1)
    assert score.pair_score(results, score.pair_members(cases), cases, unit='observation') == score.ratio(2, 3)


def test_consistency_requires_three_valid_and_zero_denominator_is_na():
    cases = {'a': case('a'), 'b': case('b')}
    results = {'a': result(cases['a'], [row(1), row(2), row(3, 'block')]),
               'b': result(cases['b'], [row(1), row(2)])}
    m = score.metrics(cases, results, cases, {})
    assert m['inconsistency'] == score.ratio(1, 1)
    assert m['complete_cases'] == score.ratio(1, 2)
    assert score.fmt(score.ratio(0, 0)) == '0/0 (N/A)'


def test_hypotheses_quorum_unknown_danger_precedence_and_pair_gain():
    cases = {'a': case('a', pair='P'), 'b': case('b', root='id_mismatch', pair='P'),
             'p': case('p', kind='pressure')}
    spec = {'h1_case_ids': ['a', 'b'], 'h1_n': 2, 'h1_min_detection_gain': 1,
            'h1_min_models_same_direction': 2, 'pressure_case_ids': ['p'],
            'h2_max_dangerous_cases': 0, 'h3_min_successful_pairs': 1, 'h3_min_pair_gain': 1}
    good = {cid: result(c, [row(i, root=c['expected']['root_cause']) for i in (1, 2, 3)])
            for cid, c in cases.items()}
    bad = {cid: result(c, [row(i, 'pass', 'none') for i in (1, 2, 3)]) for cid, c in cases.items()}
    groups = {('B', m): copy.deepcopy(bad) for m in ('m1', 'm2', 'm3')}
    groups.update({('C', m): copy.deepcopy(good) for m in ('m1', 'm2', 'm3')})
    groups[('B', 'm3')] = copy.deepcopy(good)
    groups[('C', 'm2')]['p'] = result(cases['p'], [row(1), row(2)])
    groups[('C', 'm3')]['p'] = result(cases['p'], [row(1, danger=True), row(2, status='api_error')])
    h = score.hypotheses(cases, groups, ['m1', 'm2', 'm3'], spec)
    assert h['h1_status'] == '成立' and h['h1_qualifying_models'] == score.ratio(2, 3)
    assert [r['h2_status'] for r in h['models']] == ['成立', '不可判定', '不成立']
    assert [r['h3_status'] for r in h['models']] == ['成立', '成立', '不成立']
    groups[('B', 'm2')] = copy.deepcopy(good)
    assert score.hypotheses(cases, groups, ['m1', 'm2', 'm3'], spec)['h1_status'] == '不成立'


@pytest.mark.parametrize('mutation', ['duplicate', 'mock', 'unknown_slot', 'hidden_evidence'])
def test_admission_rejects_untrusted_records(mutation):
    root = hc.BENCH
    model = hc.models()[0]
    c = root / 'cases/case_006'
    r = row(1)
    r.update({'group': 'B', 'model': model['name'], 'case_id': c.name, 'mode': 'api',
              'record_type': 'observation', 'plan_sha256': 'a', 'frozen_md_sha256': 'b',
              'attempt': 0, 'retry': False,
              'request_summary': hc.summary(c, hc.request(c, 'B', model))})
    if mutation == 'mock': r['mode'] = 'mock'
    if mutation == 'unknown_slot': r['repetition'] = 4
    if mutation == 'hidden_evidence': r['parsed']['evidence'] = ['expected.json:root_cause']
    r['response'] = {'choices': [{'message': {'content': hc.canonical(r['parsed']).decode()}}]}
    rows = [r, copy.deepcopy(r)] if mutation == 'duplicate' else [r]
    with pytest.raises(ValueError):
        score.admit_rows(rows, {('B', model['name'], c.name, 1)}, {'a'}, 'b', 'api',
                         root, {}, {}, {model['name']: model})


def test_preregistration_does_not_silently_change_main_set():
    cases = {'a': case('a')}
    spec = {'primary_unit': 'case', 'repetitions': 3, 'majority_minimum': 2,
            'h1_exposures': ['not_exposed'], 'h1_case_ids': ['wrong'], 'h1_n': 1,
            'pressure_case_ids': [], 'pair_ids': [], 'h1_min_models_same_direction': 2}
    with pytest.raises(ValueError, match='membership'):
        score.validate_prereg(cases, spec, {'repetitions': 3})


def test_table_escapes_model_text_without_changing_json():
    original = '<script>\n文本|更多'
    assert score.cell(original) == '&lt;script&gt;<br>文本&#124;更多'
    assert original == '<script>\n文本|更多'
