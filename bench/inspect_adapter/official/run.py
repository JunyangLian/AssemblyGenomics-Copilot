"""Run the unmodified upstream addition task using Inspect's native local mock.

This validates framework/tool wiring, not benchmark or model performance.
"""
import importlib.util
from importlib.metadata import version
import json
from pathlib import Path

from bench.inspect_adapter.pilot import sha, write_json

ROOT = Path(__file__).resolve().parent


def upstream_task():
    source = json.loads((ROOT / 'SOURCE.json').read_text(encoding='utf-8'))
    if version('inspect-ai') != source['tag']:
        raise ValueError('official source and installed Inspect versions differ')
    for name, entry in source['files'].items():
        if sha((ROOT / 'upstream' / name).read_bytes()) != entry['sha256']:
            raise ValueError('unmodified upstream source identity changed')
    spec = importlib.util.spec_from_file_location('official_inspect_tool_use', ROOT / 'upstream/tool_use.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.addition_problem(), source


def execute():
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log
    from inspect_ai.model import get_model, ModelOutput, ChatMessageAssistant
    from inspect_ai.tool import ToolCall

    task, source = upstream_task()

    def response(messages, tools, tool_choice, config):
        replies = [message for message in messages if message.role == 'tool']
        if not replies:
            return ModelOutput.from_message(ChatMessageAssistant(content='', tool_calls=[
                ToolCall(id='official-add-1', function='add', arguments={'x': 1, 'y': 1})]),
                model='mockllm/model', stop_reason='tool_calls')
        if len(replies) != 1 or replies[0].error or replies[0].text != '2':
            raise ValueError('official tool result differs from 1 + 1')
        return ModelOutput.from_content('mockllm/model', '2')

    model = get_model('mockllm/model', custom_outputs=response, memoize=False)
    output = ROOT.parent / 'work/official_tool_use'
    logs = inspect_eval(task, model=model, display='none', log_format='json',
                        log_dir=str(output / 'logs'), max_samples=1, message_limit=10)
    if len(logs) != 1 or logs[0].status != 'success':
        raise ValueError('official example did not complete')
    log = read_eval_log(logs[0].location)
    if len(log.samples) != 1:
        raise ValueError('official sample missing')
    sample = log.samples[0]
    calls = [c for m in sample.messages if m.role == 'assistant' for c in (m.tool_calls or [])]
    replies = [m for m in sample.messages if m.role == 'tool']
    if (sample.error or len(calls) != 1 or len(replies) != 1 or replies[0].error or
        replies[0].tool_call_id != calls[0].id or replies[0].text != '2' or
        next(iter(sample.scores.values())).value != 'C'):
        raise ValueError('official transcript or built-in scorer failed')
    result = {'status': 'pass', 'upstream_commit': source['commit'],
              'source_files': source['files'], 'task': 'addition_problem',
              'upstream_task_solver_tools_scorer_modified': False,
              'mode': 'scripted_native_mock', 'provider_calls': 0, 'model_quality_measured': False,
              'actual_tool_calls': len(calls), 'samples': 1,
              'inspect_log': str(Path(logs[0].location).relative_to(output))}
    write_json(output / 'RECEIPT.json', result)
    print('PASS: unmodified official Task -> use_tools/add -> generate -> match -> log; 0 provider calls')
    return result


if __name__ == '__main__':
    execute()
