# 外部审核意见与材料补齐

2026-10-11。用户转来外部AI意见：六对判定逻辑一致，但审阅者没有访问 task.md、expected.json、GFF/FAA 或 REVIEW_SHEET.csv，不建议直接冻结。本项目采纳其身份和证据范围限定，记录为摘要逻辑审查，模型身份未知；不是十二题逐行审核通过。

1. 完成：新增 review_audit.py（独立于构题oracle的标准库逐记录核算）、8项专项测试、review/qc_001–qc_012.json/md、六份 review/NSP1–NSP6.md、RECORD_AUDIT.md、SUMMARY.json、README.md、BLIND_INSTRUCTIONS.md 和两个审核ZIP。题面、完整公开GFF/FAA、候选答案、meta来源、CSV、原始真实子集及引用原文均在有答案包；盲审包只有公开题面/产物和统一schema，不能读到gold/meta/配对表。README及REVIEW_GUIDE补充材料入口。
2. 核算：12份候选组合均得到公开文件事实支持；逐条检查148条CDS精确连接、352条直接Parent引用、140个原候选证据位置。正常题全部关系检查，允许partial、多转录本与一致的多片段CDS重复ID。两个坐标故障直接对照mRNA：qc_003父区间124370–126714、CDS126715–126719；qc_009父区间25281–27766、CDS27767–28024。同seqid/同链成立、区间包含不成立。
3. 证据呈现不足：10题的原候选代表性定位没有列全证明全量/否定命题所需的位置。正常题E01已列全CDS/FAA header，E02主要引用gene/mRNA；完整关系还需子行。Parent缺失需查看完整ID集合，ID接续故障需查看所有相关CDS及完整FAA集合。逐记录补充材料明确列出额外支持位置，不把单个pointer存在当成语义充分。原expected、公开题目、构题器、评分器和预先锁定协议均未改；如后续实际材料审核要求修订，应另登记版本与复现，不能暗改当前包。
4. 验证：专项8/8通过；两个ZIP重复生成逐字节一致，内部SHA清单、LF与密钥格式扫描通过。完整pytest结果见TEST_RESULT.json。没有原始大文件重扫、模型调用、API预算使用或答案冻结；Linux复现仍待用户回传。
5. 下一步：原审阅AI可读取 answer_review_package.zip，无法打开ZIP则逐份提供NSP1–NSP6.md，必须先确认它能看到文件原文，再逐题保存意见。已经看过候选答案的同一审阅者只能作有答案的复核；新审阅者若用blind_cases_package.zip先保存原稿，之后才可对照候选。无论哪种，都不能记为真人专家盲审。用户确认与Linux复现之前不冻结，不启动付费运行。
