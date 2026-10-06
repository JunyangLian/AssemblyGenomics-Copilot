# 第一轮来源验收记录

2026-10-06。仅为来源准备与取材审查，不是题库、标准答案或冻结批准；此文件及回传包禁止进入模型输入或 C 知识包。

## 已验收的位置与身份

- 本地回传目录：D:/1_yanjiusheng/GenomeAssembly Copilot/bench/v1_prepare_t1t3_r3/；实际来源包在 bundle/ 下，work/ 不属于来源包。
- 本地一次传输验收回执：[verified.json](v1_prepare_t1t3_r3/verified.json)。服务器状态 complete，34 项来源，0 个必需缺口；46 个 payload 文件、4,166,362 B，控制清单另计。
- MANIFEST.json SHA-256：2f2c567d222273e6a8baa8741ebaba0c9d8a99837d6e2551e8b91de3adeb7e65，与用户服务器汇报相同。
- MANIFEST.sha256 SHA-256：ae46109f1b86a5569d355ffc4a63cc23c4dc027c3ec1abfe75f9a3c64bed5138。
- 只做了本地来源包传输验收；没有重新检查服务器原文件。原文件 SHA 使用服务器记录，子集 SHA 使用已验收清单，两者不得混写。
- 历史清单的 yeast/short_summary.txt 冲突保留并排除，当前 v1 不取用该摘要。

## 真实结果与取材注意事项

| 来源 | 实际核对的内容 | 范围 |
| --- | --- | --- |
| T1 拟南芥终稿 | 27,645 个唯一显式基因 ID；BUSCO C=97.9%、n=2326 | 基因数来自服务器全量 GTF 扫描，不是 1,000 行片段计数 |
| T1 拟南芥事故归档 | 12,637 个唯一显式基因 ID；BUSCO C=76.7%、n=2326 | 原目录 _archive_1002_filteroff，真实事故结果；与终稿组合复现场景时不得伪称原始相邻运行时序 |
| T1 线虫终稿 | 19,156 基因；BUSCO C=98.1%、n=3131；coding validation 无排除 | GTF/GFF 为片段，蛋白只含前 64 条，不能声称片段之间代表完整集合 |
| T1 拟南芥重复注释 | lowercase_pct=16.533；RepeatModeler 2.0.7、RepeatMasker 4.2.2、Dfam 3.9 | QC 与工具版本在实际 provenance 中，足以提供旧库版本注入的真实来源 |
| T1 酵母重复注释 | lowercase_pct=6.333；n_pct=0；序列/长度/ID 一致性为 true；同一套工具版本 | 真实全量 QC 的 6.333% 不能用 200 kb 子集小写比例代替 |
| T1 酵母原读段 | WT_Rep1/2 各 64 对；双端标识相配，两个样本的原始标识和 index 不同 | 有 RNA-seq provenance 和 rnaseq.sha256 来源记录，可用来构造错配 |
| T1 功能注释 | 完整结果 Any=97.99%；子集 1,024 行、1,024 个匹配蛋白，子集 Any=1,012/1,024 | P2 注入须按子集重新算分母和覆盖率，不移用全量 27,645 的统计 |
| T3 | Nakaseomyces bracarensis，GCF_045282275.1，CBM3；真实 GFF/FAA 完整 gzip 文件 | 实际 GFF 头部匹配 accession；原批次报告列 5,179 编码基因/蛋白、in_band；历史判定表只作私有来源核验 |

原 GTF 第一行确为 gene 特征裸 ID，修订后的解析已记录 bare_gene_feature_ID/gene_id_attribute，三份全量基因计数与用户提供的真实数字一致。

拟南芥 DNA 子集只有 NC_003070.9（染色体 1）前 200,000 bp，其中 8,181 bp 小写；其 GFF 片段另含 NC_000932.1 叶绿体。构造 seqid 题前必须先取 NC_003070.9 的完整特征子集，确保注入前名称、范围与 DNA 对得上，不能把现成片段的范围差异直接当作故障。软/硬屏蔽题可直接使用该真实小写区。

## 尚需阶段 2 处理的证据

1. arab_repeat_library_record 未配置，但 arab_repeat_run_record 已有 Dfam 3.9，不需为版本注入再补传库。改动版本说明须保留来源与转换过程，不凭空附加“漏屏蔽率”的统计。
2. arab_prior_configuration 未配置；事故 GTF/BUSCO 已齐全。当前包不证明具体错误命令/参数或原始时序，题目只测试可见的基因损失及回滚判定，不把未知的参数原因写成事实。
3. 酵母 hard_negative 必须结合真实 QC 与物种背景。候选发表依据：Carr M, Bensasson D, Bergman CM (2012), Evolutionary Genomics of Transposable Elements in Saccharomyces cerevisiae, PLOS ONE 7(11):e50978，DOI 10.1371/journal.pone.0050978。[原文](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0050978)，Results → Re-evaluation of TE Content and Copy Number in the S288c Reference Genome 第一段：Ty 来源序列 406,829 bp，占 3.35%。此数值支持酵母 TE 含量低的背景；Ty 占比与本次所有小写屏蔽碱基占比口径不同，不能把它解释成 6.333% 的精确正常区间，也不能创造 1–10% 的发表区间。正式预期判定仍待逐题审核。
4. 原 provenance、QC 内 PASS、项目路径、历史判定与配置注释不能原样全部进入题目。阶段 2 需按固定规则筛选/改名/记录截取，避免答案和注入痕迹泄漏。

暂定 16 题的实际来源均已定位。上述证据边界与片段整理需在构题时落实；本记录不表示 16 道答案已经批准。H1–H3 门槛仍留空；未构造 cases、未生成 expected/FROZEN、未执行 A/B/C。

## 来源目录索引

以下子集路径都相对于已验收 bundle/，来源 ID/原始路径/完整源 SHA/截取方法在 [STATUS.json](v1_prepare_t1t3_r3/bundle/STATUS.json) 中；文件字节 SHA/大小在 [MANIFEST.json](v1_prepare_t1t3_r3/bundle/MANIFEST.json) 中。

| role | cohort | 本地子集 | 大小（B） | 草案题号 |
| --- | --- | --- | ---: | --- |
| arab_repeat_qc | T1_arabidopsis | sources/arab_repeat_qc.json | 494 | 4,5,11 |
| arab_repeat_genome | T1_arabidopsis | sources/arab_repeat_genome.fa | 204056 | 2,3,5,8,11 |
| arab_repeat_run_record | T1_arabidopsis | sources/arab_repeat_run_record.json | 2139 | 4,5,11 |
| arab_final_models | T1_arabidopsis | sources/arab_final_models.gtf | 81293 | 6,15 |
| arab_prior_models | T1_arabidopsis | sources/arab_prior_models.gtf | 95336 | 6,15 |
| arab_final_busco | T1_arabidopsis | sources/arab_final_busco.txt | 703 | 6,15 |
| arab_prior_busco | T1_arabidopsis | sources/arab_prior_busco.txt | 705 | 6,15 |
| arab_final_provenance | T1_arabidopsis | sources/arab_final_provenance.json | 2019 | 6,15 |
| arab_hints | T1_arabidopsis | sources/arab_hints.gff | 62292 | 7 |
| arab_gene_models | T1_arabidopsis | sources/arab_gene_models.gff3 | 106046 | 8 |
| arab_functional_table | T1_arabidopsis | sources/arab_functional_table.tsv | 90097 | 9,10,16 |
| arab_functional_statistics | T1_arabidopsis | sources/arab_functional_statistics.tsv | 416 | 9,10,16 |
| arab_functional_validation | T1_arabidopsis | sources/arab_functional_validation.json | 865 | 9,10,16 |
| arab_query_proteins | T1_arabidopsis | sources/arab_query_proteins.faa | 474822 | 9,10,16 |
| arab_functional_provenance | T1_arabidopsis | sources/arab_functional_provenance.json | 2787 | 9,10,16 |
| yeast_repeat_qc | T1_yeast | sources/yeast_repeat_qc.json | 491 | 14 |
| yeast_repeat_genome | T1_yeast | sources/yeast_repeat_genome.fa | 204076 | 14 |
| yeast_repeat_run_record | T1_yeast | sources/yeast_repeat_run_record.json | 2127 | 14 |
| t3_gff | T3 | sources/t3_gff.gff3.gz | 706994 | 13 |
| t3_proteins | T3 | sources/t3_proteins.faa.gz | 1690895 | 13 |
| celegans_final_models | T1_celegans | sources/celegans_final_models.gtf | 83226 | 12 |
| celegans_final_busco | T1_celegans | sources/celegans_final_busco.txt | 708 | 12 |
| celegans_final_gff | T1_celegans | sources/celegans_final_gff.gff3 | 105817 | 12 |
| celegans_final_proteins | T1_celegans | sources/celegans_final_proteins.faa | 32404 | 12 |
| celegans_coding_validation | T1_celegans | sources/celegans_coding_validation.json | 1174 | 12 |
| celegans_final_provenance | T1_celegans | sources/celegans_final_provenance.json | 2060 | 12 |
| yeast_rnaseq_record | T1_yeast | sources/yeast_rnaseq_record.json | 1896 | 1 |
| yeast_rnaseq_checksums | T1_yeast | sources/yeast_rnaseq_checksums.txt | 328 | 1 |
| yeast_rep1_r1 | T1_yeast | sources/yeast_rep1_r1.fastq | 13374 | 1 |
| yeast_rep1_r2 | T1_yeast | sources/yeast_rep1_r2.fastq | 13372 | 1 |
| yeast_rep2_r1 | T1_yeast | sources/yeast_rep2_r1.fastq | 13358 | 1 |
| yeast_rep2_r2 | T1_yeast | sources/yeast_rep2_r2.fastq | 13350 | 1 |
| t3_report | T3 | sources/t3_report.tsv | 3474 | 13 |
| t3_summary | T3 | sources/t3_summary.json | 2078 | 13 |
