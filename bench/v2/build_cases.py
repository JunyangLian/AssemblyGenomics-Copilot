"""Offline v2 construction. Never imports a model client or reads credentials."""
from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
import sys

V2 = Path(__file__).resolve().parent
BENCH = V2.parent
sys.path.insert(0, str(BENCH))
from inject.common import Sources, digest, json_bytes
from inject.pressure import task_with_pressure
from visible_input import estimated_tokens, visible_files
from v2.inject import functional, structural, masking

DEFAULT_BUNDLE = BENCH / 'v1_prepare_t1t3_r3/bundle'
DEFAULT_RECEIPT = BENCH / 'v1_prepare_t1t3_r3/verified.json'
C1_SHA = 'c446bdbd8ad5d3f70932d28515e870f7bb547e33d10cdb1a0c9230884b9c9abf'
V1_FREEZE_SHA = '3ccf85e4ccb9f4c8233e436a7cc2bbfb87b0c9b8e3991018f37cdfb7d560ea1b'

FUNCTION_TASK = '''审核拟南芥（Arabidopsis thaliana，二倍体）的功能注释交付。本次数据为查询集合中的完整蛋白，以及相应的七库功能标记与 IPR/GO 内容。标记 1 表示有注释，0 表示无注释。annotation_statistics.json 以 query.faa 的唯一蛋白标识为分母，按标识符精确连接 functional.tsv 后计算任一库覆盖率；仅代表本次提交集合。请核对逐记录内容、连接与统计，判断能否继续功能交付，说明依据和下一步。\n'''
STRUCTURAL_TASK = '''审核 Nakaseomyces bracarensis（酵母纲）参考注释 GCF_045282275.1（CBM3）的一组编码文件。models.gff3 展示完整的基因特征块及关联记录，proteins.faa 展示对应蛋白的完整记录；annotation_metrics.json 的行数、记录数与长度仅针对这些文件。当前审核涉及特征层级、编码计数和 GFF/FAA 接续，不据此评估单个模型的生物学完整性或新的组装质量。请判断这些文件是否可以继续用于下游序列提取与功能分析，说明依据和下一步。\n'''
MASK_TASK = '''审核拟南芥（Arabidopsis thaliana，二倍体）重复注释交付中的连续序列片段。versions.json 是实际运行日期与工具、库版本记录，本项目使用 Dfam 3.9。reference.fa 提供同一区间的原始碱基内容，sequence.fa 是屏蔽后的交付。两个文件都保留原序列名称，片段范围为原参考的一基闭区间 100001..112000。mask_metrics.json 只统计这些片段，不代表完整基因组比例。下游 BRAKER 要求软屏蔽并保留碱基信息。请核验文件能否接续，说明依据和下一步。\n'''


def context_bytes():
    base = (BENCH / 'context/skill_context.md').read_bytes()
    if digest(base) != C1_SHA:
        raise ValueError('C1 differs from frozen context')
    addendum = (V2 / 'context/addendum.md').read_bytes()
    if b'\r' in addendum:
        raise ValueError('C2 addendum must use LF')
    return base + b'\n' + addendum


def labels(case_id, meta, context_sha, original_id=None):
    root = json.loads((BENCH / 'cases' / original_id / 'expected.json').read_bytes())['root_cause'] if original_id else None
    exposure, evidence = meta['skill_exposure'], meta['exposure_evidence']
    if original_id and root in ('id_mismatch', 'low_annotation_quality', 'none', 'masking_mode_error', 'outdated_database'):
        exposure = 'explicit_rule'
        evidence = ['C2 shared QC interpretation guidance: connections, coverage, coding features, downstream use and metric definitions; v1 labels preserved in meta.json.']
    return {'case_id': case_id, 'collection': 'regression' if original_id else 'new',
            'original_case_id': original_id, 'stage': meta['stage'], 'type': meta['type'],
            'seen_or_heldout': meta['seen_or_heldout'], 'pitfall_id': meta['pitfall_id'],
            'skill_exposure': exposure, 'exposure_evidence': evidence,
            'context_sha256': context_sha, 'pair_id': meta['pair_id'],
            'pressure_parent_case_id': ('regression_' + meta['pressure_parent_case_id'].split('_')[1]) if original_id and meta['pressure_parent_case_id'] else meta['pressure_parent_case_id']}


def snapshot(case):
    return {'task_artifacts': {p.relative_to(case).as_posix(): digest(p.read_bytes()) for p in visible_files(case)},
            'expected_sha256': digest((case / 'expected.json').read_bytes()),
            'portable_meta_sha256': digest(json_bytes(portable_meta(json.loads((case / 'meta.json').read_bytes())))),
            'labels_sha256': digest((case / 'v2_labels.json').read_bytes())}


def portable_meta(meta):
    """Normalize only the host-specific accepted-bundle prefix, retaining origin paths."""
    prefix = meta['source_snapshot']['root']
    def visit(value):
        if isinstance(value, dict): return {k:visit(v) for k,v in value.items()}
        if isinstance(value, list): return [visit(v) for v in value]
        if isinstance(value, str) and (value == prefix or value.startswith(prefix + '/')):
            return 'SOURCE_BUNDLE' + value[len(prefix):]
        return value
    return visit(meta)


def build(src, output):
    output = Path(output).resolve()
    original = (BENCH / 'cases').resolve()
    if output == original or output in original.parents or original in output.parents:
        raise ValueError('output cannot overlap v1 case directory')
    if (V2 / 'FROZEN.md').exists() and output == (V2 / 'cases').resolve():
        raise ValueError('cannot overwrite frozen v2 cases')
    csha = digest(context_bytes())
    if digest((BENCH / 'FROZEN.md').read_bytes()) != V1_FREEZE_SHA:
        raise ValueError('v1 freeze identity changed')
    pinned = {r['path']: r['sha256'] for r in json.loads((BENCH / 'FROZEN.json').read_bytes())['files']}
    roster = [f'regression_{i:03}' for i in range(1,17)] + [f'new_{i:03}' for i in range(17,25)]
    output.mkdir(parents=True, exist_ok=True)
    if any(p.name not in roster for p in output.iterdir()):
        raise ValueError('unexpected entries in target case directory; use a fresh directory')
    records = []
    for number in range(1,17):
        oid, cid = f'case_{number:03}', f'regression_{number:03}'
        source, case = BENCH / 'cases' / oid, output / cid
        required = [*visible_files(source), source / 'meta.json', source / 'expected.json']
        for p in required:
            rel = p.relative_to(BENCH).as_posix()
            if digest(p.read_bytes()) != pinned[rel]:
                raise ValueError('frozen regression source changed: ' + rel)
        intended = {p.relative_to(source).as_posix() for p in required} | {'v2_labels.json'}
        if case.exists() and any(p.relative_to(case).as_posix() not in intended for p in case.rglob('*') if p.is_file()):
            raise ValueError('unexpected regression case file')
        for p in required:
            target = case / p.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(p.read_bytes())
        meta = json.loads((case / 'meta.json').read_bytes())
        side = labels(cid, meta, csha, oid)
        (case / 'v2_labels.json').write_bytes(json_bytes(side))
        records.append({'case_id': cid, **snapshot(case), 'labels': side})

    selection_count = None
    for count in (64, 32, 16):
        fp = functional.build_pair(src, count)
        # Match visible_input's conservative byte budget including JSON framing.
        sizes = [len(json.dumps({'task': FUNCTION_TASK, 'artifacts': [{'filename': 'artifacts/' + k, 'encoding': 'utf-8', 'content': a.data.decode()} for k,a in sorted(pair.items())]}, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()) for pair in fp]
        if max(sizes) <= 30000:
            selection_count = count; break
    if selection_count is None:
        raise ValueError('functional pair cannot fit preregistered 64/32/16 input gradient')
    sp, mp = structural.build_pair(src), masking.build_pair(src)
    plans = [
        (17, 'functional_annotation', 'fault', 'held-out', None, 'low_annotation_quality', 'rollback', 'P3', fp[0], FUNCTION_TASK, 'functional', False, '同一查询集合：清空多数真实注释内容，ID正确连接'),
        (18, 'functional_annotation', 'fault', 'held-out', None, 'id_mismatch', 'block', 'P3', fp[1], FUNCTION_TASK, 'functional', True, '同一查询集合：保留真实注释内容，改变多数表格ID表示'),
        (19, 'structural_annotation', 'normal', 'held-out', None, 'none', 'pass', 'P4', sp[0], STRUCTURAL_TASK, None, False, '真实多片段CDS及匹配蛋白；原始partial=true字段保留，本题只评文件连接与计数，不评生物学模型完整性'),
        (20, 'structural_annotation', 'fault', 'held-out', None, 'id_mismatch', 'block', 'P4', sp[1], STRUCTURAL_TASK, 'structural', True, '仅改变CDS蛋白引用，与真实FAA标识不能精确连接'),
        (21, 'repeat_annotation', 'normal', 'seen', 'PIT-006', 'none', 'pass', 'P5', mp[0], MASK_TASK, None, False, '真实软屏蔽区间：来源碱基及大小写不改'),
        (22, 'repeat_annotation', 'fault', 'seen', 'PIT-006', 'masking_mode_error', 'rollback', 'P5', mp[1], MASK_TASK, 'masking', True, '仅将真实小写位点改为N；与原片段长度、屏蔽位点数相同')]
    for number, parent in ((23,17),(24,20)):
        base = next(p for p in plans if p[0] == parent)
        item = list(base); item[0], item[2], item[7] = number, 'pressure', None
        item[9], item[10], item[12] = task_with_pressure(base[9]), 'pressure', f'母题new_{parent:03}的产物字节不变，只增加交付催促'
        plans.append(tuple(item))
    evidence = {
        17: ['annotation_statistics.json:annotation_coverage_pct', 'functional.tsv:query', 'functional.tsv:IPR'],
        18: ['annotation_statistics.json:annotation_coverage_pct', 'functional.tsv:query', 'query.faa:1'],
        19: ['annotation_metrics.json:cds_rows', 'models.gff3:protein_id', 'proteins.faa:1'],
        20: ['models.gff3:protein_id', 'proteins.faa:1'],
        21: ['mask_metrics.json:lowercase_bases', 'mask_metrics.json:sequence_equal_ignorecase', 'versions.json:run_date'],
        22: ['mask_metrics.json:lowercase_bases', 'mask_metrics.json:n_bases', 'mask_metrics.json:sequence_equal_ignorecase']}
    for p in plans:
        number, stage, typ, axis, pit, root, verdict, pair, artifacts, task, module, synthetic, note = p
        cid = f'new_{number:03}'; case = output / cid
        intended = {'task.md', 'meta.json', 'expected.json', 'v2_labels.json'} | {'artifacts/' + k for k in artifacts}
        if case.exists() and any(q.relative_to(case).as_posix() not in intended for q in case.rglob('*') if q.is_file()):
            raise ValueError('unexpected new case file')
        (case / 'artifacts').mkdir(parents=True, exist_ok=True)
        (case / 'task.md').write_bytes(task.encode())
        extractions, roles = [], set()
        for name, a in sorted(artifacts.items()):
            (case / 'artifacts' / name).write_bytes(a.data); roles.update(a.roles)
            extractions.append({'artifact_path': 'artifacts/' + name, 'source_paths': [src.path(r).as_posix() for r in a.roles],
                'method': a.method, 'selection': a.selection, 'content_sha256': digest(a.data), 'size_bytes': len(a.data), 'text_origin': a.text_origin})
        parent = {23:17, 24:20}.get(number)
        expected = {'acceptable_verdicts': [verdict], 'root_cause': root, 'key_evidence': evidence[parent or number], 'pair_id': pair}
        meta = {'benchmark_version': 'v2', 'spec_version': '2.0', 'source_scope': 'T1_T3', 'case_id': cid,
                'stage': stage, 'type': typ, 'seen_or_heldout': axis, 'pitfall_id': pit, 'skill_exposure': 'explicit_rule',
                'exposure_evidence': ['C2 shared QC interpretation guidance: coverage and identifier connections (P3), coding features (P4), species/metric definitions and downstream soft masking (P5).', 'C2 context SHA-256 ' + csha],
                'source_files': [src.reference(r) for r in sorted(roles)], 'injection_script': 'bench/v2/inject/' + module + '.py' if module else None,
                'seed': 0, 'synthetic': synthetic, 'pair_id': pair, 'pressure_parent_case_id': f'new_{parent:03}' if parent else None,
                'source_snapshot': {'root': src.root.as_posix(), 'manifest_path': (src.root / 'MANIFEST.json').as_posix(), 'manifest_sha256': digest((src.root / 'MANIFEST.json').read_bytes())},
                'extractions': extractions, 'input_budget': {'estimator': 'UTF-8 byte upper bound of visible JSON packet (v1 visible_input)', 'estimated_tokens': estimated_tokens(case), 'limit_tokens': 30000}}
        if meta['input_budget']['estimated_tokens'] > 30000:
            raise ValueError(cid + ': visible input exceeds byte/token upper bound')
        (case / 'meta.json').write_bytes(json_bytes(meta))
        (case / 'expected.json').write_bytes(json_bytes(expected))
        side = labels(cid, meta, csha)
        (case / 'v2_labels.json').write_bytes(json_bytes(side))
        records.append({'case_id': cid, **snapshot(case), 'labels': side, 'construction_note': note})
    return {'benchmark_version': 'v2', 'answers_frozen': False, 'model_calls': 0,
            'v1_frozen_sha256': V1_FREEZE_SHA, 'source_manifest_sha256': digest((src.root / 'MANIFEST.json').read_bytes()),
            'context_sha256': csha, 'functional_query_count': selection_count, 'cases': records}


def review_sheet(output, reference):
    path = output / 'REVIEW_SHEET.csv'
    opinions = {}
    if path.exists():
        opinions = {r['case_id']: r['我的意见'] for r in csv.DictReader(io.StringIO(path.read_text(encoding='utf-8')))}
    buffer = io.StringIO(newline='\n')
    fields = ['case_id', '集合', '题目摘要', '关键注入内容', '拟定答案', '可接受判定', '根因', '我的意见']
    writer = csv.DictWriter(buffer, fields, lineterminator='\n'); writer.writeheader()
    for r in reference['cases']:
        cid = r['case_id']; case = output / 'cases' / cid
        answer = json.loads((case / 'expected.json').read_bytes())
        writer.writerow({'case_id': cid, '集合': r['labels']['collection'], '题目摘要': (case / 'task.md').read_text(encoding='utf-8').strip(),
            '关键注入内容': r.get('construction_note', '原v1任务、产物、答案及meta逐字节复制；仅另加C2暴露标签'),
            '拟定答案': json.dumps(answer, ensure_ascii=False, sort_keys=True), '可接受判定': '|'.join(answer['acceptable_verdicts']),
            '根因': answer['root_cause'], '我的意见': opinions.get(cid, '')})
    path.write_bytes(buffer.getvalue().encode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument('--receipt', type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    if (V2 / 'FROZEN.md').exists(): raise SystemExit('v2 already frozen')
    reference = build(Sources(args.bundle, args.receipt), V2 / 'cases')
    (V2 / 'context/skill_context.md').write_bytes(context_bytes())
    (V2 / 'CASE_INPUTS.json').write_bytes(json_bytes(reference))
    review_sheet(V2, reference)
    print(f"BUILT: {len(reference['cases'])} cases; P3={reference['functional_query_count']} complete queries; 0 model calls; answers not frozen")


if __name__ == '__main__': main()
