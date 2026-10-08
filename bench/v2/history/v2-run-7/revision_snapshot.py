"""Archive a stopped live plan before a human-authorized scope revision."""
from collections import Counter
import json
import shutil
from bench.v2.runtime import canonical, digest, read_json, write_json


def capture(root, parent_version, work_name):
    from bench.v2.plan import verify
    locked = verify(root)
    if locked['plan']['version'] != parent_version: raise ValueError('unexpected revision parent')
    if (root / 'runs/API_ACTIVE.lock').exists(): raise ValueError('wait for graceful stop before archive')
    out = root / 'history' / parent_version
    if out.exists(): raise ValueError('history already exists')
    index = read_json(root / 'API_RUNS.json')
    if index['plan_sha256'] != locked['plan_sha256']: raise ValueError('old index differs')
    observations, records, logs = {}, [], {}
    for name in index['runs']:
        path = (root / name / 'records.jsonl').resolve(strict=True)
        if (root / 'runs').resolve() not in path.parents: raise ValueError('indexed source escaped runs')
        logs[path.relative_to(root).as_posix()] = digest(path.read_bytes())
        for row in [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]:
            if row.get('mode') != 'api' or row['plan_sha256'] != locked['plan_sha256']:
                raise ValueError('mixed source log')
            records.append({**row, 'source_log': path.relative_to(root).as_posix()})
            if row['record_type'] == 'observation':
                key = (row['model'], row['group'], row['case_id'], row['repetition'])
                if key in observations: raise ValueError('duplicate observation')
                observations[key] = row
    ledger = read_json(root / 'runs/API_LEDGER.json')
    for entry in ledger['slots']:
        version, model, group, case, rep, attempt = entry['slot'].split(':')
        if version == parent_version and (model, group, case, int(rep)) not in observations:
            raise ValueError('unfinished reservation after graceful stop; review required')
    out.mkdir(parents=True)
    names = set(locked['plan']['implementation']) | {
        'RUN_PLAN.json', 'RUN_PLAN.sha256', 'API_APPROVAL.json', 'MOCK_REPORT.json', 'MOCK_REPORT.md',
        'MOCK_RUNS.json', 'API_APPROVAL.template.json', 'A_REUSE_RECEIPT.json', 'RULES_PACKAGE.json', 'API_RUNS.json'}
    for name in sorted(names):
        target = out / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes())
    (out / 'API_LEDGER.json').write_bytes((root / 'runs/API_LEDGER.json').read_bytes())
    (out / 'resume_records.jsonl').write_bytes(b''.join(canonical(r) for r in records))
    write_json(out / 'RESUME_RECEIPT.json', {'status': 'pass', 'parent_version': parent_version,
        'parent_plan_sha256': locked['plan_sha256'], 'original_log_sha256': logs,
        'records_sha256': digest((out / 'resume_records.jsonl').read_bytes()),
        'observations': len(observations), 'counts': dict(Counter(r['status'] for r in observations.values())),
        'cumulative_reserved_calls': ledger['calls'], 'budgets_refunded': False,
        'gracefully_stopped': True, 'new_interruptions': 0,
        'primary_new_observations': sum(r['case_id'].startswith('new_') for r in observations.values()),
        'policy': 'archive all outputs/errors/unknowns; no selective QC reruns'})
    marker = root / 'runs/STOP_AFTER_CURRENT_REQUEST'
    if marker.exists(): (out / 'STOP_AFTER_CURRENT_REQUEST').write_bytes(marker.read_bytes())
    schedule = root / 'runs/SCHEDULER_STATUS.json'
    if schedule.exists(): (out / 'SCHEDULER_STATUS.json').write_bytes(schedule.read_bytes())
    (root / 'API_RUNS.json').unlink()
    source = (root / 'rules_package').resolve(); work = (root / 'work').resolve()
    destination = (work / work_name).resolve()
    if source.exists():
        if root.resolve() not in source.parents or work not in destination.parents or destination.exists():
            raise ValueError('archive move must stay inside v2 and not overwrite')
        shutil.move(str(source), str(destination))
    (work / (work_name + '.zip')).write_bytes((root / 'rules_package.zip').read_bytes())
    return read_json(out / 'RESUME_RECEIPT.json')
