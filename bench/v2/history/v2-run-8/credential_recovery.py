"""Explicit human-authorized transport recovery; never inspect QC answers."""
from bench.v2.runtime import read_json, digest, canonical


def slot(row):
    return row['model'], row['group'], row['case_id'], row['repetition']


def eligible(rows):
    final_attempt = {slot(r): r for r in rows if r['record_type'] == 'attempt'}
    return {slot(r): r for r in rows if r['record_type'] == 'observation'
            and r['status'] == 'api_error'
            and final_attempt.get(slot(r), {}).get('error') == 'HTTP 429'
            and final_attempt[slot(r)].get('called') is True}


def document(root, locked):
    pin = locked['plan'].get('credential_recovery')
    if not pin: return None
    path = root / pin['file']
    if digest(path.read_bytes()) != pin['sha256']:
        raise ValueError('credential recovery registration changed')
    doc = read_json(path)
    if (doc.get('user_authorized') is not True or not doc.get('budget_authorization_quote')
        or doc.get('parent_version') != locked['plan']['resume']['parent_version']
        or doc.get('parent_plan_sha256') != locked['plan']['parent_plan_sha256']
        or doc.get('frozen_md_sha256') != locked['frozen_md_sha256']
        or doc.get('reason_filter') != 'HTTP 429 only; no QC-answer selection'
        or doc.get('automatic_network_retries') != 0):
        raise ValueError('invalid human credential-recovery authorization')
    return doc


def approved_caps(root, locked):
    doc = document(root, locked)
    if not doc: raise ValueError('explicit credential-recovery budget missing')
    prior = doc['previous_reservations']; count = len(doc['slots'])
    derived = {'max_calls':prior['calls']+2*count,
        'max_input_tokens':prior['input_reserved']+sum(s['initial_input_reservation']+s['repair_input_reservation'] for s in doc['slots']),
        'max_output_tokens':prior['output_reserved']+2*count*8192}
    if derived != doc['approved_cumulative_caps'] or count != doc['recovery_observations']:
        raise ValueError('credential recovery cap derivation changed')
    return doc, derived


def registered(root, locked, source_rows=None):
    doc = document(root, locked)
    if not doc: return None, set()
    if source_rows is None:
        import json
        path = root / locked['plan']['resume']['records']
        if digest(path.read_bytes()) != locked['plan']['resume']['records_sha256']:
            raise ValueError('credential recovery source changed')
        source_rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    allowed = eligible(source_rows)
    configured = {slot(r): r for r in doc['slots']}
    if len(configured) != len(doc['slots']) or set(configured) != set(allowed):
        raise ValueError('recovery must include all and only HTTP429 observations')
    for key, row in allowed.items():
        if configured[key]['old_observation_sha256'] != digest(canonical(row)):
            raise ValueError('recovery original failed observation changed')
    if len(allowed) != doc['recovery_observations']:
        raise ValueError('recovery count differs')
    return doc, set(allowed)


def duplicate_allowed(doc, allowed, version, semantic):
    """Only an explicitly listed parent's 429 reservation may be retried once."""
    if not doc or version != doc['parent_version']: return False
    model, group, case, repeat, attempt = semantic.split(':')
    return (model, group, case, int(repeat)) in allowed
