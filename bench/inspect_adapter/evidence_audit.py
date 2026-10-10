"""Offline post-hoc audit packet: identities and calculations, not an NLP scorer.

Author AI notes stay separate from frozen official labels. No API or shell tools.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from bench.inspect_adapter import pilot

DIRECTORY = pilot.ROOT / 'audit/pilot2'
RECEIPT = pilot.ROOT / 'pilot2/RUN_RECEIPT.json'
METHODS = {'file_stats': 'stats', 'annotation_counts': 'annotation_counts',
           'interval_counts': 'interval_counts'}
STATES = {'supported', 'partial', 'unsupported', 'uncertain'}


def locate(files, pointer):
    """Resolve the cited location, with no claim about observation truth."""
    pilot.validate_pointer(files, pointer)
    name, location = pointer.split(':', 1)
    text = files.text(name)
    if location == 'bytes':
        return {'kind': 'bytes', 'bytes': len(text.encode('utf-8'))}
    if location.isdigit():
        return {'kind': 'line', 'line': int(location), 'text': text.splitlines()[int(location) - 1]}
    if Path(name).suffix == '.json':
        return {'kind': 'field', 'field': location, 'value': json.loads(text)[location]}
    if Path(name).suffix in {'.fa', '.faa', '.fasta'}:
        sequence = files.fasta(name)[location]
        return {'kind': 'fasta_record', 'id': location, 'length': len(sequence),
                'sequence_sha256': pilot.sha(sequence.encode('utf-8'))}
    header, rows = files.table(name)
    if location in header:
        return {'kind': 'column', 'field': location, 'values': [row[location] for row in rows]}
    return {'kind': 'table_record', 'key': location, 'rows': [r for r in rows if r[header[0]] == location]}


def recompute(files, function, arguments):
    """Re-execute only the existing bounded public-byte calculation methods."""
    if function not in METHODS:
        raise ValueError('unsupported calculation operation')
    if function == 'file_stats':
        return files.stats(**arguments)
    return getattr(files, METHODS[function])(**arguments)


def build():
    receipt = pilot.read_json(RECEIPT)
    private = pilot.ROOT / 'work/pilot' / receipt['run_id']
    for name, expected in receipt['artifact_sha256'].items():
        if pilot.sha((pilot.ROOT / name).read_bytes()) != expected:
            raise ValueError('preserved private run differs from receipt')
    results_path = private / 'RESULTS.json'
    results = pilot.read_json(results_path)
    log = pilot.read_json(next((private / 'logs').glob('*.json')))
    samples = {str(s['id']): s for s in log['samples']}
    frozen_manifest = pilot.read_json(pilot.ROOT / 'pilot2/packets.draft.json')
    cases = []
    for row in results['rows']:
        cid = row['case_id']
        files = pilot.PublicFiles(pilot.CASES / cid)
        if files.manifest() != frozen_manifest[cid]:
            raise ValueError('public sample bytes changed since frozen run')
        sample = samples[cid]
        calls = {c['id']: c for m in sample['messages'] for c in m.get('tool_calls', [])}
        traces = []
        for message in sample['messages']:
            if message['role'] != 'tool' or message.get('function') not in METHODS:
                continue
            call = calls[message['tool_call_id']]
            if message.get('error') or call['function'] != message['function']:
                raise ValueError('calculation trace has an error or mismatched call')
            recorded = json.loads(message['content'])
            if recompute(files, call['function'], call['arguments']) != recorded:
                raise ValueError('calculation trace differs from public-byte replay')
            traces.append({'function': call['function'], 'arguments': call['arguments'],
                           'tool_call_id': call['id'], 'recorded_result': recorded})
        parsed = row['parsed']
        cases.append({'case_id': cid, 'public_manifest': files.manifest(),
                      'evidence': [{'index': i, **e, 'item_sha256': pilot.sha(pilot.canonical(e)),
                                    'cited_location': locate(files, e['pointer'])}
                                   for i, e in enumerate(parsed['evidence'], 1)],
                      'action': parsed['action'],
                      'action_sha256': pilot.sha(parsed['action'].encode('utf-8')),
                      'calculation_trace': traces})
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    (DIRECTORY / 'MODEL_RESULTS.json').write_bytes(results_path.read_bytes())
    pilot.write_json(DIRECTORY / 'PACKET.json', {
        'version': 'posthoc-evidence-packet-1', 'run_id': receipt['run_id'],
        'source_receipt_sha256': pilot.sha(RECEIPT.read_bytes()),
        'source_results_sha256': pilot.sha(results_path.read_bytes()),
        'review_kind': 'author_ai_posthoc; not independent or blind or human',
        'official_score_changed': False, 'cases': cases})
    print(f'BUILT: {len(cases)} cases; {sum(len(c["calculation_trace"]) for c in cases)} '
          'calculation traces replayed; no provider calls')


def validate_review(packet, review):
    if review['packet_sha256'] != pilot.sha(pilot.canonical(packet)):
        raise ValueError('review refers to a different audit packet')
    if (review['review_kind'] != 'author_ai_posthoc' or review['blind'] is not False or
        review['independent'] is not False or review['human_review'] is not False or
        review['official_score_changed'] is not False):
        raise ValueError('review identity or official-score scope misrepresented')
    cases = {row['case_id']: row for row in review['cases']}
    if len(cases) != len(review['cases']) or set(cases) != {row['case_id'] for row in packet['cases']}:
        raise ValueError('review must retain every planned case exactly once')
    for sample in packet['cases']:
        row = cases[sample['case_id']]
        if row['action_sha256'] != sample['action_sha256']:
            raise ValueError('action review refers to a different response')
        annotations = {e['index']: e for e in row['evidence']}
        if len(annotations) != len(row['evidence']) or set(annotations) != {e['index'] for e in sample['evidence']}:
            raise ValueError('review must cover every original evidence item exactly once')
        for evidence in sample['evidence']:
            note = annotations[evidence['index']]
            if note['item_sha256'] != evidence['item_sha256']:
                raise ValueError('review refers to a different evidence item')
            if note['citation_fidelity'] not in STATES or not note['reason'].strip():
                raise ValueError('invalid or unexplained author diagnosis')
        if not row['action_review']['reason'].strip():
            raise ValueError('unexplained action review')


def verify():
    packet = pilot.read_json(DIRECTORY / 'PACKET.json')
    results_path = DIRECTORY / 'MODEL_RESULTS.json'
    if (pilot.sha(RECEIPT.read_bytes()) != packet['source_receipt_sha256'] or
        pilot.sha(results_path.read_bytes()) != packet['source_results_sha256']):
        raise ValueError('audit source or receipt changed')
    receipt = pilot.read_json(RECEIPT)
    frozen_path = pilot.ROOT / 'pilot2/FROZEN.json'
    if pilot.sha(frozen_path.read_bytes()) != receipt['frozen_sha256']:
        raise ValueError('original frozen identity differs from run receipt')
    frozen = pilot.read_json(frozen_path)
    manifest_path = pilot.ROOT / 'pilot2/packets.draft.json'
    if pilot.sha(manifest_path.read_bytes()) != frozen['files']['packets.draft.json']:
        raise ValueError('public manifest differs from original freeze')
    frozen_manifest = pilot.read_json(manifest_path)
    result_hashes = [value for name, value in receipt['artifact_sha256'].items() if name.endswith('/RESULTS.json')]
    if result_hashes != [packet['source_results_sha256']]:
        raise ValueError('exported results not bound to original run receipt')
    results = pilot.read_json(results_path)
    rows = {row['case_id']: row for row in results['rows']}
    if (len(rows) != 4 or len(results['rows']) != 4 or
        {c['case_id'] for c in packet['cases']} != set(rows) or len(packet['cases']) != 4 or
        results['run_id'] != receipt['run_id'] or packet['run_id'] != receipt['run_id']):
        raise ValueError('audit dropped or replaced a planned observation')
    evidence_count, traces = 0, 0
    for case in packet['cases']:
        files = pilot.PublicFiles(pilot.CASES / case['case_id'])
        if (files.manifest() != case['public_manifest'] or
            case['public_manifest'] != frozen_manifest[case['case_id']]):
            raise ValueError('public bytes differ from audit packet')
        parsed = rows[case['case_id']]['parsed']
        original = [{'pointer': e['pointer'], 'observation': e['observation']} for e in case['evidence']]
        if (original != parsed['evidence'] or case['action'] != parsed['action'] or
            case['action_sha256'] != pilot.sha(parsed['action'].encode('utf-8'))):
            raise ValueError('audit altered model response')
        for index, evidence in enumerate(case['evidence'], 1):
            if (evidence['index'] != index or
                evidence['item_sha256'] != pilot.sha(pilot.canonical(original[index - 1])) or
                locate(files, evidence['pointer']) != evidence['cited_location']):
                raise ValueError('audit changed a citation or its cited location')
            evidence_count += 1
        receipt_sample = next(s for s in receipt['samples'] if s['case_id'] == case['case_id'])
        expected_traces = sum(receipt_sample['tool_functions'].get(name, 0) for name in METHODS)
        if (len(case['calculation_trace']) != expected_traces or
            len({t['tool_call_id'] for t in case['calculation_trace']}) != expected_traces):
            raise ValueError('audit dropped or duplicated a calculation trace')
        for trace in case['calculation_trace']:
            if recompute(files, trace['function'], trace['arguments']) != trace['recorded_result']:
                raise ValueError('recorded calculation does not reproduce')
            traces += 1
    review = pilot.read_json(DIRECTORY / 'AUTHOR_REVIEW.json')
    validate_review(packet, review)
    fidelity = Counter(e['citation_fidelity'] for row in review['cases'] for e in row['evidence'])
    private_paths = [pilot.ROOT / name for name in receipt['artifact_sha256']]
    private_available = all(path.exists() for path in private_paths)
    private_checked = 0
    for path, expected in zip(private_paths, receipt['artifact_sha256'].values()):
        if path.exists():
            if pilot.sha(path.read_bytes()) != expected:
                raise ValueError('available private logs changed since receipt')
            private_checked += 1
    return {'status': 'pass', 'meaning': 'packet identities and calculations verified; not model quality success',
            'planned_cases': 4, 'evidence_items': evidence_count, 'calculation_traces': traces,
            'author_ai_citation_fidelity_counts': dict(fidelity), 'official_counts': results['counts'],
            'official_score_changed': False, 'independent_review': False, 'human_review': False,
            'private_native_logs_reverified': private_available,
            'private_artifacts_reverified': private_checked, 'provider_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--build', action='store_true')
    action.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.build:
        build()
    else:
        print(json.dumps(verify(), ensure_ascii=False, sort_keys=True))
