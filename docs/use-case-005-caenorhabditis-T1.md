# 线虫 T1（2026-10-05 段 3 收官：redo 后 BUSCO 98.1%）

## 用例定位

T1 端到端案例 #3：**后生动物 + 100 Mb + 内含子极简模式生物 + nematoda lineage 现成**。
验证维度：与拟南芥对照的动物分支、低内含子物种的参数边界。

## 输入

| 项 | 值 |
|---|---|
| 组装 | WBcel235（C. elegans 参考组装，N2） |
| RNA-seq | ERR10809426（N2，单样本） |
| BUSCO lineage | nematoda_odb10（n=3131） |
| 模式 | BRAKER 3.0.8 ET（use_protein_evidence=false，PIT-008 头行处理后） |

## 段 3 结果

| 配置 | BUSCO_longest | 判定 |
|---|---|---|
| v1：TSEBRA 重跑 intron0.8 + filter，阈值放宽到 90 | 90.1% | 事后判为自伤（PIT-009/010） |
| **v2：braker.gtf 内部合并直连 + filter off，阈值回 95** | **98.1% [S:97.6, D:0.5], M:1.5%** | **过线** |

- 交付物：`Celegans_longest.{gff3,pep.fa,cds.fa}`，**19,156 基因/转录本/蛋白**（真值约 19.7k，Δ≈3%），导出校验 0 排除、序列逐一不变（pep sha256 `e60ef073…`）。
- 证据链与拟南芥完全同构：重跑+filter 掉 → 直连后满血，两物种独立复现 PIT-009/010。

## 教训（沉淀进流程）

1. **阈值校准纪律**：BUSCO 不达标时先归因（是不是流程自伤），再考虑调带——v1 把阈值放宽到 90 是过早放行；redo 后 95 堂堂正正通过。
2. PIT-009：单外显子过滤默认关闭；PIT-010：TSEBRA 重跑默认跳过（`tsebra_rerun=false`）。
3. 驱动命名硬编码（SC288C 残留）在新物种上连环炸了三次（AGAT 名/gffread 名/finalize sha256）——本地驱动已全部参数化（`export_prefix`）。

## 待办

- [x] 段 1 重复注释 / 段 2 RNA 比对 / 段 3 结构注释（2026-10-05 收官）
- [ ] 段 4 功能注释（动物库变体）

## 段 4 结果（2026-10-06，功能注释）

- **Any-Annotated 18,605/19,156 = 97.12%**（advisory 带 [90,100]，通过）
- InterProScan 5.76-107.0（24 线程，5.4 小时）：IPR 蛋白 14,358 / GO 蛋白 10,925
- TrEMBL best 命中 18,287；七类明细待 statistics.tsv 回贴补录
- 五库：NR=animal 子集、KEGG=animal 子集（带配对 id→KO 表）、Swissprot/TrEMBL=Eukaryota、KOG 全集

## T1 结论

线虫 T1 四段闭环：WBcel235 + 单样本 N2 RNA → 段 3 BUSCO 98.1% / 19,156 基因 → 段 4 Any-Annotated 97.12%。
v1 的 90.1% 教训（先归因再调带）已沉淀为 VC-006 候选用例。
