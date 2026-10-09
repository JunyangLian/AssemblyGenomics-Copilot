# bench v3：设计与来源隔离阶段

2026-10-09。用户批准的 T3 七类群来源已回传并验收：14 个原始 GFF/FAA gzip 文件，共 116.58 MiB。目前有 48 个本地来源角色、七套未用于 bench 构题的新 T3 配对，18 项私有候选设计。尚无 v3 cases、expected、FROZEN、C3、schema、harness、mock 或 API 记录；本目录设计/审计材料不能成为模型题目输入。

| 文件 | 用途 |
|---|---|
| DESIGN_DRAFT.md | 可答性、来源分组、证据评分、对照/长度方案及后续阶段门 |
| ERROR_TAXONOMY.md / V2_AUDIT_SUMMARY.json / V2_OBSERVATION_AUDIT.csv | 已冻结 v2 错误的开发诊断，未改变 v2 成绩 |
| SOURCE_RECEIPT.json / SOURCE_INTAKE_SUMMARY.md | 七类群真实来源运输验收、格式计数及边界 |
| SOURCE_AUDIT.md / SOURCE_INVENTORY.csv | 48 本地来源角色的位置/大小、SHA 和服务器原路径 |
| T3_CANDIDATES.csv | 27 物种记录、已收到七配对及其它历史可用性边界 |
| SOURCE_SPLIT_PROPOSAL.json / T3_TRANSFER_REQUEST.csv | 七套已收到来源及已完成补传请求；最终角色未冻结 |
| CANDIDATE_REVIEW.csv | 18 项私有候选设计，审核空白，不是已生成题或答案 |
| INDEPENDENT_REVIEW_PROTOCOL.md | 独立人类审题方案；审核人待安排 |
| PHASE1_REPORT.md / PHASE2_REPORT.md / SOURCE_INTAKE_REPORT.md | 历史设计、准备工具与本次真实验收阶段汇报 |
| AUDIT_MANIFEST.json | 本阶段小文档/工具清单，不含 incoming 原始大文件，也不是答案冻结 |

本阶段不改现有 scripts、knowledge、references、schemas、sop、templates 或 v1/v2 冻结内容。只用已验收 T1 三物种与 T3；未下载或重跑原分析。本地完成一次新运输包核验，没有重复扫描其它原始源。

## 当前阶段：来源验收完成，待规格与独立审题

来源包位于 incoming/v3_prepare_t3_r1/bundle（本地保留，不提交大文件）；实际 Linux Python 3.9.23 标准库收集已完成，版本/回执保留在包中。SOURCE_RECEIPT 的运输核验与格式检查不代表正常题 gold，历史 no_band / in_band 矛盾仍不作为答案。

七个 accession 整体拟保留为测试来源，同源变体不得跨开发/测试。下一阶段先确定消费契约、输出 schema、证据评分和 C3 通用指导，冻结相应规格后构造审核材料。最终题数、门槛、标准答案、来源角色和新 API 预算尚未冻结；需独立审题与用户确认。当前阶段停下。
