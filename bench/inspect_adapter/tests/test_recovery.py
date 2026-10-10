import pytest

from bench.inspect_adapter.pilot import draft_plan
from bench.inspect_adapter.recovery import remaining_plan


def test_recovery_deducts_every_previous_reservation_without_changing_model():
    original = draft_plan()
    resumed = remaining_plan(original, {'calls': 4, 'input_proxy': 9044, 'output_reserved': 8192}, {'run_id': 'unit-only'})
    assert resumed['max_http_requests'] == 28
    assert resumed['max_input_proxy_tokens'] == 190956
    assert resumed['max_output_token_reservation'] == 57344
    for key in ('case_ids', 'model_id', 'temperature', 'max_tokens', 'extra_body', 'repetitions'):
        assert resumed[key] == original[key]
    assert original['max_http_requests'] == 32


@pytest.mark.parametrize('calls', [-1, 32])
def test_recovery_rejects_invalid_or_exhausted_budget(calls):
    with pytest.raises(ValueError, match='invalid or exhausted'):
        remaining_plan(draft_plan(), {'calls': calls, 'input_proxy': 9044, 'output_reserved': 8192}, {})
