"""Meaningful protocol/transport safety tests; no biological mock scoring."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import copy
import json
import pytest
from bench.v2.runtime import V2, BENCH, canonical, digest, read_json, write_json, request, parse_response
from bench.v2.plan import models
from bench.v2.adapter import Mock, Budget, OpenAICompatible, ApprovalError, approval
from bench.v2.run import observe
from bench.v2.import_rules import reuse_identity, validate_rows

CASE = V2 / 'cases/new_019'
SCHEMA = read_json(V2 / 'schemas/model_output.schema.json')
MODEL = models()[0]
LOCK = {'plan': {'parse_retries': 1}, 'plan_sha256': 'p', 'frozen_md_sha256': 'f'}


def test_private_controls_never_reach_requests_and_context_identical():
    systems = []
    for m in models():
        b, c = request(CASE, 'B', m), request(CASE, 'C2', m)
        # The frozen schema names forbidden private filenames in its description;
        # the public case packet must not include those files or their contents.
        text = c['messages'][1]['content']
        assert not any(s in text for s in ('expected.json', 'meta.json', 'acceptable_verdicts', 'key_evidence', 'v2_labels', 'source_files'))
        assert b['messages'][1] == c['messages'][1]
        assert b['max_tokens'] == c['max_tokens'] == 8192
        assert b['temperature'] == c['temperature'] == 0
        systems.append(c['messages'][0])
    assert all(s == systems[0] for s in systems)


def test_request_ids_use_exact_official_mapping_while_display_names_remain():
    official = {m['name']: m['id'] for m in read_json(V2 / 'PROVIDER_MODELS.json')['models']}
    for m in models():
        body = request(CASE, 'B', m)
        assert body['model'] == official[m['name']] == m['requested_model_id']
        assert m['name'] != body['model']


class Replies:
    def __init__(self, outputs): self.outputs, self.calls = outputs, []
    def complete(self, body, slot):
        self.calls.append(body); return self.outputs[len(self.calls) - 1]


def valid_raw():
    raw = Mock(SCHEMA, 20261007).complete(request(CASE, 'B', MODEL), 'test')[0]
    raw['model'] = request(CASE, 'B', MODEL)['model']
    return raw


def test_one_format_repair_has_no_prior_response_or_grading_feedback():
    first = {'choices': [{'message': {'content': 'MALFORMED_RESPONSE_SENTINEL'}}]}
    client = Replies([(first, None), (valid_raw(), None)]); rows = []
    final = observe(CASE, 'B', MODEL, client, 1, LOCK, rows.append)
    assert final['status'] == 'ok' and final['attempts'] == 2
    assert len(client.calls) == 2 and len(rows) == 3
    assert 'MALFORMED_RESPONSE_SENTINEL' not in canonical(client.calls[1]).decode()
    assert client.calls[0]['messages'] == client.calls[1]['messages'][:2]


def test_second_parse_failure_is_retained_and_api_error_not_retried():
    bad = {'choices': [{'message': {'content': '{}'}}]}
    client = Replies([(bad, None), (bad, None)]); rows = []
    final = observe(CASE, 'B', MODEL, client, 1, LOCK, rows.append)
    assert final['status'] == 'parse_error' and final['attempts'] == 2
    client = Replies([(None, 'HTTP 429')]); rows = []
    final = observe(CASE, 'B', MODEL, client, 1, LOCK, rows.append)
    assert final['status'] == 'api_error' and len(client.calls) == 1


def test_unknown_evidence_and_duplicate_json_keys_rejected():
    raw = valid_raw(); obj = json.loads(raw['choices'][0]['message']['content'])
    obj['evidence'] = ['expected.json:root_cause']
    raw['choices'][0]['message']['content'] = json.dumps(obj)
    assert parse_response(raw, CASE, V2)[1]
    raw['choices'][0]['message']['content'] = '{"verdict":"pass","verdict":"block"}'
    assert parse_response(raw, CASE, V2)[1]


def test_real_api_refuses_before_environment_key_read(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError('key accessed before approval')
    monkeypatch.setattr('bench.v2.adapter.os.environ.get', forbidden)
    dummy = type('Dummy', (), {'root': tmp_path, 'locked': LOCK})()
    with pytest.raises(ApprovalError, match='pending'): OpenAICompatible(MODEL, dummy)
    with pytest.raises(ApprovalError, match='pending'): Budget(tmp_path, LOCK)


@pytest.fixture
def authorized(tmp_path):
    locked = {'plan': {'version': 'v2-test', 'models': [MODEL]}, 'plan_sha256': 'p', 'frozen_md_sha256': 'f'}
    write_json(tmp_path / 'MOCK_REPORT.json', {'status': 'pass', 'plan_sha256': 'p'})
    write_json(tmp_path / 'API_APPROVAL.json', {'approved': True, 'accepts_unknown_price': True,
        'accepts_unknown_provider_defaults': True, 'parameters_reviewed': True, 'user_approval_quote': 'test fixture only',
        'plan_sha256': 'p', 'frozen_md_sha256': 'f', 'models': [MODEL['name']], 'groups': ['B', 'C2'],
        'mock_report_sha256': digest((tmp_path / 'MOCK_REPORT.json').read_bytes()),
        'max_calls': 2, 'max_input_tokens': 1000000, 'max_output_tokens': 16384})
    return tmp_path, locked


def test_cumulative_ledger_reserves_repairs_and_survives_reinitialization(authorized):
    root, lock = authorized; body = request(CASE, 'B', MODEL)
    b = Budget(root, lock); b.reserve('model:B:case:1:0', body)
    with pytest.raises(ApprovalError, match='already reserved'): Budget(root, lock).reserve('model:B:case:1:0', body)
    other = Budget(root, lock); other.reserve('model:B:case:1:1', body)
    with pytest.raises(ApprovalError, match='cap reached'): Budget(root, lock).reserve('model:B:case:2:0', body)
    assert read_json(root / 'runs/API_LEDGER.json')['calls'] == 2
    assert read_json(root / 'runs/API_LEDGER.json')['output_reserved'] == 16384


def test_provider_over_limit_usage_flag_preserved(authorized):
    root, lock = authorized; b = Budget(root, lock); b.reserve('slot', request(CASE, 'B', MODEL))
    b.usage('slot', {'prompt_tokens': 100000000, 'completion_tokens': 10})
    assert read_json(root / 'runs/API_LEDGER.json')['provider_usage_exceeded_reservation'] is True


def test_identity_mismatch_never_scores_as_success():
    raw = valid_raw(); raw['model'] = 'unregistered-model'
    client = Replies([(raw, None)]); rows = []
    final = observe(CASE, 'B', MODEL, client, 1, LOCK, rows.append)
    assert final['status'] == 'identity_error' and final['parsed'] is None


def test_exact_official_display_name_is_a_registered_identity():
    raw = valid_raw(); raw['model'] = MODEL['name']
    rows = []
    final = observe(CASE, 'B', MODEL, Replies([(raw, None)]), 1, LOCK, rows.append)
    assert final['status'] == 'ok' and final['parsed'] is not None


def test_a_reuse_only_when_original_bytes_and_rule_identity_match():
    if not (BENCH / 'incoming/bundle/MANIFEST.json').exists(): pytest.skip('private accepted A bundle absent')
    result = reuse_identity()
    assert result['observations'] == 48 and result['counts'] == {'not_covered': 21, 'ok': 27}


def test_a_duplicate_or_missing_slots_rejected():
    cases = [{'case_id': 'new_019', 'visible_payload_sha256': 'v'}]
    status = {'run_id': 'r', 'observations': 3, 'counts': {'not_covered': 3}}
    identity = {'plan_sha256': 'p', 'frozen_md_sha256': 'f'}
    row = {'record_type': 'observation', 'mode': 'rules', 'simulated': False, 'group': 'A', 'model': 'rules',
           'case_id': 'new_019', 'repetition': 1, 'run_id': 'r', 'plan_sha256': 'p', 'frozen_md_sha256': 'f',
           'request_summary': {'visible_payload_sha256': 'v'}, 'status': 'not_covered', 'parsed': None}
    with pytest.raises(ValueError, match='duplicate'): validate_rows([row, row], cases, status, identity, V2)
    with pytest.raises(ValueError, match='planned slots'): validate_rows([row], cases, status, identity, V2)


def test_server_transport_preserves_failures_and_rejects_output_escape(tmp_path, monkeypatch):
    import importlib.util
    from transfer import manifest, verify
    from bench.v2.runtime import packet, visible_files, rules, REPO
    from bench.v2.import_rules import EXPORT
    package = tmp_path / 'bench/v2/rules_package'; package.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('v2_server_test_only', V2 / 'server/run_rules.py')
    server = importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
    cases = []
    for number in range(17, 25):
        name = f'new_{number:03}'
        public = {}
        for path in visible_files(V2 / 'cases' / name):
            rel = path.relative_to(V2 / 'cases' / name).as_posix()
            target = package / 'cases' / name / rel; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes()); public[rel] = digest(path.read_bytes())
        cases.append({'case_id': name, 'public_files': public, 'visible_payload_sha256': digest(canonical(packet(package / 'cases' / name)))})
    for name in EXPORT:
        source = V2 / name if name == EXPORT[0] else BENCH / name
        target = package / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(source.read_bytes())
    for name in rules():
        target = package / 'original_rules' / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO / name).read_bytes().replace(b'\r\n', b'\n'))
    plan = {'cases': cases, 'rule_sources': rules(), 'adapter_files': {n: digest((package / n).read_bytes()) for n in EXPORT},
            'output_root': 'bench_transfer/test/bundle', 'frozen_md_sha256': 'f', 'plan_sha256': 'p'}
    write_json(package / 'SERVER_PLAN.json', plan); manifest(package)
    def unavailable(*args): raise RuntimeError('test-only execution failure')
    monkeypatch.setattr(server, 'evaluate_case', unavailable)
    monkeypatch.setattr(server, 'versions', lambda: {'test_only': True})
    status = server.execute(package)
    assert status['observations'] == 24 and status['counts'] == {'execution_error': 24}
    out = tmp_path / 'bench/bench_transfer/test/bundle'; assert verify(out)['verified_files'] == 5
    assert server.execute(package)['observations'] == 24  # fixed files replace, not append
    plan['output_root'] = '../outside'; write_json(package / 'SERVER_PLAN.json', plan); manifest(package)
    with pytest.raises(ValueError, match='output must stay'): server.execute(package)
