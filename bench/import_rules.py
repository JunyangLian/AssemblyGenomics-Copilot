"""Verify server A transport and planned slots before local scoring admission."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from harness_common import BENCH, canonical, digest, read_json, write_json, parse_response
from run_plan import verify as verify_plan
from transfer import verify as verify_transfer
from visible_input import packet


def accept(bundle, root=BENCH):
    locked = verify_plan(root)
    receipt = verify_transfer(bundle)
    status = read_json(bundle / 'STATUS.json')
    identity = read_json(bundle / 'identity.json')
    if status.get('status') != 'complete' or status.get('api_calls') != 0:
        raise ValueError('server A transport is incomplete or has unexpected model calls')
    for doc in [status, identity]:
        for field in ['plan_sha256', 'frozen_md_sha256']:
            if doc.get(field) != locked[field]:
                raise ValueError('server result identity differs')
    if identity.get('rule_sources') != locked['plan']['rule_sources']:
        raise ValueError('server existing rule identity differs')
    from make_rules_package import EXPORT
    if identity.get('adapter_files') != {n:digest((root / n).read_bytes()) for n in EXPORT}:
        raise ValueError('server adapter identity differs')
    rows = [read_json_line for read_json_line in
            (__import__('json').loads(line) for line in (bundle / 'records.jsonl').read_text(encoding='utf-8').splitlines())]
    slots = set()
    wanted = {(r['case_id'], i) for r in locked['plan']['cases'] for i in range(1,4)}
    for row in rows:
        slot = (row['case_id'], row['repetition'])
        if slot not in wanted or slot in slots:
            raise ValueError('unexpected/duplicate A observation')
        slots.add(slot)
        if (row.get('mode') != 'rules' or row.get('group') != 'A' or row.get('model') != 'rules' or
            row.get('simulated') is not False or row.get('record_type') != 'observation' or
            row.get('run_id') != status['run_id']):
            raise ValueError('non-server A observation')
        if row['plan_sha256'] != locked['plan_sha256'] or row['frozen_md_sha256'] != locked['frozen_md_sha256']:
            raise ValueError('observation identity differs')
        case = root / 'cases' / row['case_id']
        if row.get('request_summary', {}).get('visible_payload_sha256') != digest(canonical(packet(case))):
            raise ValueError('server payload does not match frozen public inputs')
        if row['status'] not in {'ok', 'not_covered', 'execution_error'}:
            raise ValueError('invalid A status')
        if row['status'] == 'ok':
            raw = {'choices':[{'message':{'content':canonical(row['parsed']).decode('utf-8')}}]}
            parsed, error = parse_response(raw, case, root)
            if error or parsed != row['parsed']:
                raise ValueError('invalid A structured output')
        elif row.get('parsed') is not None:
            raise ValueError('failed A observation must not carry a verdict')
    if slots != wanted or status['observations'] != len(wanted):
        raise ValueError('missing planned A observations')
    from collections import Counter
    if status['counts'] != dict(Counter(r['status'] for r in rows)):
        raise ValueError('A summary counts differ')
    rid = status['run_id']
    if '/' in rid or '\\' in rid or ':' in rid or rid.startswith('.'):
        raise ValueError('invalid server run_id')
    target = root / 'runs' / rid
    if target.exists():
        if (target / 'records.jsonl').read_bytes() != (bundle / 'records.jsonl').read_bytes():
            raise ValueError('existing A run differs')
    else:
        target.mkdir(parents=True)
        for name in ['records.jsonl', 'STATUS.json', 'versions.json', 'identity.json']:
            shutil.copyfile(bundle / name, target / name)
    write_json(root / 'A_RECEIPT.json', {**receipt, 'status':'pass', 'run_id':rid,
                                      'observations':len(rows), 'counts':status['counts'], 'plan_sha256':locked['plan_sha256']})
    return {'status':'pass', 'run_id':rid, 'observations':len(rows), 'counts':status['counts']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('bundle', type=Path); args=parser.parse_args()
    print(accept(args.bundle))
