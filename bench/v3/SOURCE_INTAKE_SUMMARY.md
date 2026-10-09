# 七类群来源验收摘要

2026-10-09。服务器回传 v3_prepare_t3_r1/bundle，14 原始 gzip 文件、七完整 GFF/FAA 配对，共 122,240,797 B（116.58 MiB）。本地一次运输校验覆盖 34 个清单 payload 文件；来源 SHA 见 SOURCE_RECEIPT.json，未重扫其它历史原源。

| 类群 | 物种 / accession | GFF gene 行 | mRNA 行 | CDS 行 | FAA 蛋白记录 |
|---|---|---:|---:|---:|---:|
| fungi | Arxiozyma heterogenica / GCF_036370985.1 | 5434 | 5205 | 5357 | 5205 |
| nematoda | Strongyloides ratti / GCF_001040885.1 | 12445 | 12445 | 33782 | 12445 |
| insecta | Anopheles gambiae / GCF_943734735.2 | 14803 | 30505 | 206438 | 30505 |
| viridiplantae | Carica papaya / GCF_054855325.1 | 23452 | 33226 | 231299 | 33226 |
| mammalia | Ornithorhynchus anatinus / GCF_004115215.2 | 29634 | 38747 | 504850 | 38747 |
| aves | Gallus gallus / GCF_016699485.2 | 25440 | 68684 | 932726 | 68683 |
| actinopterygii | Zeus faber / GCF_960531495.2 | 20894 | 28185 | 338487 | 28185 |

这些是服务器对真实文件的字面特征行/记录计数，不等同于编码基因数、唯一模型数或正常性标准答案。鸡的 mRNA 行与 FAA 记录差一、木瓜 gene 行与旧报告计数差异都保留原样；不能仅凭汇总计数判故障，后续需按消费契约检查具体记录连接。

Linux 实际执行使用 Python 3.9.23（conda-forge）及标准库 gzip，无外部分析工具。回传脚本 SHA 与批准的 PACKAGE_RECEIPT.json 对应成员一致，配置内容与本地批准配置一致。gzip/格式检查和运输校验不等于生物学 QC 通过；历史 no_band / in_band 冲突仍不可作标准答案。

七来源拟整体保留作测试，同源正常/变体/压力副本不得跨开发与测试。当前未冻结最终来源角色、题数、schema、标准答案、门槛或模型预算；18 项候选仍为私有设计。
