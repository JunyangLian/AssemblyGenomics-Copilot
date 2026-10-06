# 拟南芥 T1（2026-09-24 intake；2026-10-05 段 3 收官：BUSCO 97.9%）

## 用例定位

T1 端到端案例 #2：**植物 + 单倍体 + 中等基因组（135 Mb）+ eudicot lineage 现成**。
验证维度：与酵母的物种差（植物 vs 真菌、内含子含量正常 vs 贫乏、基因数 ~27k vs ~6k）。

## 参考基因组与锚点

| 项 | 值 | 来源 |
|---|---|---|
| 组装 | **GCF_000001735.4 TAIR10.1**（NCBI RefSeq） | NCBI FTP（36 MB gz，5 染色体 + MT + CP） |
| 注释 GFF | 同 release `genomic.gff.gz`（21 MB） | NCBI FTP（基因数待下载后实测计数） |
| 蛋白 | 同 release `protein.faa.gz`（11 MB） | 基线锚（数量从 GFF 实测统计） |
| 文件大小 | 36 + 21 + 11 = 68 MB | 总下载 <100 MB |

## RNA-seq（Col-0 野生型对照，study ERP185510）

| run | sample_title | reads | FASTQ 大小 |
|---|---|---|---|
| **ERR15942844** | control-1_S11 | **151M** | 4.47 GB + 4.91 GB |
| **ERR15942845** | control-2_S12 | **67M** | 2.04 GB + 2.26 GB |

- Paired-end ✓ Illumina ✓ Col-0 野生型 ✓
- ENA 直连下载（服务器实测 S3 可达；ENA 需验证）

## BUSCO lineage

`eudicotyledons_odb12.2` — **服务器已有**（/home/user/busco_downloads/lineages/），零下载

## 功能注释库

五库全部按"真菌适配→植物适配"切换（D-017 探测路径不变）：
- NR → `Plants.fa.dmnd`（有！不再用 fungi）
- Swiss-Prot → Eukaryota（含植物）✓
- KEGG → 全库版（含植物）✓
- KOG → 同一 kog_clean ✓
- TrEMBL → Eukaryota ✓

## 基线锚带（intake 预估，GFF 下载后校准）

| 指标 | 锚点参考 | 带子（待实测校准） |
|---|---|---|
| 基因数 | TAIR10 约 27,000-28,000 编码基因 | [24000, 31000] enforce |
| BUSCO | eudicotyledons 预期 >95% | [95, 100] enforce |
| 重复屏蔽 | 拟南芥约 3-5%（低重复物种） | [1, 10] advisory |
| 功能 Any | 模式植物预期 >85% | [75, 100] advisory |

## 需要下载的数据清单

| # | 文件 | 来源 | 大小 |
|---|---|---|---|
| 1 | genomic.fna.gz | NCBI | 36 MB |
| 2 | genomic.gff.gz（锚点 GFF） | NCBI | 21 MB |
| 3 | protein.faa.gz（锚点蛋白） | NCBI | 11 MB |
| 4 | RNA-seq ERR15942844 × 2 FASTQ | ENA | ~9 GB |
| 5 | RNA-seq ERR15942845 × 2 FASTQ | ENA | ~4 GB |
| 6 | BUSCO lineage | 服务器已有 | 0 |
| | **合计** | | **~14 GB** |

## 待办

- [x] 下载数据（实际只用了 ERR15942845（67M reads）单样本；79.88% 比对率）
- [x] 段 1/2/3 已执行（服务器迁移后：Lianjunyang@user，/home/Lianjunyang/env/…）
- [x] 段 3 收官（2026-10-05）
- [ ] 段 4 功能注释

## 段 3 结果（2026-10-05，BRAKER 3.0.8 ET 模式 + BUSCO 6.1.0 eudicots_odb10）

实际 lineage：`eudicots_odb10`（intake 时预估的 eudicotyledons_odb12.2 随服务器迁移作废）。

| 配置 | 基因数 | BUSCO_longest | 判定 |
|---|---|---|---|
| TSEBRA 重跑 intron0.8 + filter（原方案） | 12,637 | 76.7% | fail-fast 拦截 |
| 重跑 intron0.8、filter off | 19,572 | 89.5% | PIT-009 主因 |
| 重跑 intron1.0、filter off | 18,376 | 80.5% | PIT-010：重跑≠内部合并 |
| **内部合并 braker.gtf 直连（定稿）** | **27,645** | **97.9% [S:96.9, D:1.1], M:1.4%** | **过 95 线** |

- 参照：raw braker.gtf 全异构体 BUSCO 98.1%（S:83.1, D:15.0——proteins 模式不折叠异构体，D 虚高；M 1.2% 是真信号）；TAIR10 真值 27,655 编码基因，预测 27,645（Δ=10，0.04%）。
- 交付物：`Athaliana_longest.{gff3,pep.fa,cds.fa}`（27,645 基因/转录本/蛋白，导出校验 0 排除、序列逐一不变，pep sha256 `4a9a2a93…`）。
- 复用教训：PIT-009（单外显子过滤在 ET 模式下连内含子丰富物种都杀）、PIT-010（TSEBRA 重跑≠内部合并，已加 `tsebra_rerun=false` + AGAT 基因数保持校验）、导出器 UTR 白名单。

## 段 4 结果（2026-10-06，功能注释）

- **Any-Annotated 27,089/27,645 = 97.99%**（advisory 带 [75,100]，通过）
- InterProScan 5.76-107.0（24 线程，--disable-precalc，9.2 小时）：IPR 蛋白 23,352 / GO 蛋白 18,495
- 七类明细（27,645 分母）：Nr(Plants) 97.52 / Swissprot 70.33 / KEGG 59.08 / KOG 74.46 /
  TrEMBL 97.15 / Interpro 84.47 / GO 66.90；**Any 97.99**，未注释 556
- validation.json：PASS（all_queries_one_row / denominator_is_total / seven_flags_complete / unannotated_kept 全 true）
- 五库：NR=Plants 子集、Swissprot/TrEMBL=Eukaryota、KEGG=全库、KOG 全集；diamond --very-sensitive 24 线程
- 教训：run_cmd 默认 7200s + IPS 10800s 硬超时会在大库上杀子步（与段 3 BRAKER 7200s 同款）——已全部移除

## T1 结论

拟南芥 T1 四段闭环：组装锚 GCF_000001735.4 + 单样本 RNA → 段 1 软屏蔽（16.5%）→ 段 2 比对（79.88%）→
段 3 BUSCO 97.9% / 27,645 基因 → 段 4 Any-Annotated 97.99%。全链无阈值放宽。
