import json

import pytest

from bench.inspect_adapter import glm_followup as followup


def test_scope_and_all_new_caps_are_explicit():
    setup = followup.plan()
    assert setup['planned_observations'] == 84 and len(setup['case_ids']) == 14
    assert setup['repetitions'] == 3 and not setup['api_call_authorized']
    assert setup['max_http_requests'] == 294
    assert setup['max_output_token_reservation'] == 1720320
    for new, used in [('max_http_requests', 'calls'), ('max_input_proxy_tokens', 'input_proxy'),
                     ('max_output_token_reservation', 'output_reserved')]:
        assert setup['proposed_cumulative_caps'][used] == setup['previous_consumption'][used] + setup[new]
    assert setup['reference_reservation_cost_cny'] == 6.016896
    assert setup['analysis']['all_cases_prior_protocol_attempted']
    assert setup['analysis']['post_result_prompt_clarification']


def test_same_generic_instruction_in_both_arms_and_unchanged_targets():
    setup = followup.plan()
    clarification = (followup.DIRECTORY / 'citation_instruction.txt').read_text(encoding='utf-8')
    for condition in setup['conditions']:
        task = followup.make_task(setup, condition, True)
        assert len(task.dataset) == 42
        for sample in task.dataset:
            cid = sample.metadata['case_id']
            assert sample.target == (followup.packets.DIRECTORY / 'cases' / cid / 'expected.json').read_text(encoding='utf-8')
            original = followup.t3_task.messages(followup.PublicFiles(followup.packets.DIRECTORY / 'cases' / cid), condition)
            assert sample.input[0].text == original[0]['content'] + '\n' + clarification
            assert sample.input[1].text == original[1]['content']
            assert 'acceptable_decisions' not in str(sample.input)


def test_previous_failed_range_stays_failed_and_no_output_repair():
    receipt = followup.pilot.read_json(followup.glm_compat.DIRECTORY / 'RUN_RECEIPT.json')
    row = next(r for r in receipt['rows'] if r['status'] == 'parse_error')
    with pytest.raises(ValueError, match='evidence field absent'):
        followup.t3_task.parse_output(row['output'], followup.PublicFiles(followup.packets.DIRECTORY / 'cases' / row['case_id']))
    assert row['scores']['valid_output'] == 0
    value = json.loads(row['output'])
    # A separate synthetic format probe, never substituted for saved output.
    value['evidence'] = [{'pointer': 'task.md:1', 'observation': 'Offline format probe.'}]
    assert followup.t3_task.parse_output(json.dumps(value), followup.PublicFiles(
        followup.packets.DIRECTORY / 'cases' / row['case_id']))['verdict'] == 'pass'


def test_pending_new_budget_blocks_before_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(followup, 'DIRECTORY', tmp_path)
    monkeypatch.setattr(followup.os.environ, 'get', lambda *_: pytest.fail('credentials read without new approval'))
    with pytest.raises(ValueError, match='human-approved freeze'):
        followup.execute()


def test_current_full_fixture_is_not_a_quality_score():
    receipt = followup.pilot.read_json(followup.DIRECTORY / 'FIXTURE_RECEIPT.json')
    assert receipt['external_calls'] == 0 and not receipt['model_quality_measured']
    assert receipt['planned_slots'] == receipt['valid_final_json'] == 84
    assert receipt['wire_requests'] == 294 and receipt['tool_replies'] == 1050
    assert receipt['requests_with_exact_reasoning_replay'] == 210
    assert receipt['implementation'] == followup.file_hashes()
    assert receipt['longer_reply_pressure']['slots_preserved'] == 84
    assert receipt['longer_reply_pressure']['budget']['stopped_reason'] == 'request_validation_or_budget_limit'


def test_report_keeps_every_failed_slot_and_cumulative_usage(tmp_path, monkeypatch):
    from bench.inspect_adapter import glm_followup_report as report
    setup = followup.plan()
    directory = tmp_path / 'documents'
    work = tmp_path / 'work'
    output = work / 'synthetic-report-test'
    directory.mkdir()
    output.mkdir(parents=True)
    followup.pilot.write_json(directory / 'FROZEN.json', {'test_fixture': True})
    seal = followup.pilot.sha((directory / 'FROZEN.json').read_bytes())
    monkeypatch.setattr(followup, 'DIRECTORY', directory)
    monkeypatch.setattr(followup, 'WORK', work)
    monkeypatch.setattr(followup, 'approved', lambda: setup)
    rows = [{'case_id': cid, 'condition': condition, 'repetition': rep, 'status': 'missing',
             'parsed': None, 'output': '', 'execution_error': None, 'final_submission_scheduled': False,
             'scores': dict.fromkeys(followup.t3_live.SCORES, 0), 'tool_calls': 0, 'tool_errors': 0}
            for condition in setup['conditions'] for cid in setup['case_ids'] for rep in (1, 2, 3)]
    budget = {'calls': 0, 'input_proxy': 0, 'output_reserved': 0, 'stopped_reason': 'offline_test', 'records': []}
    result = {'run_id': 'synthetic-report-test', 'fixture': False, 'seal_sha256': seal,
              'gold_freeze_sha256': setup['gold_freeze_sha256'], 'planned_observations': 84,
              'fatal_error_class': None, 'rows': rows, 'summary': followup.summarize(setup, rows),
              'budget': {k: v for k, v in budget.items() if k != 'records'}, 'scope': setup['analysis']}
    followup.pilot.write_json(output / 'RESULTS.json', result)
    followup.pilot.write_json(output / 'REQUEST_BUDGET.json', budget)
    public = report.write_report(output)
    assert len(public['rows']) == 84 and not public['quality_comparison_valid']
    assert not public['independent_validation']
    assert public['cumulative_consumption'] == setup['previous_consumption']
    assert public['qc_metrics']['tools']['fault_detection_cases'] == 0
    assert public['qc_metrics']['tools']['incomplete_cases'] == 14
    assert '0/14 (0.0%)' in (directory / 'REPORT.md').read_text(encoding='utf-8')
    result['rows'][0]['case_id'] = 'unregistered'
    followup.pilot.write_json(output / 'RESULTS.json', result)
    with pytest.raises((ValueError, FileNotFoundError)):
        report.write_report(output)
