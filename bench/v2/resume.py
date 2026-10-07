"""Carry prior observations verbatim and fail unfinished reservations without resending."""
from collections import Counter
import json
from bench.v2.runtime import canonical, digest, read_json, write_json, request, summary


def slot(row):
    return row['model'], row['group'], row['case_id'], row['repetition']


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []


def parent_records(root, locked):
    registered = locked['plan'].get('resume')
    if not registered: return []
    for field in ('receipt', 'records'):
        path = (root / registered[field]).resolve(strict=True)
        if root.resolve() not in path.parents or digest(path.read_bytes()) != registered[field + '_sha256']:
            raise ValueError('resume provenance changed')
    receipt = read_json(root / registered['receipt'])
    parent = read_json(root / 'history' / registered['parent_version'] / 'RUN_PLAN.json')
    if receipt['parent_plan_sha256'] != locked['plan']['parent_plan_sha256']:
        raise ValueError('resume parent plan differs')
    for name, sha in receipt['original_log_sha256'].items():
        path = (root / name).resolve(strict=True)
        if (root / 'runs').resolve() not in path.parents or digest(path.read_bytes()) != sha:
            raise ValueError('original model responses changed')
    if parent['cases'] != locked['plan']['cases'] or parent['shared_implementation'] != locked['plan']['shared_implementation']:
        raise ValueError('resume requires identical public packets and request/parser helpers')
    previous = {m['name']: m for m in parent['models']}
    selected = {m['name']: m for m in locked['plan']['models']}
    result = []
    for row in rows(root / registered['records']):
        if row['model'] not in selected:
            raise ValueError('cannot discard an already attempted removed model')
        if selected[row['model']] != previous[row['model']]:
            raise ValueError('resumed model protocol changed')
        if row['plan_sha256'] != receipt['parent_plan_sha256'] or row['frozen_md_sha256'] != locked['frozen_md_sha256']:
            raise ValueError('unexpected source observation identity')
        if row.get('request_summary'):
            body = request(root / 'cases' / row['case_id'], row['group'], selected[row['model']], root, row.get('attempt', 0) > 0)
            if row['request_summary'] != summary(root / 'cases' / row['case_id'], body, root):
                raise ValueError('resumed request differs from current public request')
        provenance = {'plan_sha256': row['plan_sha256'], 'run_id': row.get('run_id'),
            'record_sha256': digest(canonical(row)), 'source_log': row.get('source_log'),
            'source_records': registered['records'], 'source_records_sha256': registered['records_sha256']}
        result.append({**row, 'plan_sha256': locked['plan_sha256'], 'reused_from': provenance})
    observations = [r for r in result if r['record_type'] == 'observation']
    keys = [slot(r) for r in observations]
    if len(keys) != len(set(keys)) or len(keys) != receipt['observations']:
        raise ValueError('resume slots missing or duplicated')
    if dict(Counter(r['status'] for r in observations)) != receipt['counts']:
        raise ValueError('resume cannot select successful answers or discard failures')
    return result


def prepare_api(root, locked, make_id):
    """Create a durable directory index before calls; on restart append only unseen slots."""
    path = root / 'API_RUNS.json'
    if path.exists():
        index = read_json(path)
        if index.get('mode') != 'api' or index['plan_sha256'] != locked['plan_sha256']:
            raise ValueError('existing API index belongs to another plan')
    else:
        paths = []
        for group in locked['plan']['groups']:
            for model in locked['plan']['models']:
                rid = make_id(model['name'], group, locked['frozen_md_sha256'])
                directory = root / 'runs' / rid; directory.mkdir(parents=True, exist_ok=False)
                (directory / 'records.jsonl').write_bytes(b'')
                paths.append(directory.relative_to(root).as_posix())
        index = {'mode': 'api', 'plan_sha256': locked['plan_sha256'], 'runs': paths}
        write_json(path, index)
    expected = [(g, m['name']) for g in locked['plan']['groups'] for m in locked['plan']['models']]
    if len(index['runs']) != len(expected) or len(set(index['runs'])) != len(expected):
        raise ValueError('API index must contain exactly one directory per model/group')
    directories, known, all_rows = {}, {}, []
    for name, (group, model) in zip(index['runs'], expected):
        directory = (root / name).resolve(strict=True)
        if (root / 'runs').resolve() not in directory.parents:
            raise ValueError('API index escaped runs')
        directories[group, model] = directory
        selected = rows(directory / 'records.jsonl')
        for row in selected:
            if row['plan_sha256'] != locked['plan_sha256'] or row['model'] != model or row['group'] != group or row.get('mode') != 'api':
                raise ValueError('mixed API indexed records')
            if row['record_type'] == 'observation':
                key = slot(row)
                if key in known: raise ValueError('duplicate API observation')
                known[key] = row
        all_rows.extend(selected)
    def emit(row):
        directory = directories[row['group'], row['model']]
        row = {**row, 'run_id': directory.name}
        with (directory / 'records.jsonl').open('ab') as stream:
            stream.write(canonical(row)); stream.flush()
        all_rows.append(row)
        if row['record_type'] == 'observation': known[slot(row)] = row
    # A crash partway through importing a parent record must not duplicate its attempts.
    reused = {r['reused_from']['record_sha256'] for r in all_rows if r.get('reused_from')}
    for row in parent_records(root, locked):
        if row['reused_from']['record_sha256'] not in reused:
            if row['record_type'] == 'observation' and slot(row) in known:
                raise ValueError('parent observation conflicts with new result')
            emit(row); reused.add(row['reused_from']['record_sha256'])
    # Any reservation without a final observation is an unknown, never a license to resend.
    ledger = read_json(root / 'runs/API_LEDGER.json')
    pending = {}
    for entry in ledger['slots']:
        version, model, group, case, rep, attempt = entry['slot'].split(':')
        if version != locked['plan']['version']: continue
        key = (model, group, case, int(rep))
        if key not in known: pending.setdefault(key, []).append(entry)
    for (model, group, case, rep), entries in pending.items():
        emit({'record_type': 'observation', 'mode': 'api', 'model': model, 'group': group,
            'case_id': case, 'repetition': rep, 'plan_sha256': locked['plan_sha256'],
            'frozen_md_sha256': locked['frozen_md_sha256'], 'status': 'interrupted', 'parsed': None,
            'response': None, 'usage': None, 'attempts': len(entries),
            'source_reservations': [r['slot'] for r in entries],
            'error': 'interrupted after reservation; receipt unknown; never resend'})
    paused = {r['model'] for r in known.values() if r['status'] == 'identity_error'}
    return directories, known, paused
