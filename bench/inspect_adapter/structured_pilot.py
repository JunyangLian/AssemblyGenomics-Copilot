"""Version 2 development elicitation: bounded tools, then JSON-only submission.

Reuse frozen scoring and transport; no repairing old answers or auto fallback.
"""
from contextlib import contextmanager
import argparse
import json
import os

from bench.inspect_adapter import pilot

ROOT = pilot.ROOT
DIRECTORY = ROOT / 'pilot2'
BASE = {name: getattr(pilot, name) for name in
        ('draft_plan', 'implementation_hashes', 'draft_hashes', 'messages',
         'make_task', 'RequestBudget')}


def draft_plan():
    plan = BASE['draft_plan']()
    return {**plan, 'version': 'inspect-development-pilot-2-json-object',
            'condition': 'guided_readonly_tools_then_json_object',
            'max_evidence_rounds': 5, 'evidence_max_tokens': 512,
            'final_max_tokens': 2048, 'max_turns_per_case': 6,
            'max_http_requests': 24, 'max_output_token_reservation': 18432,
            'final_response_format': {'type': 'json_object'},
            'transport': {'NO_PROXY': 'api.siliconflow.cn', 'tls_verification': True},
            'stop_http_statuses': [400, 401, 403, 404, 422, 429],
            'online_json_mode_compatibility': 'not yet verified for this model',
            'development_tuning': 'prompts adapted after pilot 1 failures; no independent improvement claim',
            'answer_policy': 'same four already-approved answer bytes; new run conditions need approval'}


def messages(files, schema):
    system = (DIRECTORY / 'system.txt').read_text(encoding='utf-8')
    return [{'role': 'system', 'content': system + '\n' + json.dumps(schema, ensure_ascii=False, sort_keys=True)},
            {'role': 'user', 'content': json.dumps({'task': files.text('task.md'),
                                                  'files': files.manifest()}, ensure_ascii=False, sort_keys=True)}]


def draft_hashes():
    return {**BASE['draft_hashes'](),
            **{name: pilot.sha((DIRECTORY / name).read_bytes()) for name in ('system.txt', 'final.txt')}}


def implementation_hashes():
    return {**BASE['implementation_hashes'](),
            'structured_pilot.py': pilot.sha((ROOT / 'structured_pilot.py').read_bytes())}


class RequestBudget(BASE['RequestBudget']):
    """Reject phase/config drift before any physical request reservation."""
    def reserve(self, method, url, data):
        body = pilot.strict_object(data.decode('utf-8'))
        response_format = body.get('response_format')
        if response_format is None:
            phase, tokens = 'collect', self.plan['evidence_max_tokens']
            if len(body.get('tools') or []) != 5 or body.get('tool_choice', 'auto') != 'auto':
                raise ValueError('evidence phase requires native tools in auto mode')
        elif response_format == self.plan['final_response_format']:
            phase, tokens = 'final', self.plan['final_max_tokens']
            if body.get('tools') or body.get('tool_choice') not in (None, 'none'):
                raise ValueError('final JSON phase must have no tools')
        else:
            raise ValueError('unapproved response format; no automatic fallback')
        if body.get('max_tokens') != tokens:
            raise ValueError('phase output limit differs from plan')
        original = self.plan
        try:
            self.plan = {**original, 'max_tokens': tokens}
            super().reserve(method, url, data)
        finally:
            self.plan = original
        self.records[-1]['phase'] = phase


def make_task(plan, answers):
    from inspect_ai import Task
    from inspect_ai.dataset import Sample
    from inspect_ai.model import ChatMessageSystem, ChatMessageUser
    from inspect_ai.scorer import Score, scorer, mean
    from inspect_ai.solver import solver, use_tools

    schema = pilot.read_json(pilot.SCHEMA)
    public = {cid: pilot.PublicFiles(pilot.CASES / cid) for cid in plan['case_ids']}
    samples = [Sample(id=cid, input=[ChatMessageSystem(content=m['content']) if m['role'] == 'system'
               else ChatMessageUser(content=m['content']) for m in messages(files, schema)],
               target=pilot.canonical(answers[cid]).decode('utf-8'),
               metadata={'split': 'development', 'post_result_prompt_tuning': True})
               for cid, files in public.items()]
    final_instruction = (DIRECTORY / 'final.txt').read_text(encoding='utf-8')

    @solver
    def collect_then_submit():
        async def solve(state, generate):
            state = await use_tools(pilot.inspect_tools(public[str(state.sample_id)]))(state, generate)
            rounds = 0
            for _ in range(plan['max_evidence_rounds']):
                state.tool_choice = 'auto'
                state = await generate(state, tool_calls='single',
                                       max_tokens=plan['evidence_max_tokens'], extra_body=plan['extra_body'])
                rounds += 1
                if state.completed:
                    return state  # Never override Inspect time/token/turn limits.
                if not state.output.message.tool_calls:
                    break
            state.metadata['evidence_rounds'] = rounds
            state.metadata['final_submission_scheduled'] = True
            state.tools = []
            state.tool_choice = 'none'
            state.messages.append(ChatMessageUser(content=final_instruction))
            return await generate(state, tool_calls='none', max_tokens=plan['final_max_tokens'],
                                  extra_body={**plan['extra_body'],
                                              'response_format': plan['final_response_format']})
        return solve

    @scorer(metrics={name: [mean()] for name in ('schema_valid', 'evidence_locator_valid', 'decision_joint')})
    def labels():
        async def score(state, target):
            values, parsed, error = pilot.score_output(state.output.completion, json.loads(target.text),
                                                     public[str(state.sample_id)], schema)
            return Score(value=values, answer=json.dumps(parsed, ensure_ascii=False),
                         explanation=error or 'Evidence semantics and action safety unadjudicated.',
                         metadata={'evidence_support': 'unadjudicated', 'action_safety': 'unadjudicated'})
        return score

    return Task(name='assemblygenomics_development_tool_pilot', version=plan['version'],
                dataset=samples, solver=collect_then_submit(), scorer=labels(), epochs=1,
                turn_limit=plan['max_turns_per_case'], time_limit=480,
                score_on_error=True, continue_on_fail=True,
                metadata={'no_heldout_or_hypothesis_claim': True, 'two_phase_elicitation': True})


@contextmanager
def bindings():
    """Temporary entry-point binding; leave the frozen module intact on return."""
    replacement = {'PILOT': DIRECTORY, 'draft_plan': draft_plan, 'messages': messages,
                   'draft_hashes': draft_hashes, 'implementation_hashes': implementation_hashes,
                   'make_task': make_task, 'RequestBudget': RequestBudget}
    previous = {name: getattr(pilot, name) for name in replacement}
    try:
        for name, value in replacement.items():
            setattr(pilot, name, value)
        yield
    finally:
        for name, value in previous.items():
            setattr(pilot, name, value)


def prepare():
    with bindings():
        pilot.prepare()
        plan = draft_plan()
        estimate = pilot.read_json(DIRECTORY / 'ESTIMATE.json')
        estimate.update(hard_request_count_cap=plan['max_http_requests'],
                        output_requested_token_ceiling=plan['max_output_token_reservation'],
                        peak_reference_estimate_cny=(plan['max_input_proxy_tokens'] * 3 +
                                                    plan['max_output_token_reservation'] * 9) / 1000000,
                        phase_caps={'collect_calls_per_case': 5, 'collect_tokens_per_call': 512,
                                    'final_calls_per_case': 1, 'final_tokens_per_call': 2048},
                        actual_provider_calls=0)
        pilot.write_json(DIRECTORY / 'ESTIMATE.json', estimate)
        if any((DIRECTORY / f'answers/{cid}/expected.json').read_bytes() !=
               (ROOT / f'pilot/answers/{cid}/expected.json').read_bytes() for cid in plan['case_ids']):
            raise ValueError('answer bytes differ from original approved pilot')


def execute():
    with bindings():
        plan, _ = pilot.approved()  # Before credentials, environment or provider initialization.
        if plan != draft_plan():
            raise ValueError('approved proposal differs from version 2 implementation')
        os.environ['NO_PROXY'] = plan['transport']['NO_PROXY']
        pilot.execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--freeze', action='store_true')
    action.add_argument('--api', action='store_true')
    parser.add_argument('--approval-quote')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.freeze:
        with bindings():
            pilot.freeze(args.approval_quote or '')
    else:
        execute()
