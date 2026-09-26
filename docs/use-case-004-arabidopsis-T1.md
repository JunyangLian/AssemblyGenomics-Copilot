# 拟南芥 T1 intake（2026-09-24，待确认后开跑）

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

- [ ] 下载数据（RNA-seq FASTQ 是大头，~13 GB）
- [ ] 下载后跑锚点 GFF 统计（确认基因数 → 写入基线）
- [ ] 落盘 project.yaml + 段 1 SOP → 执行
