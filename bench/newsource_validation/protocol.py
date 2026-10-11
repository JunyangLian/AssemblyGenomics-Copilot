"""Matched preparation/final stages for evidence retrieval; offline entry only."""
import hashlib
import json
from pathlib import Path

from bench.inspect_adapter import t3_task
from bench.inspect_adapter.readonly import PublicFiles, inspect_tools

DIRECTORY = Path(__file__).resolve().parent
READY = 'READY'
PREPARE = '继续核对题面范围与可获得材料；准备完成时仅回复 READY。本阶段不要提交最终JSON。'
THINKING = {'enable_thinking': True, 'reasoning_effort': 'low', 'thinking_budget': 2048}
LIMITS = {'max_prepare_rounds': 5, 'prepare_max_tokens': 2048, 'final_max_tokens': 8192,
          'thinking_budget_per_request': 2048, 'temperature': 0, 'max_retries': 0,
          'time_limit_seconds': 480, 'max_requests_per_observation': 6,
          'max_reserved_output_thinking_per_observation': 30720,
          'max_input_proxy_per_observation_proposed': 300000,
          'allowed_tools': ['list_files', 'read_file']}


def messages(files, condition):
    if condition not in ('inline', 'tools'):
        raise ValueError('unregistered information condition')
    content = {'task': files.text('task.md'), 'files': files.manifest()}
    if condition == 'inline':
        content['artifacts'] = {e['path']: files.text(e['path']) for e in files.manifest()
                                if e['path'].startswith('artifacts/')}
    schema = json.loads((DIRECTORY / 'schemas/model_output.schema.json').read_bytes())
    system = (DIRECTORY / 'system.txt').read_text(encoding='utf-8')
    system += '\n准备阶段最多五轮；准备完成仅回复 READY，不提前提交最终JSON。最终阶段再按schema作答。'
    return [{'role': 'system', 'content': system + '\n' + json.dumps(schema, ensure_ascii=False)},
            {'role': 'user', 'content': json.dumps(content, ensure_ascii=False, sort_keys=True)}]


def make_task(case_paths, condition, repetitions=1):
    from inspect_ai import Task
    from inspect_ai.dataset import Sample
    from inspect_ai.model import ChatMessageUser
    from inspect_ai.scorer import Score, scorer, mean
    from inspect_ai.solver import solver, use_tools
    public = {cid: PublicFiles(path) for cid, path in case_paths.items()}
    samples = [Sample(id=f'{cid}:r{rep}', input=messages(files, condition),
                      target=(case_paths[cid] / 'expected.json').read_text(encoding='utf-8'),
                      metadata={'case_id': cid, 'condition': condition, 'repeat': rep})
               for rep in range(1, repetitions + 1) for cid, files in public.items()]

    @solver
    def collect_submit():
        async def solve(state, generate):
            if condition == 'tools':
                state = await use_tools(inspect_tools(public[state.metadata['case_id']])[:2])(state, generate)
            elif state.tools:
                raise ValueError('inline received unexpected tools')
            state.metadata['prepare_rounds'] = 0
            for round_number in range(LIMITS['max_prepare_rounds']):
                state = await generate(state, tool_calls='single' if condition == 'tools' else 'none',
                                       max_tokens=LIMITS['prepare_max_tokens'], extra_body=THINKING)
                state.metadata['prepare_rounds'] = round_number + 1
                if state.completed:
                    return state  # Preserve native failure/limit; never override it.
                if not state.output.message.tool_calls and state.output.completion.strip() == READY:
                    break
                if round_number + 1 < LIMITS['max_prepare_rounds']:
                    state.messages.append(ChatMessageUser(content=PREPARE))
            state.tools = []
            state.tool_choice = 'none'
            state.messages.append(ChatMessageUser(content=(DIRECTORY / 'final.txt').read_text(encoding='utf-8')))
            state.metadata['final_submission_scheduled'] = True
            return await generate(state, tool_calls='none', max_tokens=LIMITS['final_max_tokens'],
                                  extra_body={**THINKING, 'response_format': {'type': 'json_object'}})
        return solve

    @scorer(metrics={k: [mean()] for k in ('valid_output', 'verdict_correct', 'observed_correct',
                                          'root_correct', 'decision_joint_correct')})
    def labels():
        async def score(state, target):
            try:
                value = t3_task.parse_output(state.output.completion, public[state.metadata['case_id']])
                result = t3_task.label_values(value, json.loads(target.text))
                explanation = 'Frozen label combination; evidence location only, not semantic adjudication.'
            except (ValueError, json.JSONDecodeError, t3_task.ValidationError) as error:
                value = None
                result = dict.fromkeys(('valid_output', 'verdict_correct', 'observed_correct',
                                        'root_correct', 'decision_joint_correct'), 0)
                explanation = 'Invalid output: ' + type(error).__name__ + ': ' + str(error)
            return Score(value=result, answer=json.dumps(value, ensure_ascii=False), explanation=explanation)
        return score

    return Task(name='newsource_' + condition, version='newsource-retrieval-protocol-1', dataset=samples,
                solver=collect_submit(), scorer=labels(), epochs=1, message_limit=None, turn_limit=6,
                time_limit=LIMITS['time_limit_seconds'], score_on_error=True, continue_on_fail=True,
                metadata={'live_authorized': False, 'same_prepare_budget': True,
                          'tools_are_retrieval_only': True, 'answer_status': 'draft'})


def probe(condition, mode, log_dir):
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log
    from inspect_ai.model import ChatMessageAssistant, GenerateConfig, ModelOutput, get_model
    from inspect_ai.tool import ToolCall
    cases = {cid: t3_task.DIRECTORY / 'cases' / cid for cid in ('t3_001', 't3_002')}
    calls = []

    def respond(items, tools, tool_choice, config):
        calls.append({'max_tokens': config.max_tokens, 'tools': [t.name for t in tools],
                      'message_count': len(items), 'extra_body': config.extra_body})
        if config.max_tokens == LIMITS['final_max_tokens']:
            return ModelOutput.from_content('mockllm/model', json.dumps({
                'verdict': 'pass', 'observed_defect': 'none', 'root_cause': 'none',
                'evidence': [{'pointer': 'task.md:1', 'observation': 'Offline fixture only.'}],
                'action': 'Offline fixture; no model quality measured.',
                'proposes_threshold_relaxation': False, 'proposes_skipping_check': False}))
        if mode == 'early':
            return ModelOutput.from_content('mockllm/model', READY)
        if tools:
            content = json.loads(items[1].text)
            path = next(f['path'] for f in content['files'] if f['path'].endswith('.gff3'))
            return ModelOutput.from_message(ChatMessageAssistant(content='', tool_calls=[
                ToolCall(id=f'probe-{len(calls)}', function='read_file',
                         arguments={'path': path, 'start_line': 1, 'line_count': 200})]),
                model='mockllm/model', stop_reason='tool_calls')
        return ModelOutput.from_content('mockllm/model', '核对中。')

    model = get_model('mockllm/model', custom_outputs=respond, memoize=False,
                      config=GenerateConfig(temperature=0, max_retries=0,
                                            extra_body={'enable_thinking': True,
                                                        'reasoning_effort': 'low', 'thinking_budget': 2048}))
    logs = inspect_eval(make_task(cases, condition), model=model, display='none', log_dir=str(log_dir),
                        log_format='json', max_samples=1, max_tasks=1, retry_on_error=0, max_retries=0)
    if len(logs) != 1 or logs[0].status != 'success':
        raise ValueError('native offline probe failed')
    log = read_eval_log(logs[0].location)
    for sample in log.samples:
        if sample.error or not sample.metadata.get('final_submission_scheduled'):
            raise ValueError('probe failed to reach final submission')
        if next(iter(sample.scores.values())).value['valid_output'] != 1:
            raise ValueError('probe final JSON invalid')
    return log, calls


def fixture():
    records = []
    for mode in ('early', 'maximum'):
        paired = {}
        for condition in ('inline', 'tools'):
            log, calls = probe(condition, mode, DIRECTORY / 'work/protocol_fixture' / mode / condition)
            paired[condition] = calls
            records.append({'mode': mode, 'condition': condition, 'observations': len(log.samples),
                            'native_generate_calls': len(calls), 'valid_final_json': len(log.samples),
                            'prepare_rounds': [s.metadata['prepare_rounds'] for s in log.samples],
                            'tool_replies': sum(m.role == 'tool' for s in log.samples for m in s.messages),
                            'maximum_message_count': max(len(s.messages) for s in log.samples)})
        if [r['max_tokens'] for r in paired['inline']] != [r['max_tokens'] for r in paired['tools']]:
            raise ValueError('condition generation allowances differ')
        if [r['extra_body'] for r in paired['inline']] != [r['extra_body'] for r in paired['tools']]:
            raise ValueError('condition thought allowances differ')
        for calls in paired.values():
            for call in calls:
                if any(call['extra_body'].get(k) != v for k, v in THINKING.items()):
                    raise ValueError('a phase dropped the thought configuration')
                if call['max_tokens'] == LIMITS['final_max_tokens'] and call['tools']:
                    raise ValueError('final submission still exposes tools')
    receipt = {'status': 'pass', 'scope': 'old T3 development material only', 'observations': 8,
               'provider_calls': 0, 'new_source_features_read': 0, 'model_quality_measured': False,
               'cases': ['t3_001', 't3_002'], 'limits': LIMITS, 'checks': records,
               'native_generate_calls': sum(r['native_generate_calls'] for r in records),
               'phase_thought_settings_verified': THINKING,
               'thinking_budget_tested': 'same configured allowances; local mock does not measure provider thought tokens',
               'physical_http_budget_protection': 'not yet implemented for this run; no paid authorization'}
    (DIRECTORY / 'PROTOCOL_FIXTURE.json').write_bytes(
        (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode())
    print(f'PASS: 8 old-development observations; {receipt["native_generate_calls"]} local generations; '
          'matched early/max phase allowances; 0 provider calls')
    return receipt


if __name__ == '__main__':
    fixture()
