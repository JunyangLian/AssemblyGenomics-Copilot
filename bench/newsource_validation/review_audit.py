"""Private record-by-record review supplement, independent of the case oracle.

Never imported by the solver, group A, scorer or deterministic generator.
Does not modify any candidate answer, public artifact or locked protocol.
"""
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import unquote
import zipfile

DIRECTORY = Path(__file__).resolve().parent


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect_records(gff, faa):
    """Inspect every CDS and every direct Parent, not just cardinality/edited row."""
    rows, ids, headers = [], defaultdict(list), {}
    for line, text in enumerate(gff.splitlines(), 1):
        if not text or text.startswith('#'):
            continue
        cols = text.split('\t')
        if len(cols) != 9:
            raise ValueError('GFF needs nine columns')
        attrs = {}
        for entry in cols[8].split(';'):
            if not entry:
                continue
            key, value = entry.split('=', 1)
            if key in attrs:
                raise ValueError('duplicate GFF attribute')
            attrs[key] = unquote(value)
        start, end = int(cols[3]), int(cols[4])
        if start < 1 or end < start or not attrs.get('ID'):
            raise ValueError('invalid coordinate or absent ID')
        row = {'line': line, 'id': attrs['ID'], 'type': cols[2], 'seqid': cols[0],
               'strand': cols[6], 'interval': [start, end], 'attributes': attrs}
        rows.append(row)
        ids[row['id']].append(row)
    current, sequence = None, []

    def save():
        if current is not None:
            if not sequence:
                raise ValueError('empty FAA record')
            headers[current]['residues'] = len(''.join(sequence))

    for line, text in enumerate(faa.splitlines(), 1):
        if text.startswith('>'):
            save()
            tokens = text[1:].split()
            if not tokens or tokens[0] in headers:
                raise ValueError('empty or duplicate FAA header ID')
            current, sequence = tokens[0], []
            headers[current] = {'line': line, 'header': text, 'id': current}
        elif text.strip():
            if current is None:
                raise ValueError('FAA sequence before header')
            sequence.append(text.strip())
    save()
    if not rows or not headers:
        raise ValueError('no feature or protein records')
    duplicate_issues = []
    for name, group in ids.items():
        if len(group) > 1:
            signatures = {(r['seqid'], r['strand'], r['attributes'].get('Parent'),
                           r['attributes'].get('protein_id')) for r in group}
            if any(r['type'] != 'CDS' for r in group) or len(signatures) != 1:
                duplicate_issues.append({'id': name, 'lines': [r['line'] for r in group]})
    cds, edges, gene_parent_issues = [], [], []
    for row in rows:
        attrs = row['attributes']
        if row['type'] == 'CDS':
            name = attrs.get('protein_id')
            header = headers.get(name)
            cds.append({'gff_line': row['line'], 'cds_id': row['id'], 'protein_id': name,
                        'faa_header_line': header['line'] if header else None,
                        'faa_header': header['header'] if header else None,
                        'exact_match': header is not None})
        if row['type'] == 'gene':
            if attrs.get('Parent'):
                gene_parent_issues.append(row['line'])
            continue
        # Each comma-separated Parent is checked separately.
        for name in attrs.get('Parent', '').split(','):
            parents = ids.get(name, [])
            parent = parents[0] if len(parents) == 1 else None
            expected_type = 'gene' if row['type'] == 'mRNA' else 'mRNA'
            edge = {'child_line': row['line'], 'child_id': row['id'], 'child_type': row['type'],
                    'parent_id': name, 'parent_lines': [r['line'] for r in parents],
                    'parent_line': parent['line'] if parent else None,
                    'parent_type': parent['type'] if parent else None,
                    'child_seqid': row['seqid'], 'parent_seqid': parent['seqid'] if parent else None,
                    'child_strand': row['strand'], 'parent_strand': parent['strand'] if parent else None,
                    'child_interval': row['interval'], 'parent_interval': parent['interval'] if parent else None,
                    'resolved_unique': parent is not None,
                    'type_ok': parent is not None and parent['type'] == expected_type,
                    'seqid_ok': parent is not None and parent['seqid'] == row['seqid'],
                    'strand_ok': parent is not None and parent['strand'] == row['strand'],
                    'contained': parent is not None and parent['interval'][0] <= row['interval'][0]
                                 <= row['interval'][1] <= parent['interval'][1]}
            edge['contract_ok'] = all(edge[k] for k in ('resolved_unique', 'type_ok', 'seqid_ok', 'strand_ok', 'contained'))
            edges.append(edge)
    protein_ids = {r['protein_id'] for r in cds}
    missing = [r['gff_line'] for r in cds if not r['exact_match']]
    unresolved = sorted({e['child_line'] for e in edges if not e['resolved_unique']})
    incompatible = sorted({e['child_line'] for e in edges if e['resolved_unique'] and not e['contract_ok']})
    extra = sorted(set(headers) - protein_ids)
    issues = {'missing_sequence_lines': missing, 'unresolved_parent_lines': unresolved,
              'incompatible_parent_lines': incompatible, 'extra_protein_ids': extra,
              'duplicate_feature_issues': duplicate_issues, 'gene_parent_issues': gene_parent_issues}
    return {'rows': rows, 'faa_headers': list(headers.values()), 'cds_connections': cds,
            'parent_connections': edges, 'issues': issues, 'contract_satisfied': not any(issues.values())}


def check_candidate(facts, expected):
    issues = facts['issues']
    categories = []
    if issues['missing_sequence_lines']:
        categories.append(('gff_faa_link_missing', 'id_mismatch'))
    if issues['unresolved_parent_lines']:
        categories.append(('gff_reference_unresolved', 'gff_hierarchy_error'))
    if issues['incompatible_parent_lines'] or issues['duplicate_feature_issues'] or issues['gene_parent_issues']:
        categories.append(('gff_hierarchy_inconsistent', 'gff_hierarchy_error'))
    if facts['contract_satisfied']:
        inferred = {'verdict': 'pass', 'observed_defect': 'none', 'root_cause': 'none'}
    elif len(categories) == 1:
        observed, root = categories[0]
        inferred = {'verdict': 'block', 'observed_defect': observed, 'root_cause': root}
    else:
        raise ValueError('ambiguous/unsupported fault combination; requires review')
    if inferred not in expected['acceptable_decisions']:
        raise ValueError('file facts disagree with candidate decision')
    return inferred


def pointer_details(files, expected, facts):
    result = []
    for claim in expected['key_evidence']:
        locations = []
        for pointer in claim['acceptable_pointers']:
            name, loc = pointer.split(':', 1)
            if name not in files or name in ('expected.json', 'meta.json'):
                raise ValueError('private/absent evidence file')
            text = files[name].decode('utf-8')
            if loc.isdigit():
                lines = text.splitlines()
                if not 1 <= int(loc) <= len(lines):
                    raise ValueError('evidence pointer line absent')
                resolved = lines[int(loc) - 1]
            elif name.endswith('.json') and loc in json.loads(text):
                resolved = json.loads(text)[loc]
            else:
                raise ValueError('evidence field absent')
            locations.append({'pointer': pointer, 'resolved': resolved})
        support = []
        normal = facts['contract_satisfied']
        if normal and claim['claim_id'] == 'E01':
            support = [f'artifacts/models.gff3:{r["gff_line"]}' for r in facts['cds_connections']]
            support += [f'artifacts/proteins.faa:{r["line"]}' for r in facts['faa_headers']]
        elif normal and claim['claim_id'] == 'E02':
            support = [f'artifacts/models.gff3:{i}' for e in facts['parent_connections']
                       for i in (e['child_line'], e['parent_line'])]
        elif facts['issues']['missing_sequence_lines']:
            support = [f'artifacts/models.gff3:{i}' for i in facts['issues']['missing_sequence_lines']]
            support += [f'artifacts/proteins.faa:{r["line"]}' for r in facts['faa_headers']]
        else:
            for edge in facts['parent_connections']:
                if not edge['contract_ok']:
                    support += [f'artifacts/models.gff3:{edge["child_line"]}']
                    if edge['parent_line']:
                        support += [f'artifacts/models.gff3:{edge["parent_line"]}']
                    else:
                        support += [f'artifacts/models.gff3:{r["line"]}' for r in facts['rows'] if r['type'] == 'gene']
        support = list(dict.fromkeys(support))
        result.append({'claim_id': claim['claim_id'], 'statement': claim['statement'],
                       'existing_pointer_values': locations, 'all_record_support_pointers': support,
                       'supplemental_pointers_not_in_candidate': [p for p in support if p not in claim['acceptable_pointers']],
                       'scope': 'location and full-file facts checked; listed individual lines are not automatic semantic proof'})
    return result


def markdown(cid, files, facts, pointers):
    lines = [f'# {cid} 逐记录材料复核', '',
             '私有审核补充；不是盲审、真人专家审核或模型成绩。候选答案未改、未冻结。', '',
             '## 每条 CDS → FAA 精确连接', '',
             '| GFF 行 | protein_id | FAA header 行 | 精确连接 |', '|---|---|---|---|']
    for row in facts['cds_connections']:
        lines.append(f'| {row["gff_line"]} | {row["protein_id"]} | {row["faa_header_line"]} | {row["exact_match"]} |')
    lines += ['', '## 全部直接 Parent 关系', '',
              '| 子行/类型 | Parent | 父行/类型 | 子区间 | 父区间 | 序列相同 | 链相同 | 合同成立 |',
              '|---|---|---|---|---|---|---|---|']
    for edge in facts['parent_connections']:
        lines.append(f'| {edge["child_line"]}/{edge["child_type"]} | {edge["parent_id"]} | '
                     f'{edge["parent_lines"]}/{edge["parent_type"]} | {edge["child_interval"]} | '
                     f'{edge["parent_interval"]} | {edge["seqid_ok"]} | {edge["strand_ok"]} | {edge["contract_ok"]} |')
    lines += ['', '## 候选引用逐项定位', '']
    for claim in pointers:
        lines += ['### ' + claim['claim_id'], '', claim['statement'], '']
        for pointer in claim['existing_pointer_values']:
            lines += ['- ' + pointer['pointer'], '']
            value = pointer['resolved']
            lines += ['```text', value if isinstance(value, str) else json.dumps(value, ensure_ascii=False), '```', '']
        if claim['supplemental_pointers_not_in_candidate']:
            lines += ['原候选是代表性定位；完成全记录核对还需要以下行。此处补充材料，不修改 expected.json：', '',
                      ', '.join(claim['supplemental_pointers_not_in_candidate']), '']
    lines += ['## 完整公开题目与候选答案', '',
              '以下逐文件原文供复核。代码框行号与文件自身的行号不同，请以原始附件或上面的 pointer 为准。', '']
    for name in ('task.md', 'artifacts/models.gff3', 'artifacts/proteins.faa',
                 'artifacts/record_counts.json', 'expected.json', 'meta.json'):
        lines += ['### ' + name, '', '````text', files[name].decode('utf-8').rstrip('\n'), '````', '']
    return ('\n'.join(lines).rstrip('\n') + '\n').encode('utf-8')


def archive(path, contents):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as stream:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            stream.writestr(info, data)
    path.write_bytes(buffer.getvalue())


def run():
    from bench.newsource_validation.cases import verify_protocol_lock
    verify_protocol_lock()
    reference = json.loads((DIRECTORY / 'CASE_MANIFEST.json').read_bytes())
    packets = defaultdict(dict)
    for path, checksum in reference['files'].items():
        data = (DIRECTORY / 'cases' / path).read_bytes()
        if digest(data) != checksum:
            raise ValueError('case changed since construction: ' + path)
        cid, name = path.split('/', 1)
        packets[cid][name] = data
    output = DIRECTORY / 'review'
    output.mkdir(exist_ok=True)
    full, blind, reports = {}, {}, {}
    for cid, files in sorted(packets.items()):
        facts = inspect_records(files['artifacts/models.gff3'].decode(), files['artifacts/proteins.faa'].decode())
        expected = json.loads(files['expected.json'])
        decision = check_candidate(facts, expected)
        pointers = pointer_details(files, expected, facts)
        report = {'case_id': cid, 'file_facts': facts, 'candidate_combination_supported': decision,
                  'candidate_pointer_review': pointers, 'all_existing_locations_valid': True,
                  'external_review_completed': False, 'human_blind_review_completed': False}
        reports[cid] = report
        md = markdown(cid, files, facts, pointers)
        (output / f'{cid}.md').write_bytes(md)
        (output / f'{cid}.json').write_bytes(canonical(report))
        full[f'review/{cid}.md'] = md
        full[f'review/{cid}.json'] = canonical(report)
        for name, data in files.items():
            full[f'cases/{cid}/{name}'] = data
            if name == 'task.md' or name.startswith('artifacts/'):
                blind[f'cases/{cid}/{name}'] = data
    pairs = defaultdict(list)
    for cid, files in packets.items():
        pairs[json.loads(files['meta.json'])['pair_id']].append(cid)
    for pair, ids in sorted(pairs.items()):
        md = (f'# {pair} 完整配对审核材料\n\n有答案的材料复核；不能作为盲审。两题均需独立读取原文。\n\n').encode()
        md += b'\n\n'.join((output / (cid + '.md')).read_bytes() for cid in sorted(ids))
        md = md.rstrip(b'\n') + b'\n'
        (output / (pair + '.md')).write_bytes(md)
        full['review/' + pair + '.md'] = md
    subset_data = (DIRECTORY / 'selection/SOURCE_SUBSETS.json').read_bytes()
    selected = json.loads(subset_data)
    for accession, source in selected.items():
        full['source_subsets/' + accession + '.json'] = canonical(source)
    for name in ('REVIEW_SHEET.csv', 'REVIEW_GUIDE.md', 'CASE_MANIFEST.json', 'SOURCE_RECEIPT.json', 'PROTOCOL_LOCK.json'):
        full[name] = (DIRECTORY / name).read_bytes()
    full['README.md'] = (DIRECTORY / 'review/README.md').read_bytes()
    blind['REVIEW_INSTRUCTIONS.md'] = (DIRECTORY / 'review/BLIND_INSTRUCTIONS.md').read_bytes()
    blind['model_output.schema.json'] = (DIRECTORY / 'schemas/model_output.schema.json').read_bytes()
    # A full review sees candidate labels; only the second packet permits a blind first pass.
    summary = {'status': 'record_level_audit_complete', 'cases_checked': len(reports),
               'candidate_combinations_supported': len(reports), 'api_calls': 0,
               'cds_rows_checked': sum(len(r['file_facts']['cds_connections']) for r in reports.values()),
               'parent_edges_checked': sum(len(r['file_facts']['parent_connections']) for r in reports.values()),
               'existing_pointer_locations_checked': sum(len(e['existing_pointer_values']) for r in reports.values()
                                                        for e in r['candidate_pointer_review']),
               'new_model_calls': 0, 'answers_frozen': False, 'answers_changed': False,
               'protocol_changed': False, 'independent_ai_blind_review_completed': False,
               'human_blind_review_completed': False,
               'external_summary_review': 'user supplied; summary logic only; reviewer did not access task/GFF/FAA/expected/CSV; model identity unknown',
               'auditor_scope': 'separate stdlib parser, all presented records; not an independent expert',
               'original_large_source_rescans': 0, 'source_subset_sha256': digest(subset_data),
               'case_manifest_sha256': digest((DIRECTORY / 'CASE_MANIFEST.json').read_bytes()),
               'candidate_answer_hashes': {cid: digest(files['expected.json']) for cid, files in packets.items()},
               'cases_with_supplemental_pointer_locations': [cid for cid, r in reports.items()
                     if any(e['supplemental_pointers_not_in_candidate'] for e in r['candidate_pointer_review'])]}
    lines = ['# 十二题逐记录核算结果', '',
             '这是作者的程序核算和材料补充，尚未完成外部逐文件审阅，不能替代用户确认。候选答案与锁定协议未改。', '',
             '| 题号 | CDS行 | 直接Parent引用 | 候选判定与文件事实 | 存在额外支持行 |', '|---|---|---|---|---|']
    for cid, r in reports.items():
        lines.append(f'| {cid} | {len(r["file_facts"]["cds_connections"])} | {len(r["file_facts"]["parent_connections"])} | '
                     f'{r["candidate_combination_supported"]["verdict"]} 一致 | '
                     f'{cid in summary["cases_with_supplemental_pointer_locations"]} |')
    lines += ['', '所有正常题均逐条检查精确蛋白连接及全部直接Parent。两道坐标故障：', '',
              '- qc_003：models.gff3第7行 CDS 126715–126719；直接父mRNA第3行 124370–126714，seqid与链相同，区间不包含。',
              '- qc_009：models.gff3第10行 CDS 27767–28024；直接父mRNA第3行 25281–27766，seqid与链相同，区间不包含。', '',
              '原有pointer全部可定位，但代表性引用不能独自证明全量关系或不存在某ID。10题补充表列出全记录支持位置；'
              '正常题E01原引用已包含全部CDS与FAA header，E02的父记录引用还需与子行结合。未把pointer存在性称为语义审核通过。', '',
              '外部AI此前没有访问实际题目，仅认可摘要逻辑，记录为用户转述的摘要审查，模型身份未知；真人盲审和独立AI盲审仍未完成。', '']
    proof = ('\n'.join(lines).rstrip('\n') + '\n').encode()
    (output / 'RECORD_AUDIT.md').write_bytes(proof)
    full['review/RECORD_AUDIT.md'] = proof
    (output / 'SUMMARY.json').write_bytes(canonical(summary))
    full['review/SUMMARY.json'] = canonical(summary)
    for contents in (full, blind):
        contents['MANIFEST.json'] = canonical({'algorithm': 'sha256', 'files': {n: digest(b) for n, b in sorted(contents.items())}})
    archive(output / 'answer_review_package.zip', full)
    archive(output / 'blind_cases_package.zip', blind)
    (output / 'PACKAGE_RECEIPT.json').write_bytes(canonical({
        name: {'sha256': digest((output / name).read_bytes()), 'bytes': (output / name).stat().st_size}
        for name in ('answer_review_package.zip', 'blind_cases_package.zip')}))
    verify_protocol_lock()
    for cid, files in packets.items():
        if (DIRECTORY / 'cases' / cid / 'expected.json').read_bytes() != files['expected.json']:
            raise ValueError('candidate answer changed during audit')
    print('AUDITED: all CDS/Parent/direct coordinates and pointer values in 12 cases; candidates supported')
    print('Private reviewer packets prepared; original answers/protocol unchanged; no freeze, API or expert review')
    return reports, summary


if __name__ == '__main__':
    run()
