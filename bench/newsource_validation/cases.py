"""Predeclared source selection, deterministic pairs and private draft validation."""
import argparse
from collections import defaultdict
import csv
import io
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator
from bench.inspect_adapter import t3_packets as old

DIRECTORY = Path(__file__).resolve().parent
ASSIGNMENT = [('GCF_059516105.1', 'protein'), ('GCF_947243775.1', 'parent'),
              ('GCF_000001215.4', 'coordinate'), ('GCF_027887165.2', 'protein'),
              ('GCF_000181795.1', 'parent'), ('GCF_053813885.1', 'coordinate')]
POLICY = {**old.POLICY, 'seed': 20261011,
          'case_order': 'sort SHA256(seed|accession|variant) then assign qc_NNN',
          'artifact_read_pages_maximum': 4, 'page_lines': 200, 'page_bytes': 16000,
          'candidate_limit_definition': 'first 50 eligible blocks, not first 50 raw genes',
          'normal_scope': 'only declared closed connected coding subset'}
FAMILIES = {'protein': 'protein_identifier_connection', 'parent': 'parent_reference_closure',
            'coordinate': 'child_parent_interval'}
KEYS = {'protein': 'missing_sequence_lines', 'parent': 'unresolved_parent_lines',
        'coordinate': 'incompatible_parent_lines'}
OBSERVED = {'protein': 'gff_faa_link_missing', 'parent': 'gff_reference_unresolved',
            'coordinate': 'gff_hierarchy_inconsistent'}


def immutable(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError('existing draft changed; preserve it and create a version: ' + str(path))
    path.write_bytes(data)


def pages(data):
    """Mirror existing read_file page limits without choosing informative lines."""
    count, index = 0, 0
    lines = data.decode('utf-8').splitlines()
    while index < len(lines):
        size, taken = 0, 0
        for line in lines[index:index + POLICY['page_lines']]:
            if size + len(line.encode()) > POLICY['page_bytes']:
                break
            size += len(line.encode())
            taken += 1
        if not taken:
            raise ValueError('one public line cannot be retrieved')
        count += 1
        index += taken
    return count


def public(record, rows):
    proteins = record['proteins']
    return {'task.md': old.task(record['sources'][0]['species']).encode(),
            'artifacts/models.gff3': old.gff_bytes(rows),
            'artifacts/proteins.faa': old.faa_bytes(proteins),
            'artifacts/record_counts.json': old.canonical(old.surface(rows, proteins))}


def fits(record, rows):
    visible = public(record, rows)
    return (sum(map(len, visible.values())) <= POLICY['max_visible_bytes'] and
            sum(pages(b) for n, b in visible.items() if n.startswith('artifacts/')) <=
            POLICY['artifact_read_pages_maximum'])


def verify_protocol_lock():
    lock = old.read_json(DIRECTORY / 'PROTOCOL_LOCK.json')
    root = DIRECTORY.parent.parent
    for name, digest in lock['files'].items():
        if old.digest((root / name).read_bytes()) != digest:
            raise ValueError('preconstruction protocol identity changed: ' + name)
    return lock


def extract():
    verify_protocol_lock()
    if (DIRECTORY / 'FROZEN.json').exists():
        raise ValueError('answers frozen; cannot extract')
    receipt = old.read_json(DIRECTORY / 'SOURCE_RECEIPT.json')
    from bench.newsource_validation.intake import verify
    verify(Path(receipt['bundle_path']))  # Cache metadata; no repeat source hash pass.
    grouped = defaultdict(dict)
    for source in receipt['sources']:
        grouped[source['source_group']][source['kind']] = source
    selected = {}
    for accession, mode in ASSIGNMENT:
        sources = [grouped[accession][kind] for kind in ('gff', 'faa')]
        paths = [Path(receipt['bundle_path']) / s['package_path'] for s in sources]
        candidates = old.candidate_blocks(paths[0])
        wanted = {old.attributes(r)['protein_id'] for b in candidates for r in b if r[2] == 'CDS'}
        available = old.protein_subset(paths[1], wanted)
        kept = []
        for block in candidates:
            rows = [r for b in kept + [block] for r in b]
            names = list(dict.fromkeys(old.attributes(r)['protein_id'] for r in rows if r[2] == 'CDS'))
            if any(name not in available for name in names):
                continue
            record = {'rows': rows, 'proteins': {n: available[n] for n in names},
                      'sources': sources, 'mode': mode}
            altered, _ = old.change(rows, record['proteins'], mode)
            if any(old.relations(rows, record['proteins']).values()) or not all(fits(record, r) for r in (rows, altered)):
                continue
            kept.append(block)
            if len(kept) == POLICY['genes_selected']:
                record.update(gene_ids=[old.attributes(b[0])['ID'] for b in kept],
                              candidate_blocks_examined=len(candidates))
                selected[accession] = record
                break
        if accession not in selected:
            raise ValueError('GAP: cannot select two complete connected blocks under fixed policy: ' + accession)
        print('EXTRACTED: ' + accession + '; ' + str(len(rows)) + ' GFF rows', flush=True)
    immutable(DIRECTORY / 'selection/SOURCE_SUBSETS.json', old.canonical(selected))
    return selected


def generate(selected):
    identities = sorted((old.digest(f'{POLICY["seed"]}|{a}|{v}'.encode()), a, v)
                        for a, mode in ASSIGNMENT for v in ('original', 'variant'))
    packets = {}
    for index, (_, accession, variant) in enumerate(identities, 1):
        cid, record = f'qc_{index:03d}', selected[accession]
        proteins, mode = record['proteins'], record['mode']
        before = record['rows']
        altered, detail = old.change(before, proteins, mode)
        is_variant = variant == 'variant'
        rows = altered if is_variant else before
        files = public(record, rows)
        facts = old.relations(rows, proteins)
        pair = 'NSP' + str(1 + [a for a, m in ASSIGNMENT].index(accession))
        if is_variant:
            line = facts[KEYS[mode]][0]
            if mode == 'protein':
                pointers = [f'artifacts/models.gff3:{line}'] + [
                    f'artifacts/proteins.faa:{i}' for i, l in enumerate(files['artifacts/proteins.faa'].decode().splitlines(), 1)
                    if l.startswith('>')]
                statement = 'CDS protein_id 在本题全部 FAA 首 token 中无精确匹配；不允许改用其它标识。'
            else:
                parent_line = 2 if mode == 'parent' else next(i for i, r in enumerate(rows, 2) if r[2] == 'mRNA')
                pointers = [f'artifacts/models.gff3:{line}', f'artifacts/models.gff3:{parent_line}']
                statement = ('mRNA 的 Parent 在完整块中没有对应 gene。' if mode == 'parent' else
                             'CDS 闭区间越过其 mRNA 父区间；长度不变也不能满足包含要求。')
            evidence = [old.evidence(1, statement, list(dict.fromkeys(pointers)))]
            decision = {'verdict': 'block', 'observed_defect': OBSERVED[mode],
                        'root_cause': 'id_mismatch' if mode == 'protein' else 'gff_hierarchy_error'}
        else:
            pointers = [f'artifacts/models.gff3:{i}' for i, r in enumerate(rows, 2) if r[2] == 'CDS']
            pointers += [f'artifacts/proteins.faa:{i}' for i, l in enumerate(files['artifacts/proteins.faa'].decode().splitlines(), 1) if l.startswith('>')]
            evidence = [old.evidence(1, '每个不同 CDS protein_id 与完整 FAA 的首 token 精确接续；逐个 ID 验证，不以行数代替。', pointers),
                        old.evidence(2, '所有 Parent 接续且类型、序列/链与父子闭区间符合题面必要合同。',
                                     [f'artifacts/models.gff3:{i}' for i, r in enumerate(rows, 2) if r[2] in ('gene', 'mRNA')])]
            decision = {'verdict': 'pass', 'observed_defect': 'none', 'root_cause': 'none'}
        sources = [{'path': s['package_path'], 'sha256': s['sha256'], 'source_origin': s['source_path'],
                    'source_group': accession, 'selection': json.dumps({'policy': POLICY,
                    'gene_ids': record['gene_ids'], 'transform': detail if is_variant else 'unmodified source subset'}, ensure_ascii=False, sort_keys=True)}
                   for s in record['sources']]
        meta = {'schema_version': 'newsource-case-1', 'case_id': cid, 'source_group': accession,
                'split': 'sealed_test', 'stage': 'structural_annotation', 'type': 'fault' if is_variant else 'normal',
                'mechanism_family': FAMILIES[mode], 'source_files': sources,
                'injection_script': 'bench/newsource_validation/cases.py', 'seed': POLICY['seed'],
                'synthetic': True, 'pair_id': pair, 'pressure_parent': None,
                'source_exposure': 'new_to_model_prompt_tool_development',
                'mechanism_exposure': 'seen_in_project_development', 'historical_rule_report_seen': True,
                'visible_contract': {'review_target': 'input', 'scope': 'declared_subset',
                    'consumer_contract': '完整Parent层级、同序列/链、闭区间包含、protein_id精确连接FAA首token',
                    'allowed_id_mapping': 'exact only', 'artifact_roles': {
                        'delivery': [n for n in files if n.startswith('artifacts/')], 'reference': []},
                    'usable_previous_result': False}, 'verbatim_tool_exceptions': [],
                'excerpt_policy': '固定规则选两个原始完整编码gene块和所有关联完整蛋白；仅格式重排LF/FAA60列，不代表完整基因组；确定性变体逐字段记录。',
                'review_status': 'draft'}
        expected = {'schema_version': 'newsource-case-1', 'case_id': cid, 'acceptable_decisions': [decision],
                    'root_identifiability': 'confirmed' if is_variant else 'no_defect', 'key_evidence': evidence,
                    'rationale': '仅审核本题声明的文件连接与层级；不推断上游运行原因或生物学质量。',
                    'pair_id': pair, 'independent_review_status': 'pending', 'user_approved': False}
        schema = old.read_json(DIRECTORY / 'schemas/model_output.schema.json')
        singles = [w for k in ('root_cause', 'observed_defect') for w in schema['properties'][k]['enum'] if '_' not in w]
        singles += ['fault', 'bad', 'injected', 'injection', 'truncated']
        for n, kind in (('artifacts/models.gff3', 'gff'), ('artifacts/proteins.faa', 'faa')):
            found = sorted({w for w in singles if re.search(r'(?<![A-Za-z0-9_])' + re.escape(w) + r'(?![A-Za-z0-9_])', files[n].decode(), re.I)})
            if found:
                source = next(s for s in record['sources'] if s['kind'] == kind)
                meta['verbatim_tool_exceptions'].append({'path': n, 'source_sha256': source['sha256'],
                                                       'reason': 'source verbatim tokens only: ' + ', '.join(found)})
        packets[cid] = {**files, 'meta.json': old.canonical(meta), 'expected.json': old.canonical(expected)}
    return packets


def validate(packets, selected):
    validators = {n: Draft202012Validator(old.read_json(DIRECTORY / 'schemas' / f'{n}.schema.json')) for n in ('case_meta', 'expected')}
    regenerated = generate(selected)
    if packets != regenerated:
        raise ValueError('packet bytes differ from deterministic source-backed generation')
    schema = old.read_json(DIRECTORY / 'schemas/model_output.schema.json')
    enums = set(schema['properties']['root_cause']['enum'] + schema['properties']['observed_defect']['enum'])
    strict = [w for w in enums if '_' in w]
    singles = [w for w in enums if '_' not in w] + ['fault', 'bad', 'injected', 'injection', 'truncated']
    pairs, result = defaultdict(list), {}
    if len(packets) != 12:
        raise ValueError('twelve cases required, no silent partial set')
    for cid, files in packets.items():
        meta, gold = (json.loads(files[n]) for n in ('meta.json', 'expected.json'))
        validators['case_meta'].validate(meta)
        validators['expected'].validate(gold)
        if meta['case_id'] != cid or gold['case_id'] != cid or gold['user_approved']:
            raise ValueError('wrong identity or premature approval')
        visible = {n: b for n, b in files.items() if n == 'task.md' or n.startswith('artifacts/')}
        for name, data in visible.items():
            text = name + '\n' + data.decode()
            if b'\r' in data or re.search(r'(?:expected|meta)\.json', text, re.I) or any(w.casefold() in text.casefold() for w in strict):
                raise ValueError('private/enum leakage or non-LF: ' + name)
            found = [w for w in singles if re.search(r'(?<![A-Za-z0-9_])' + re.escape(w) + r'(?![A-Za-z0-9_])', text, re.I)]
            if found and name not in {e['path'] for e in meta['verbatim_tool_exceptions']}:
                raise ValueError('authored trace words: ' + name)
        rows = old.parse_gff(visible['artifacts/models.gff3'].decode())
        proteins = old.fasta_records(visible['artifacts/proteins.faa'].decode())
        if json.loads(visible['artifacts/record_counts.json']) != old.surface(rows, proteins):
            raise ValueError('counts differ')
        facts = old.relations(rows, proteins)
        mode = selected[meta['source_group']]['mode']
        fault = meta['type'] == 'fault'
        if fault:
            if not facts[KEYS[mode]] or any(facts[k] for k in facts if k not in (KEYS[mode], 'extra_protein_ids')):
                raise ValueError('different or extra fault mechanism')
            if mode != 'protein' and facts['extra_protein_ids']:
                raise ValueError('extra protein mismatch')
        elif any(facts.values()):
            raise ValueError('normal subset violates contract')
        if not fits(selected[meta['source_group']], rows):
            raise ValueError('material exceeds byte/retrieval ceiling')
        for evidence in gold['key_evidence']:
            for pointer in evidence['acceptable_pointers']:
                name, loc = pointer.split(':', 1)
                if name not in visible or (loc.isdigit() and not 1 <= int(loc) <= len(visible[name].decode().splitlines())):
                    raise ValueError('missing/private evidence pointer')
                if not loc.isdigit() and (not name.endswith('.json') or loc not in json.loads(visible[name])):
                    raise ValueError('missing evidence field')
        pairs[meta['pair_id']].append(cid)
        result[cid] = {'source_group': meta['source_group'], 'type': meta['type'], 'pair_id': meta['pair_id'],
                       'visible_bytes': sum(map(len, visible.values())), 'artifact_read_pages': sum(pages(b) for n, b in visible.items() if n.startswith('artifacts/')),
                       'decision': gold['acceptable_decisions'][0], 'reference_facts': facts}
    if len(pairs) != 6:
        raise ValueError('six source pairs required')
    for ids in pairs.values():
        if len(ids) != 2 or {result[c]['type'] for c in ids} != {'normal', 'fault'}:
            raise ValueError('incomplete source pair')
        a, b = (packets[c] for c in ids)
        if any(a[n] != b[n] for n in ('task.md', 'artifacts/record_counts.json', 'artifacts/proteins.faa')):
            raise ValueError('paired task or surface differs')
    return result


def build():
    verify_protocol_lock()
    selected = old.read_json(DIRECTORY / 'selection/SOURCE_SUBSETS.json')
    packets = generate(selected)
    result = validate(packets, selected)
    for cid, files in packets.items():
        for name, data in files.items():
            immutable(DIRECTORY / 'cases' / cid / name, data)
    immutable(DIRECTORY / 'CASE_MANIFEST.json', old.canonical({'files': {cid + '/' + n: old.digest(b) for cid, files in packets.items() for n, b in files.items()},
              'answers': 'draft; user not approved', 'api_calls': 0, 'protocol_sha256': old.digest((DIRECTORY / 'PROTOCOL_LOCK.json').read_bytes())}))
    old.write_json(DIRECTORY / 'VALIDATION.json', {'status': 'pass', 'cases': result, 'api_calls': 0,
                   'unresolved': ['user gold confirmation', 'Linux generation parity', 'paid budget protection and authorization']})
    buf = io.StringIO(newline='')
    writer = csv.writer(buf, lineterminator='\n')
    writer.writerow(['case_id', 'source_group', 'type', 'pair_id', 'changed_fields', 'candidate_verdict', 'observed_defect', 'root_cause', 'key_evidence', 'user_comments'])
    for cid, files in packets.items():
        meta, gold = (json.loads(files[n]) for n in ('meta.json', 'expected.json'))
        d = gold['acceptable_decisions'][0]
        writer.writerow([cid, meta['source_group'], meta['type'], meta['pair_id'], json.loads(meta['source_files'][0]['selection'])['transform'], d['verdict'], d['observed_defect'], d['root_cause'], gold['key_evidence'][0]['statement'], ''])
    (DIRECTORY / 'REVIEW_SHEET.csv').write_bytes(buf.getvalue().encode())
    print('PASS: 12 draft cases / 6 pairs; reproducible bytes, schema, leakage, evidence and retrieval checks; 0 API calls')
    return packets


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('extract', 'build'))
    {'extract': extract, 'build': build}[parser.parse_args().action]()
