"""Four draft development packets derived exclusively from received T1 sources."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

V3 = Path(__file__).resolve().parents[1]
BENCH = V3.parent
DEFAULT_SOURCES = BENCH / 'v1_prepare_t1t3_r3/bundle/sources'


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def fasta_records(text):
    result = []
    header, seq = None, []
    for line in text.splitlines():
        if line.startswith('>'):
            if header is not None:
                result.append((header, ''.join(seq)))
            header, seq = line[1:], []
        elif line.strip():
            if header is None:
                raise ValueError('sequence before FASTA header')
            seq.append(line.strip())
    if header is not None:
        result.append((header, ''.join(seq)))
    return result


def fasta_bytes(records):
    return ''.join('>' + header + '\n' + '\n'.join(seq[i:i+60] for i in range(0, len(seq), 60)) + '\n'
                   for header, seq in records).encode('utf-8')


def tsv_bytes(fields, rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode('utf-8')


def load_sources(sources_root):
    records = json.loads((V3 / 'development/SOURCE_RECORDS.json').read_text(encoding='utf-8'))['sources']
    content = {}
    for role, record in records.items():
        path = sources_root / record['filename']
        if path.stat().st_size != record['size_bytes']:
            raise ValueError('source size differs from received record: ' + role)
        # Reuse approved source receipt hashes; do not rescan historical originals.
        content[role] = path.read_text(encoding='utf-8')
    return records, content


def evidence(number, statement, pointers, method):
    return {'claim_id': 'E{:02d}'.format(number), 'statement': statement,
            'acceptable_pointers': pointers, 'verification_method': method,
            'required_for_joint': True, 'review_note': '拟定关键事实，待人类独立审核与用户确认。'}


def packet(case_id, task, artifacts, records, roles, selection, contract, stage, kind,
           observed, cause, verdict, facts, rationale, seen=False, synthetic=False, pair=None):
    source_files = []
    for role in roles:
        item = records[role]
        source_files.append({'path': item['path'], 'sha256': item['sha256'],
                             'source_origin': item['source_origin'], 'source_group': 'T1_arabidopsis',
                             'selection': json.dumps({'development_selection': selection,
                                                      'received_selection': item['existing_selection'],
                                                      'original_sha256': item['original_sha256']}, ensure_ascii=False, sort_keys=True)})
    meta = {'schema_version': 'v3-spec-draft-1', 'case_id': case_id,
            'source_group': 'T1_arabidopsis', 'split': 'development', 'stage': stage, 'type': kind,
            'mechanism_family': {'functional_annotation': 'coverage_observability', 'structural_annotation': 'input_evidence_observability',
                                 'repeat_annotation': 'masking_delivery_role'}[stage],
            'pitfall_exposure': 'seen' if seen else 'held_out', 'pitfall_ids': ['PIT-006'] if seen else [],
            'guidance_exposure': 'unassigned', 'guidance_version_sha256': None,
            'source_files': source_files, 'injection_script': 'bench/v3/inject/build_development.py',
            'seed': 0, 'synthetic': synthetic, 'pair_id': pair, 'pressure_parent': None,
            'visible_contract': contract, 'verbatim_tool_exceptions': [], 'excerpt_policy': selection, 'review_status': 'draft'}
    expected = {'schema_version': 'v3-spec-draft-1', 'case_id': case_id,
                'acceptable_decisions': [{'verdict': verdict, 'observed_defect': observed, 'root_cause': cause}],
                'key_evidence': facts,
                'root_identifiability': 'no_defect' if cause == 'none' else ('insufficient_evidence' if cause == 'insufficient_evidence' else 'confirmed'),
                'rationale': rationale, 'pair_id': pair, 'independent_review_status': 'pending', 'user_approved': False}
    files = {'task.md': task.encode('utf-8'), 'meta.json': json_bytes(meta), 'expected.json': json_bytes(expected)}
    files.update({'artifacts/' + name: value for name, value in artifacts.items()})
    return files


def generate(sources_root=DEFAULT_SOURCES):
    records, content = load_sources(Path(sources_root))
    result = {}
    reader = csv.DictReader(io.StringIO(content['arab_functional_table']), delimiter='\t')
    rows = list(reader)[:32]
    if len(rows) != 32 or len({row['query'] for row in rows}) != 32:
        raise ValueError('required complete query subset unavailable')
    flags = [field for field in reader.fieldnames if field.endswith('-Annotated')]
    proteins = dict((header.split()[0], (header, seq)) for header, seq in fasta_records(content['arab_query_proteins']))
    selected = [proteins[row['query']] for row in rows]
    for row in rows[2:]:
        for flag in flags:
            row[flag] = '0'
        for field in ('IPR', 'GO'):
            row[field] = ''
    annotated = sum(any(row[flag] == '1' for flag in flags) for row in rows)
    if annotated != 2:
        raise ValueError('source does not support declared retained annotation subset')
    metrics = {'query_records': 32, 'annotation_rows': 32, 'matched_ids': 32, 'annotated_records': annotated,
               'coverage_percent': 100 * annotated / 32}
    task = '''# 阶段交付审核

请审核拟南芥（Arabidopsis thaliana）的功能注释交付子集是否可以进入下游结果汇总，输出规定的 JSON。

本题给出的 32 条蛋白构成本次完整审核集合，不能外推全物种基因数。query.faa 的 header 首个 token 必须与 annotation.tsv 的 query 精确相接，不允许去后缀或其它 ID 转换。每条 query 应有且只有一行记录；七个 -Annotated 列任一为 1 即视为有功能标注。本次下游合同要求此集合的标注覆盖率至少为 80%，这是本次交付要求，不是物种通用基线。

当前审核对象是已生成的交付表；没有提供此前已验收版本。本题只提供蛋白、逐条表和从这两者重算的统计，未提供数据库、命令、检索输出或执行日志。请以可见材料区分交付是否合格和能否确认上游原因，并建议最小必要的后续核查。
'''
    result['dev_001'] = packet('dev_001', task, {'query.faa': fasta_bytes(selected), 'annotation.tsv': tsv_bytes(reader.fieldnames, rows),
        'annotation_metrics.json': json_bytes(metrics)}, records, ['arab_functional_table', 'arab_query_proteins'],
        '保留已验收表首32个query及匹配的完整蛋白；保留前2行真实标记，后30行七个标记置0并清空IPR/GO；重算统计。',
        {'review_target': 'completed_delivery', 'scope': 'declared_subset', 'consumer_contract': 'query 精确连接且至少80%具有任一功能标记',
         'allowed_id_mapping': '仅精确匹配，未声明其它映射', 'artifact_roles': {'delivery': ['artifacts/query.faa', 'artifacts/annotation.tsv'], 'reference': []}, 'usable_previous_result': False},
        'functional_annotation', 'uncertainty', 'low_functional_coverage', 'insufficient_evidence', 'rollback',
        [evidence(1, '32条中仅2条有任一标记，覆盖率6.25%，小于题面80%要求。', ['artifacts/annotation_metrics.json:annotated_records','artifacts/annotation_metrics.json:coverage_percent','task.md:5'], 'exact_value'),
         evidence(2, '两文件32个ID精确相接，不支持ID不一致解释。', ['artifacts/annotation_metrics.json:matched_ids','artifacts/annotation.tsv:query','artifacts/query.faa:g1.t1'], 'record_connection'),
         evidence(3, '题面限定未提供执行与检索材料，不能确认上游机制。', ['task.md:7'], 'visible_absence')],
        '交付覆盖不足可确证，应撤回当前表并核查/重建；不能从标记缺失唯一推断低生物学质量、数据库或检索配置错误。')

    task = '''# 阶段输入审核

请审核拟南芥（Arabidopsis thaliana）结构注释准备目录中的 RNA 接续证据是否满足启动条件，输出规定的 JSON。

审核对象是输入准备，不是已经运行的注释结果。本次消费者必须从 hints.gff 读入至少一条 intron 特征才能启动；不允许用未声明的其它证据通道替代。input_metrics.json 是对此处给定文件的字节数和特征行重算，只代表这个输入。

没有提供任何已执行作业、消费日志或已完成模型交付。请判断当前输入能否启动；关于过去的流程是否实际使用 RNA，只能依据本题真正提供的材料作判断。
'''
    result['dev_002'] = packet('dev_002', task, {'hints.gff': b'', 'input_metrics.json': json_bytes({'hints_bytes': 0, 'feature_rows': 0, 'intron_rows': 0})},
        records, ['arab_hints'], '从真实hints子集确定性移除全部特征记录；空文件只模拟当前输入，不制造运行日志。',
        {'review_target': 'input', 'scope': 'declared_subset', 'consumer_contract': '启动前 hints 至少包含一条 intron',
         'allowed_id_mapping': '不涉及ID映射', 'artifact_roles': {'delivery': ['artifacts/hints.gff'], 'reference': []}, 'usable_previous_result': False},
        'structural_annotation', 'uncertainty', 'empty_hints', 'insufficient_evidence', 'block',
        [evidence(1, '给定输入0字节、0条intron，不满足启动条件。', ['artifacts/input_metrics.json:hints_bytes','artifacts/input_metrics.json:intron_rows'], 'exact_value'),
         evidence(2, '这是启动前输入审核，没有消费日志，不能确认历史RNA是否使用。', ['task.md:5','task.md:7'], 'scope_or_role')],
        '阻止启动并补齐/核对证据来源；不能据空输入认定历史注释未使用RNA，也没有依据撤回未提供的完成结果。', synthetic=True)

    seqid, sequence = fasta_records(content['arab_repeat_genome'])[0]
    seqid = seqid.split()[0]
    sequence = sequence[:4096]
    if len(sequence) != 4096:
        raise ValueError('required real genome window unavailable')
    intervals, start = [], None
    for index, char in enumerate(sequence + 'X'):
        if char in 'acgt' and start is None:
            start = index
        if char not in 'acgt' and start is not None:
            intervals.append({'seqid': seqid, 'start': start + 1, 'end': index})
            start = None
    if not intervals:
        raise ValueError('required real lowercase interval unavailable')
    hard = ''.join('N' if char in 'acgt' else char for char in sequence)
    common = {'regions.tsv': tsv_bytes(['seqid', 'start', 'end'], intervals),
              'sequence_metrics.json': json_bytes({'records': 1, 'reference_length': 4096, 'delivery_length': 4096, 'ids_equal': True})}
    task = '''# 阶段交付审核

请审核拟南芥（Arabidopsis thaliana）的序列交付窗口是否满足下游读取要求，输出规定的 JSON。

这里两份 FASTA 都是染色体1起始4096个碱基的窗口；窗口坐标为1..4096，不代表完整染色体或全基因组重复比例。sequence.fa 是当前已生成的交付对象；reference.fa 只用于此窗口的ID和长度定位，不是此前已验收的交付版本。两文件ID/长度应一致，不要求参考文件的大小写或N编码满足交付模式。

regions.tsv 按原序列里的小写acgt连续区间导出，坐标是一基闭区间。本次消费者要求 sequence.fa 在这些区间保留小写acgt及碱基信息，不接受改成N；区间外原有N允许保留。请依据交付文件和区间核查，本题不评价全基因组屏蔽比例、库版本或组装完整性。
'''
    for case_id, delivery, reference, verdict_value, cause_value, observed_value in [
        ('dev_003', sequence, hard, 'pass', 'none', 'none'),
        ('dev_004', hard, sequence, 'rollback', 'masking_mode_error', 'masking_mode_incompatible'),
    ]:
        artifacts = {**common, 'sequence.fa': fasta_bytes([(seqid, delivery)]), 'reference.fa': fasta_bytes([(seqid, reference)])}
        first = intervals[0]
        result[case_id] = packet(case_id, task, artifacts, records, ['arab_repeat_genome'],
            '取真实基因组首记录前4096碱基；导出原小写区间；另一表示仅将acgt小写逐位转N；按题号交换delivery/reference角色。',
            {'review_target': 'completed_delivery', 'scope': 'declared_subset', 'consumer_contract': '同ID/长度窗口；交付在声明区间保留小写acgt',
             'allowed_id_mapping': '仅精确ID，坐标一基闭区间', 'artifact_roles': {'delivery': ['artifacts/sequence.fa'], 'reference': ['artifacts/reference.fa','artifacts/regions.tsv']}, 'usable_previous_result': False},
            'repeat_annotation', 'normal' if verdict_value == 'pass' else 'fault', observed_value, cause_value, verdict_value,
            [evidence(1, '两个窗口ID和长度相同。', ['artifacts/sequence_metrics.json:ids_equal','artifacts/sequence_metrics.json:delivery_length'], 'exact_value'),
             evidence(2, '全部声明区间的交付碱基为{}，首个区间{}..{}可直接核对。'.format('真实小写acgt' if verdict_value == 'pass' else 'N', first['start'], first['end']),
                      ['artifacts/regions.tsv:2','artifacts/sequence.fa:' + seqid], 'record_connection'),
             evidence(3, '消费的是sequence.fa；reference只用于窗口定位。', ['task.md:5','task.md:7'], 'scope_or_role')],
            '只判交付角色：参考为N不导致误报；交付区间变N则违反可见契约，需要撤回并从保留碱基信息的来源重建。',
            seen=True, synthetic=True, pair='D-MASK-01')
    return result


def hashes(packets):
    return {case + '/' + name: hashlib.sha256(data).hexdigest()
            for case, files in sorted(packets.items()) for name, data in sorted(files.items())}


def build(output, sources_root=DEFAULT_SOURCES):
    output = Path(output).resolve()
    if output != (V3/'development/cases').resolve() and not output.is_relative_to((V3/'work').resolve()):
        raise ValueError('output must be development/cases or a child directory within bench/v3/work')
    if (V3/'FROZEN.md').exists():
        raise ValueError('v3 is frozen; draft builder cannot overwrite it')
    packets = generate(sources_root)
    # Preflight every target before any mutation; never overwrite approved drafts.
    for case, files in packets.items():
        old = output/case/'expected.json'
        if old.exists() and json.loads(old.read_text(encoding='utf-8'))['user_approved']:
            raise ValueError('approved answer cannot be overwritten: ' + case)
        for name in files:
            target = output/case/name
            if not target.resolve().is_relative_to(output):
                raise ValueError('output path escapes destination')
    for case, files in packets.items():
        for name, data in files.items():
            target = output/case/name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != data:
                target.write_bytes(data)
    return packets


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-root', type=Path, default=DEFAULT_SOURCES)
    parser.add_argument('--output', type=Path, default=V3/'development/cases')
    args = parser.parse_args()
    packets = build(args.output, args.sources_root)
    print('BUILT: {} draft development cases; 0 API calls; 2 candidate gaps remain.'.format(len(packets)))
