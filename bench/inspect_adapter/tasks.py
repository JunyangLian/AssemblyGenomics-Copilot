"""Inspect CLI task registration; offline replay only, no generation calls."""
from inspect_ai import task

from bench.inspect_adapter.bridge import make_task


@task
def v2_offline_replay():
    return make_task()
