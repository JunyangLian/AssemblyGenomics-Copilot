"""Offline deterministic v1 construction. No model client or API credentials."""
from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
import statistics
from urllib.parse import unquote

from inject.common import (Artifact, Sources, busco_summary, complete_gene_blocks,
                           digest, fasta_bytes, fasta_records, json_bytes,
                           projected_repeat_qc, tool_versions)
from inject import (agp_layout, functional_tables, gene_models, gzip_stream,
                    input_reads, masking, repeat_library, rna_evidence, sequence_names)
from inject.pressure import task_with_pressure
from visible_input import estimated_tokens, visible_files

BENCH = Path(__file__).resolve().parent
DEFAULT_BUNDLE = BENCH / 'v1_prepare_t1t3_r3/bundle'
DEFAULT_RECEIPT = BENCH / 'v1_prepare_t1t3_r3/verified.json'


def attrs(row):
    return dict(piece.split('=', 1) for piece in row.split('\t')[8].split(';') if '=' in piece)


def normal_structural(src, t3=False):
    role = 't3_gff' if t3 else 'celegans_final_gff'
    prole = 't3_proteins' if t3 else 'celegans_final_proteins'
    blocks = complete_gene_blocks(src.text(role), limit=2, full_source=t3)
    protein_ids = set()
    for block in blocks:
        for row in block:
            if row.split('\t')[2] == 'CDS':
                a = attrs(row)
                protein_ids.add(unquote(a['protein_id']) if t3 else a['Parent'])
    proteins = fasta_records(src.text(prole))
    selected = [(ident, seq) for ident, seq in proteins if ident in protein_ids]
    if {ident for ident, _ in selected} != protein_ids:
        raise ValueError('normal GFF excerpt lacks matching complete proteins')
    result = {
        'models.gff3': Artifact(('##gff-version 3\n' + '\n'.join(r for b in blocks for r in b) + '\n').encode(),
            (role,), 'first two complete gene blocks, with original rows and a GFF version directive', 'feature_subset'),
        'proteins.faa': Artifact(fasta_bytes(selected), (prole,), 'complete source proteins linked to the selected GFF CDS IDs', 'fasta_records'),
    }
    if t3:
        rows = [r for r in src.text(role).splitlines() if r and not r.startswith('#')]
        genes = {attrs(r)['ID'] for r in rows if r.split('\t')[2] == 'gene'}
        parent_gene = {attrs(r)['ID']: attrs(r).get('Parent') for r in rows if 'ID' in attrs(r)}
        coding, linked = set(), set()
        for row in rows:
            if row.split('\t')[2] != 'CDS':
                continue
            a = attrs(row); linked.add(unquote(a['protein_id']))
            for parent in a['Parent'].split(','):
                while parent not in genes and parent in parent_gene:
                    parent = parent_gene[parent]
                if parent in genes:
                    coding.add(parent)
        pids = [p[0] for p in proteins]
        metrics = {'gene_loci': len(genes), 'coding_genes': len(coding), 'proteins': len(proteins),
                   'median_protein_length_aa': statistics.median(len(p[1]) for p in proteins),
                   'duplicate_protein_ids': len(pids) - len(set(pids)),
                   'internal_stops': sum(seq.rstrip('*').count('*') for _, seq in proteins),
                   'ambiguous_residues': sum(sum(c not in 'ACDEFGHIKLMNPQRSTVWY*' for c in seq) for _, seq in proteins),
                   'cds_protein_ids_without_sequence': len(linked - set(pids)),
                   'proteins_without_cds_id': len(set(pids) - linked)}
        result['annotation_metrics.json'] = Artifact(json_bytes(metrics), (role, prole),
            'whole received original T3 GFF/FAA recomputation; distinct coding gene ancestors and CDS protein_id joins; no report verdict copied')
    else:
        metric = {'gene_count': src.rows['celegans_final_models']['selection']['full_source_unique_gene_ids'],
                  'busco': busco_summary(src.text('celegans_final_busco'))}
        validation = src.json('celegans_coding_validation')
        metric['coding_validation'] = {
            'coding_genes': validation['coding_gene_ids'], 'coding_transcripts': validation['coding_transcripts'],
            'excluded': validation['excluded_gene_ids'],
            'proteins_unchanged': validation['protein_IDs_and_sequences_unchanged'],
            'cds_unchanged': validation['CDS_IDs_and_sequences_unchanged']}
        result['annotation_metrics.json'] = Artifact(json_bytes(metric),
            ('celegans_final_models', 'celegans_final_busco', 'celegans_coding_validation'),
            'full original gene count and real BUSCO protein result; project real coding closure fields without source status or paths')
    return result


def yeast_normal(src):
    return {
        'mask_metrics.json': Artifact(json_bytes(projected_repeat_qc(src, 'yeast_repeat_qc')),
            ('yeast_repeat_qc',), 'whole-run real repeat QC invariants and percentages; omit status/rules; do not substitute subset percentages'),
        'versions.json': Artifact(json_bytes(tool_versions(src, 'yeast_repeat_run_record')),
            ('yeast_repeat_run_record',), 'actual user run tool and database versions only')}


REPEAT_TASK = '''审核拟南芥（Arabidopsis thaliana，二倍体）的重复注释阶段交付。下游计划使用 BRAKER 的软屏蔽输入；本项目计划采用 Dfam 3.9。请根据 versions.json 中实际使用的版本和 mask_metrics.json 中全基因组的屏蔽统计及一致性检查，判断能否进入下一阶段，并说明依据和下一步。百分比的分母是本次完整基因组碱基数。'''
FUNCTION_TASK = '''审核拟南芥（Arabidopsis thaliana，二倍体）的功能注释阶段交付。本次审核数据是 16 条完整查询蛋白及对应的七库功能标记表，字段值 1 表示有注释，0 表示无注释。annotation_statistics.json 以 query.faa 中的蛋白为分母，通过标识符精确连接 functional.tsv 后计算任一库的覆盖率。请核对逐记录证据与统计，判定本阶段能否继续，并给出依据及下一步。'''
GENE_TASK = '''审核拟南芥（Arabidopsis thaliana，二倍体）结构注释交付。baseline 是同项目保留的比较基准，delivery 是本次提交结果；提交方说明这次进行了 TSEBRA 合并重跑。两个 metrics 文件的基因数来自各自完整 GTF，BUSCO 均使用 proteins 模式及 eudicots_odb10；GTF 只展示各自前两个完整基因供格式核验。请比较结果，判断是否可用于后续功能注释，并说明依据和下一步。'''


# This roster is private. Tasks contain neither case IDs nor expected labels.
PLAN = [
    (1,1,'input','fault','held-out',None,'explicit_rule','pairing_error',['block'],['sample_1.fastq:1','sample_2.fastq:1','read_statistics.json:matching_identifiers_by_position'],
     '审核酿酒酵母（Saccharomyces cerevisiae）RNA-seq 双端输入。sample_1.fastq 与 sample_2.fastq 被提交为同一样本的 R1/R2，各展示前八条完整记录，记录顺序按原文件保留。请核对配对标识和测序记录，判定是否可以开始比对，并说明依据和下一步。','input_reads',True,'两个真实 T1 样本的 R1/R2 交叉选择；未生成读段。'),
    (2,2,'input','fault','held-out',None,'not_exposed','truncated_input',['block'],['integrity.json:read_completed','integrity.json:message'],
     '审核拟南芥参考序列输入。genome.fa.gz 含一个序列片段；integrity.json 是对该文件执行 Python gzip.decompress 的实际读取记录。该记录不是对完整基因组质量的评估。请判断本文件能否用于后续处理，并说明依据和下一步。','gzip_stream',True,'真实序列重新压缩，删除 gzip 尾部；读取异常为实际 Python 输出。'),
    (3,5,'hic','fault','held-out',None,'related_guidance','agp_inconsistent',['block'],['lengths.json:fasta_lengths','layout.agp:1'],
     '审核拟南芥 scaffold 阶段的一段交付。assembly.fa 是对象序列片段，layout.agp 描述其组成；lengths.json 是这两份文件的长度摘要。坐标使用 AGP 的一基闭区间。本审核仅涉及文件一致性，不据此评价全基因组挂载率或互作图质量。请判断能否继续，并说明依据及下一步。','agp_layout',True,'真实 6000 bp 子集构造一条 AGP，object end 改为 6200。'),
    (4,7,'repeat_annotation','fault','seen','PIT-001','explicit_rule','outdated_database',['warn','rollback'],['versions.json:database_version','task.md:1'],REPEAT_TASK,'repeat_library',False,'真实 Dfam 3.9 记录中的版本字段改为 3.0；不捏造受版本影响的屏蔽数值。'),
    (5,8,'repeat_annotation','fault','seen','PIT-006','explicit_rule','masking_mode_error',['rollback'],['mask_metrics.json:replacement_symbol','mask_metrics.json:lowercase_bases'],
     '审核拟南芥重复注释阶段的序列交付。下游 BRAKER 要求软屏蔽并保留原始碱基信息，当前序列已经完成屏蔽处理；sequence.fa 展示一个 6000 bp 片段，mask_metrics.json 的计数仅针对该片段。请判断当前交付是否符合下游要求，并说明依据和下一步。','masking',True,'只将真实小写碱基替换为 N，其余序列保留。'),
    (6,9,'structural_annotation','fault','seen','PIT-010','explicit_rule','gene_loss',['rollback'],['baseline_metrics.json:gene_count','delivery_metrics.json:gene_count','delivery_metrics.json:busco.complete_pct'],GENE_TASK,'gene_models',False,'真实事故 12637/C76.7 与终稿 27645/C97.9；比较场景重构，不声称历史相邻或已确认精确参数根因。'),
    (7,10,'structural_annotation','fault','held-out',None,'related_guidance','evidence_not_used',['rollback'],['run_inputs.json:evidence_mode','run_inputs.json:hints_entries','hints.gff:empty'],
     '审核拟南芥结构注释阶段交付。该轮使用 ET 证据模式，已完成模型生成，并声明 RNA-seq 参与注释。run_inputs.json 列出参与的 RNA 样本数和实际提供的 hints 文件，hints.gff 展示该证据输入。请判断是否可继续交付模型，并说明依据及下一步。','rna_evidence',True,'清空真实非空 hints；ET/RNA 样本数来自真实 provenance，不模拟运行日志。'),
    (8,11,'structural_annotation','fault','held-out',None,'related_guidance','seqid_mismatch',['block'],['reference.fa:1','models.gff3:2','sequence_names.json:common_sequence_names'],
     '审核拟南芥结构注释文件的交付一致性。reference.fa 展示覆盖一个完整基因坐标范围的参考片段，models.gff3 展示该基因及关联记录；原坐标按序列片段起点保留，没有平移。sequence_names.json 为序列名称摘要。请判断能否将这两份文件一起用于序列提取，并说明依据和下一步。','sequence_names',True,'先对齐真实 chr1 完整基因与 FASTA，再仅修改 GFF seqid。'),
    (9,12,'functional_annotation','fault','held-out',None,'related_guidance','low_annotation_quality',['rollback'],['annotation_statistics.json:annotation_coverage_pct','functional.tsv:2','functional.tsv:3'],FUNCTION_TASK,'functional_tables',False,'16 条真实蛋白，保留首条功能标记，其余十五条清零；ID 保持一致。'),
    (10,13,'functional_annotation','fault','held-out',None,'not_exposed','id_mismatch',['block'],['annotation_statistics.json:annotation_coverage_pct','query.faa:1','functional.tsv:3'],FUNCTION_TASK,'functional_tables',True,'相同蛋白与原功能标记；十五条表格 ID .t 改为 |t；精确连接覆盖同为 1/16。'),
    (11,14,'repeat_annotation','normal','seen','PIT-006','explicit_rule','none',['pass'],['mask_metrics.json:lowercase_pct','mask_metrics.json:sequence_equal_ignorecase','versions.json:database_version'],REPEAT_TASK,None,False,'拟南芥真实段 1 正常结果；不用酵母来源。'),
    (12,15,'structural_annotation','normal','seen','PIT-010','explicit_rule','none',['pass'],['annotation_metrics.json:gene_count','annotation_metrics.json:busco.complete_pct','annotation_metrics.json:coding_validation.excluded'],
     '审核线虫（Caenorhabditis elegans，二倍体）结构注释终稿。annotation_metrics.json 汇总完整模型基因数、proteins 模式 nematoda_odb10 的 BUSCO 和编码交付核验；models.gff3 与 proteins.faa 只展示两个完整基因及其蛋白。请判断该阶段是否可以进入功能注释，并说明依据及下一步。',None,False,'线虫 T1 终稿 19156/C98.1，真实编码核验。'),
    (13,16,'structural_annotation','normal','held-out',None,'related_guidance','none',['pass'],['annotation_metrics.json:coding_genes','annotation_metrics.json:cds_protein_ids_without_sequence','annotation_metrics.json:duplicate_protein_ids'],
     '审核 Nakaseomyces bracarensis（酵母纲）参考注释 GCF_045282275.1（CBM3）的 GFF/蛋白交付。annotation_metrics.json 根据完整 GFF 与 FAA 计算；models.gff3 与 proteins.faa 展示两个完整基因及对应蛋白。当前审核针对编码计数、ID 接续和蛋白内容一致性，不评估新的组装。请判断是否可以继续使用，并说明依据及下一步。',None,False,'T3 完整真实 GFF/FAA 对；模型只见计算指标和匹配记录，不见 T3 判定。'),
    (14,18,'repeat_annotation','hard_negative','held-out',None,'related_guidance','none',['pass','warn'],['mask_metrics.json:lowercase_pct','mask_metrics.json:sequence_equal_ignorecase','versions.json:database_version'],
     '审核酿酒酵母（Saccharomyces cerevisiae，S288c 系参考）重复注释阶段交付。该物种基因组紧凑，下游要求保留碱基信息的软屏蔽参考。mask_metrics.json 来自本次完整基因组屏蔽，百分比分母是完整基因组碱基数；versions.json 记录实际工具和库版本。请结合物种背景核对统计与一致性，判断能否进入结构注释，并说明依据及下一步。',None,False,'用户真实运行小写比例 6.333%；论文 Ty 3.35% 仅是背景，不作为全部重复的硬阈值。'),
]

EXPOSURE = {
 'pairing_error': 'SKILL.md intro + hard constraints: constraint 4 explicitly prohibits A_R1+B_R2 and mixed samples.',
 'truncated_input': 'Reviewed every section of shared context: no gzip stream/trailer validation guidance; generic failure-reporting is not a gzip rule.',
 'agp_inconsistent': 'references/qc-and-review-policy.md: coordinate/edit-reference legality is related; no AGP-vs-FASTA length rule.',
 'outdated_database': 'knowledge/pitfalls/01-dfam.yaml: PIT-001 generic database version mechanism.',
 'masking_mode_error': 'knowledge/pitfalls/06-softmask-lowercase.yaml: PIT-006 hard vs soft masking and -xsmall.',
 'gene_loss': 'knowledge/pitfalls/README.md: PIT-010 retained raw-vs-rerun gene-count comparison; no accident numbers.',
 'evidence_not_used': 'SKILL.md introduction mentions RNA evidence not entering annotation; no explicit empty-hints diagnostic retained.',
 'seqid_mismatch': 'knowledge/pitfalls/08-fasta-header-mismatch.yaml: BAM/FASTA names; GFF/FASTA is a related mechanism.',
 'low_annotation_quality': 'SKILL.md introduction mentions sparse functional coverage; no scenario-specific coverage threshold.',
 'id_mismatch': 'Reviewed whole shared context: BAM reference-name guidance exists but no functional query/table ID-join diagnostic; label not_exposed refers to the functional join mechanism.',
 'none': 'knowledge/baselines/README.md dual-layer/advisory policy and all registered taxon bands; inspect retained mechanisms against normal controls.'}


def build(src: Sources, output: Path, context: Path):
    output = output.resolve(); output.mkdir(parents=True, exist_ok=True)
    if (BENCH / 'FROZEN.md').exists() and output == (BENCH / 'cases').resolve():
        raise ValueError('frozen case directory cannot be overwritten')
    context_sha = digest(context.read_bytes())
    records, review, built = [], [], {}
    for item in PLAN:
        num, old, stage, typ, axis, pit, exposure, root, verdicts, evidence, task, module, synthetic, note = item
        case_id = f'case_{num:03d}'
        if num == 4: artifacts = repeat_library.build(src, older=True)
        elif num in (9,10): artifacts = functional_tables.build(src, change_ids=num == 10)
        elif num == 11: artifacts = repeat_library.build(src)
        elif num in (12,13): artifacts = normal_structural(src, t3=num == 13)
        elif num == 14: artifacts = yeast_normal(src)
        else: artifacts = globals()[module].build(src)
        built[case_id] = (item, artifacts, task + '\n')
    for num, parent, old in [(15,6,19),(16,9,20)]:
        item, artifacts, task = built[f'case_{parent:03d}']
        new = list(item); new[0], new[1], new[3], new[11] = num, old, 'pressure', 'pressure'
        new[-1] = f'仅给 case_{parent:03d} task 增加催促语句；artifacts 字节完全相同。'
        built[f'case_{num:03d}'] = (new, artifacts, task_with_pressure(task))
    for case_id, (item, artifacts, task) in sorted(built.items()):
        num, old, stage, typ, axis, pit, exposure, root, verdicts, evidence, _, module, synthetic, note = item
        case = output / case_id; (case / 'artifacts').mkdir(parents=True, exist_ok=True)
        intended = set(artifacts)
        if any(p.name not in intended for p in (case / 'artifacts').iterdir()):
            raise ValueError('existing artifact not in fixed roster; use a fresh output directory')
        (case / 'task.md').write_bytes(task.encode('utf-8'))
        extractions, roles = [], set()
        for name, a in sorted(artifacts.items()):
            (case / 'artifacts' / name).write_bytes(a.data); roles.update(a.roles)
            row = {'artifact_path': 'artifacts/' + name, 'source_paths': [src.path(r).as_posix() for r in a.roles],
                   'method': a.method, 'selection': a.selection, 'content_sha256': digest(a.data),
                   'size_bytes': len(a.data), 'text_origin': a.text_origin}
            if a.verbatim_selection: row['verbatim_selection'] = a.verbatim_selection
            extractions.append(row)
        pair = 'P2' if num in (9,10) else None
        expected = {'acceptable_verdicts': verdicts, 'root_cause': root, 'key_evidence': evidence, 'pair_id': pair}
        meta = {'benchmark_version': 'v1', 'spec_version': '1.2', 'source_scope': 'T1_T3',
                'case_id': case_id, 'legacy_case_number': old, 'stage': stage, 'type': typ,
                'seen_or_heldout': axis, 'pitfall_id': pit, 'skill_exposure': exposure,
                'exposure_evidence': [EXPOSURE[root], 'bench/context/skill_context.md SHA-256 ' + context_sha],
                'source_files': [src.reference(r) for r in sorted(roles)],
                'injection_script': 'bench/inject/' + module + '.py' if module else None,
                'seed': 0, 'synthetic': synthetic, 'pair_id': pair,
                'pressure_parent_case_id': f'case_{6 if num == 15 else 9:03d}' if typ == 'pressure' else None,
                'source_snapshot': {'root': src.root.as_posix(), 'manifest_path': (src.root / 'MANIFEST.json').as_posix(),
                                    'manifest_sha256': digest((src.root / 'MANIFEST.json').read_bytes())},
                'extractions': extractions, 'input_budget': {'estimator': 'visible_packet_utf8_bytes_v1 (conservative upper bound)',
                    'estimated_tokens': estimated_tokens(case), 'limit_tokens': 30000}}
        if num in (6,15): meta['related_pitfall_ids'] = ['PIT-002','PIT-009']
        if num == 8: meta['related_pitfall_ids'] = ['PIT-008']
        if num in (11,12):
            meta['exposure_evidence'][0] = (
                'knowledge/pitfalls/06-softmask-lowercase.yaml PIT-006: softmasking mechanism, checked here by genuine invariance and lowercase fields.' if num == 11 else
                'knowledge/pitfalls/README.md PIT-010: rerun gene loss mechanism; this normal control supplies genuine final count, protein BUSCO and coding closure.')
        if num == 14:
            run = src.json('yeast_repeat_run_record')
            meta['publication_sources'] = [{'citation': 'Carr M, Bensasson D, Bergman CM (2012). Evolutionary Genomics of Transposable Elements in Saccharomyces cerevisiae. PLOS ONE 7(11):e50978.',
                'doi': '10.1371/journal.pone.0050978', 'url': 'https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0050978',
                'locator': 'Results: Re-evaluation of TE Content and Copy Number in the S288c Reference Genome, first paragraph',
                'reported_values': [{'metric': 'recognizable Ty element coverage', 'value': 3.35, 'unit': 'percent',
                    'context': 'S288c reference; 406829 bp recognizable Ty. Not all RepeatModeler/RepeatMasker repeats. Supports compact low-TE background, not an exact normal interval for 6.333%.'}]}]
            meta['own_run'] = {'runner': 'user', 'command': None, 'command_status': 'not_recorded',
                'command_missing_reason': 'Existing T1 provenance records settings, versions and input hashes but not the complete executed command. No rerun or inferred command.',
                'tool_versions': tool_versions(src, 'yeast_repeat_run_record'),
                'input_sha256': [v for k,v in run['inputs'].items() if k.endswith('_sha256')],
                'output_source_paths': [src.path('yeast_repeat_qc').as_posix()],
                'run_record_path': src.path('yeast_repeat_run_record').as_posix(),
                'run_record_sha256': src.rows['yeast_repeat_run_record']['package_sha256']}
        (case / 'expected.json').write_bytes(json_bytes(expected))
        (case / 'meta.json').write_bytes(json_bytes(meta))
        records.append({'case_id': case_id, 'stage': stage, 'type': typ, 'seen_or_heldout': axis,
                        'skill_exposure': exposure, 'pitfall_id': pit, 'pair_id': pair,
                        'expected_sha256': digest(json_bytes(expected)), 'task_artifacts': {
                            p.relative_to(case).as_posix(): digest(p.read_bytes()) for p in visible_files(case)}})
        review.append({'case_id': case_id, '题目摘要': task.strip().split('。')[0], '关键注入内容': note,
            '拟定答案': verdicts[0], '可接受判定': '|'.join(verdicts), '根因': root,
            '关键依据': '|'.join(evidence), '轴一': axis, '轴二': exposure, '陷阱': pit or '', '我的意见': ''})
    return {'version': 'v1-draft', 'source_manifest_sha256': digest((src.root/'MANIFEST.json').read_bytes()),
            'context_sha256': context_sha, 'cases': records}, review


def review_bytes(rows):
    stream = io.StringIO(newline='\n')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument('--receipt', type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument('--output', type=Path, default=BENCH / 'cases')
    parser.add_argument('--context', type=Path, default=BENCH / 'context/skill_context.md')
    parser.add_argument('--inputs', type=Path, default=BENCH / 'CASE_INPUTS.json')
    args = parser.parse_args()
    if (BENCH / 'FROZEN.md').exists():
        raise SystemExit('Use the reproduction validator for frozen cases; do not rebuild official answers.')
    result, review = build(Sources(args.bundle, args.receipt), args.output, args.context)
    args.inputs.write_bytes(json_bytes(result))
    review_path = args.inputs.parent / 'REVIEW_SHEET.csv'
    if not review_path.exists():
        review_path.write_bytes(review_bytes(review))  # Never overwrite human opinions.
    print('Built', len(result['cases']), 'draft cases; no answers frozen and no model calls.')


if __name__ == '__main__': main()
