# 十二题候选答案审核

答案尚未确认、冻结或送入模型。本文件和 REVIEW_SHEET.csv 是私有审核材料。

每个来源均提供两个原始完整编码 gene 特征块及所有关联完整蛋白。正常与变体的题面、FAA、字面计数完全一致；仅 GFF 的约定字段变化。所有题都只审核声明子集的连接与层级，不判定整条生信流程或全基因组生物学质量。

| 对 | 物种 | 正常候选 | 变体候选 | 字段变更 | 变体候选根因 |
|---|---|---|---|---|---|
| NSP1 | Syngnathus floridae | qc_008 / pass | qc_006 / block | protein_id XP_088235420.1 → XP_088235420.101 | id_mismatch |
| NSP2 | Saccharomyces kudriavzevii | qc_005 / pass | qc_004 / block | mRNA Parent gene-SKDI_01G0410 → gene-SKDI_01G0410_1 | gff_hierarchy_error |
| NSP3 | Drosophila melanogaster | qc_012 / pass | qc_003 / block | CDS 126626–126630 → 126715–126719，超过父区间 | gff_hierarchy_error |
| NSP4 | Monodelphis domestica | qc_011 / pass | qc_001 / block | protein_id XP_056650550.1 → XP_056650550.101 | id_mismatch |
| NSP5 | Trichinella spiralis | qc_010 / pass | qc_007 / block | mRNA Parent gene-Tsp_07077 → gene-Tsp_07077_1 | gff_hierarchy_error |
| NSP6 | Theobroma cacao | qc_002 / pass | qc_009 / block | CDS 26289–26546 → 27767–28024，超过父区间 | gff_hierarchy_error |

正常候选的 observed_defect/root_cause 均为 none。两道 ID 变体对应 gff_faa_link_missing；两道 Parent 变体对应 gff_reference_unresolved；两道区间变体对应 gff_hierarchy_inconsistent。候选答案只识别可见的文件缺陷，没有捏造其上游历史原因。

请核对：原始蛋白连接是否成立、Parent 是否闭合、父子坐标是否包含，以及候选决定是否符合 task.md 中的消费合同。partial、多转录本和重复的多片段 CDS ID 不单独构成失败。正常题的逐个 protein_id 接续证据列出全部 CDS 行和 FAA header 行，没有仅凭条数判 pass。

REVIEW_SHEET.csv 的 user_comments 可填修改意见。每题的 cases/qc_NNN/expected.json 包含确切定位；meta.json 包含原始路径、SHA 和变更字段。不能把这些私有内容加入模型提示或工具白名单。

程序已核算 schema、字面统计、单一注入机制、引用存在性、泄漏、配对表面一致与再生成一致。作者 AI 起草和程序核算均不算真人盲审；本批也没有完成独立 AI 审核。用户确认与 Linux 复现完成之前保留 draft 状态。

2026-10-11 外部意见指出其未访问实际文件，本项目记录为“摘要逻辑审查”，不登记为12题审核通过。材料已补齐到 [review/answer_review_package.zip](review/answer_review_package.zip)，也可直接上传六份 `review/NSP1.md`–`NSP6.md`。完整CDS连接与直接Parent关系、每个pointer原文及额外支持位置见 [review/RECORD_AUDIT.md](review/RECORD_AUDIT.md) 和逐题JSON/Markdown。正常题E01列全CDS与FAA header，E02原引用是代表性父记录，须结合全部子行才能证明完整层级；补充材料不修改候选答案。
