"""Admit real A results only after provenance, public inputs and slots match."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from collections import Counter
import json
from bench.v2.runtime import V2, BENCH, canonical, digest, read_json, write_json, packet, parse_response, rules
from transfer import verify as transport_verify
from rule_adapter import RULE_MAP

EXPORT = ['server/run_rules.py', 'rule_adapter.py', 'visible_input.py', 'transfer.py']


def validate_rows(rows, cases, status, identity, root):
    wanted = {(c['case_id'], i): c for c in cases for i in range(1, 4)}
    seen = set()
    for r in rows:
        slot = (r.get('case_id'), r.get('repetition'))
        if slot not in wanted or slot in seen:
            raise ValueError('unexpected/duplicate A slot')
        seen.add(slot)
        if (r.get('record_type') != 'observation' or r.get('mode') != 'rules'
            or r.get('group') != 'A' or r.get('model') != 'rules' or r.get('simulated') is not False
            or r.get('run_id') != status['run_id'] or r.get('plan_sha256') != identity['plan_sha256']
            or r.get('frozen_md_sha256') != identity['frozen_md_sha256']
            or r.get('request_summary', {}).get('visible_payload_sha256') != wanted[slot]['visible_payload_sha256']):
            raise ValueError('A observation/public input identity differs')
        if r.get('status') not in ('ok', 'execution_error', 'not_covered'):
            raise ValueError('invalid A status')
        if r['status'] == 'ok':
            case = root / 'cases' / r['case_id']
            parsed, error = parse_response({'choices': [{'message': {'content': canonical(r['parsed']).decode('utf-8')}}]}, case, root)
            if error or parsed != r['parsed']:
                raise ValueError('invalid structured A result')
        elif r.get('parsed') is not None:
            raise ValueError('failed A slot cannot carry parsed verdict')
    if seen != set(wanted) or status['observations'] != len(wanted) or status['counts'] != dict(Counter(r['status'] for r in rows)):
        raise ValueError('A planned slots/summary differ')


def reuse_identity(root=V2):
    receipt = read_json(BENCH / 'A_RECEIPT.json')
    bundle = BENCH / 'incoming/bundle'
    transport = transport_verify(bundle)
    if receipt['status'] != 'pass' or transport['manifest_sha256'] != receipt['manifest_sha256']:
        raise ValueError('previous A receipt/transport differs')
    identity, status = read_json(bundle / 'identity.json'), read_json(bundle / 'STATUS.json')
    prior = read_json(BENCH / 'RUN_PLAN.json')
    if (identity['rule_sources'] != rules() or prior['rule_sources'] != rules()
        or prior['rule_mapping'] != RULE_MAP or identity['frozen_md_sha256'] != digest((BENCH / 'FROZEN.md').read_bytes())
        or status['status'] != 'complete' or status['api_calls'] != 0
        or any(identity['adapter_files'][n] != digest((BENCH / n).read_bytes()) for n in EXPORT[1:])):
        raise ValueError('original A rules, adapter or frozen version differs')
    cases = []
    for old in prior['cases']:
        new_id = old['case_id'].replace('case_', 'regression_')
        for name, sha in old['public_files'].items():
            if digest((root / 'cases' / new_id / name).read_bytes()) != sha:
                raise ValueError('regression public bytes differ from prior A input')
        payload = digest(canonical(packet(BENCH / 'cases' / old['case_id'])))
        if payload != digest(canonical(packet(root / 'cases' / new_id))):
            raise ValueError('regression serialized packet differs')
        cases.append({**old, 'visible_payload_sha256': payload})
    rows = [json.loads(s) for s in (bundle / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
    validate_rows(rows, cases, status, identity, BENCH)
    if identity['plan_sha256'] not in {prior.get('rules_parent_plan_sha256'), digest((BENCH / 'RUN_PLAN.json').read_bytes())}:
        raise ValueError('prior A plan not registered for reuse')
    return {'receipt_sha256': digest((BENCH / 'A_RECEIPT.json').read_bytes()),
            'manifest_sha256': transport['manifest_sha256'], 'records_sha256': digest((bundle / 'records.jsonl').read_bytes()),
            'rule_sources': identity['rule_sources'], 'adapter_files': identity['adapter_files'],
            'run_id': status['run_id'], 'plan_sha256': identity['plan_sha256'], 'observations': len(rows),
            'counts': status['counts']}


def reuse(root=V2):
    from bench.v2.plan import verify
    locked = verify(root)
    source = BENCH / 'incoming/bundle/records.jsonl'
    rows = [json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    for row in rows:
        provenance = {k: row[k] for k in ('run_id', 'case_id', 'plan_sha256', 'frozen_md_sha256')}
        provenance['source_record_sha256'] = digest(canonical(row))
        row.update(case_id=row['case_id'].replace('case_', 'regression_'), mode='rules_reuse',
                   run_id='v2-reuse-' + locked['plan_sha256'][:12], reused_from=provenance,
                   plan_sha256=locked['plan_sha256'], frozen_md_sha256=locked['frozen_md_sha256'])
    target = root / 'runs' / ('v2-reuse-' + locked['plan_sha256'][:12])
    target.mkdir(parents=True, exist_ok=True)
    data = b''.join(canonical(r) for r in rows)
    p = target / 'records.jsonl'
    if p.exists() and p.read_bytes() != data:
        raise ValueError('existing reused run differs')
    p.write_bytes(data)
    write_json(root / 'A_REUSE_RECEIPT.json', {'status': 'pass', 'run': target.relative_to(root).as_posix(),
        'plan_sha256': locked['plan_sha256'], 'source': locked['plan']['a_reuse'],
        'observations': len(rows), 'new_executions': 0, 'api_calls': 0, 'records_sha256': digest(data)})
    return rows


def accept(bundle, root=V2):
    from bench.v2.plan import verify
    locked = verify(root)
    receipt = transport_verify(bundle)
    status, identity = read_json(bundle / 'STATUS.json'), read_json(bundle / 'identity.json')
    if status.get('status') != 'complete' or status.get('api_calls') != 0:
        raise ValueError('server A incomplete or contains model calls')
    for doc in (status, identity):
        if doc['plan_sha256'] != locked['plan_sha256'] or doc['frozen_md_sha256'] != locked['frozen_md_sha256']:
            raise ValueError('server v2 identity mismatch')
    expected_adapters = {n: digest((root / n if n == EXPORT[0] else BENCH / n).read_bytes()) for n in EXPORT}
    if identity['rule_sources'] != locked['plan']['rule_sources'] or identity['adapter_files'] != expected_adapters:
        raise ValueError('server existing rules or adapter differ')
    cases = [c for c in locked['plan']['cases'] if c['case_id'].startswith('new_')]
    rows = [json.loads(s) for s in (bundle / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
    validate_rows(rows, cases, status, identity, root)
    rid = status['run_id']
    if any(c in rid for c in '/\\:') or rid.startswith('.'):
        raise ValueError('invalid run_id')
    target = root / 'runs' / rid; target.mkdir(parents=True, exist_ok=True)
    for name in ('records.jsonl', 'STATUS.json', 'identity.json', 'versions.json'):
        path = target / name
        if path.exists() and path.read_bytes() != (bundle / name).read_bytes():
            raise ValueError('existing server result differs')
        path.write_bytes((bundle / name).read_bytes())
    reused = reuse(root)
    write_json(root / 'A_RECEIPT.json', {**receipt, 'status': 'pass', 'plan_sha256': locked['plan_sha256'],
        'new_run': target.relative_to(root).as_posix(), 'new_observations': len(rows), 'reused_observations': len(reused),
        'total_observations': len(rows) + len(reused), 'api_calls': 0})
    return read_json(root / 'A_RECEIPT.json')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('bundle', type=Path, nargs='?'); p.add_argument('--reuse', action='store_true')
    args = p.parse_args()
    if args.reuse:
        print('PASS: ' + str(len(reuse())) + ' A observations reused; 0 new executions')
    elif args.bundle:
        print(accept(args.bundle))
    else:
        p.error('bundle or --reuse is required')
