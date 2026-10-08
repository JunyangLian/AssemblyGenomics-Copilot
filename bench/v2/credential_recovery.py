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
    if doc.get('version') == 'v2-credential-recovery-2':
        pin = doc['inherited_approval']
        path = (root / pin['file']).resolve(strict=True)
        if (root / 'history').resolve() not in path.parents or digest(path.read_bytes()) != pin['sha256']:
            raise ValueError('inherited recovery approval changed')
        previous = read_json(path)
        caps = {k: previous[k] for k in ('max_calls','max_input_tokens','max_output_tokens')}
        if (caps != doc['approved_cumulative_caps']
            or previous.get('user_credential_recovery_authorization_quote') != doc['budget_authorization_quote']):
            raise ValueError('third credential cannot silently enlarge inherited caps')
        return doc, caps
    prior = doc['previous_reservations']; count = len(doc['slots'])
    derived = {'max_calls':prior['calls']+2*count,
        'max_input_tokens':prior['input_reserved']+sum(s['initial_input_reservation']+s['repair_input_reservation'] for s in doc['slots']),
        'max_output_tokens':prior['output_reserved']+2*count*8192}
    if derived != doc['approved_cumulative_caps'] or count != doc['recovery_observations']:
        raise ValueError('credential recovery cap derivation changed')
    return doc, derived


def priority_candidates(root, locked, doc, source_rows):
    """Unfinished original429 slots and the latest429, restricted to active models."""
    from bench.v2.resume import rows
    pin = doc['original_429_source']
    path = (root / pin['file']).resolve(strict=True)
    if (root / 'history').resolve() not in path.parents or digest(path.read_bytes()) != pin['sha256']:
        raise ValueError('original HTTP429 source changed')
    original = eligible(rows(path))
    observed = {slot(r) for r in source_rows if r['record_type']=='observation'}
    current = eligible(source_rows)
    active = locked['plan']['execution']['active_model_names']
    if active != doc['active_model_names']:
        raise ValueError('priority execution scope changed')
    selected = {k:v for k,v in original.items() if k not in observed and k[0] in active}
    selected.update({k:v for k,v in current.items() if k[0] in active})
    versions = {k: ([pin['version'],doc['parent_version']] if k in current and k in original
                   else [doc['parent_version']] if k in current else [pin['version']]) for k in selected}
    return selected, versions


def registered(root, locked, source_rows=None):
    doc = document(root, locked)
    if not doc: return None, set()
    if source_rows is None:
        import json
        path = root / locked['plan']['resume']['records']
        if digest(path.read_bytes()) != locked['plan']['resume']['records_sha256']:
            raise ValueError('credential recovery source changed')
        source_rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    if doc.get('version') == 'v2-credential-recovery-2':
        allowed, versions = priority_candidates(root, locked, doc, source_rows)
    else:
        allowed, versions = eligible(source_rows), None
    configured = {slot(r): r for r in doc['slots']}
    if len(configured) != len(doc['slots']) or set(configured) != set(allowed):
        raise ValueError('recovery must include all and only HTTP429 observations')
    for key, row in allowed.items():
        if configured[key]['old_observation_sha256'] != digest(canonical(row)):
            raise ValueError('recovery original failed observation changed')
        if versions and configured[key].get('reservation_versions') != versions[key]:
            raise ValueError('recovery ancestor reservations changed')
    if len(allowed) != doc['recovery_observations']:
        raise ValueError('recovery count differs')
    return doc, set(allowed)


def duplicate_allowed(doc, allowed, version, semantic):
    """Only an explicitly listed parent's 429 reservation may be retried once."""
    if not doc: return False
    model, group, case, repeat, attempt = semantic.split(':')
    key = (model, group, case, int(repeat))
    if key not in allowed: return False
    if doc.get('version') == 'v2-credential-recovery-2':
        return version in next(r['reservation_versions'] for r in doc['slots'] if slot(r)==key)
    return version == doc['parent_version']
