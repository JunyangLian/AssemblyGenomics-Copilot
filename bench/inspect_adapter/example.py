"""Official-component learning example using a local mock, not benchmark data."""
from pathlib import Path


def execute():
    from inspect_ai import Task, eval as inspect_eval
    from inspect_ai.dataset import Sample
    from inspect_ai.model import get_model, ModelOutput
    from inspect_ai.scorer import match
    from inspect_ai.solver import generate

    task = Task(name='inspect_component_learning_example',
                dataset=[Sample(input='Return the word pass.', target='pass')],
                solver=generate(), scorer=match())
    model = get_model('mockllm/model', custom_outputs=[ModelOutput.from_content('mockllm/model', 'pass')])
    log = inspect_eval(task, model=model, display='none',
                       log_dir=str(Path(__file__).resolve().parent / 'work/example'))[0]
    if log.status != 'success' or next(iter(log.samples[0].scores.values())).value != 'C':
        raise ValueError('mock component example failed')
    print('PASS: Dataset -> generate(local mock) -> match -> Inspect log; 0 provider calls')
    return log


if __name__ == '__main__':
    execute()
