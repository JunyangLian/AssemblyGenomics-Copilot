# 来源验收与候选题构造汇报

2026-10-11。本批尚未冻结答案，没有新测试模型调用。

1. 完成文件：intake.py / SOURCE_RECEIPT.json（一次运输验收）；protocol.py / system.txt / final.txt / schemas/ / PROTOCOL_FIXTURE.json / PROTOCOL_LOCK.json（构题前锁定）；cases.py / selection/SOURCE_SUBSETS.json / cases/qc_001–qc_012 / CASE_MANIFEST.json / VALIDATION.json（确定性构题与校验）；material_audit.py / MATERIAL_AUDIT.json（相同字节和实际分页）；REVIEW_GUIDE.md / REVIEW_SHEET.csv（待用户审核）；server/reproduce_cases.py / package.py / reproduction_package.zip / REPRODUCTION_PACKAGE_RECEIPT.json（最小跨平台复现）。README、协议草案、PLAN与CHANGELOG同步记录当前状态。
2. 完整 `python -m pytest -q`：519 passed，41个来自 Inspect tenacity 参数的第三方弃用警告，283.22秒。新增12项前置测试；schema、泄漏、单一机制、字面计数、配对一致和源码子集再生成校验12/12通过。原生mock仅用旧开发题，共8条观测/32次本地生成，不计模型质量分数。本地解压复现包12/12相同，无API或原始源哈希重扫。
3. 待完成：Linux复现回传、用户确认12份候选答案、正式API预算保护与授权。建议先执行README中的两个服务器命令，并核对REVIEW_GUIDE/CSV；这一步不使用模型。新来源支持固定规则，无缺文件或自动替换来源。付费价格/身份和累计预算仍未知，不能沿用历史额度或开始调用。
4. 边界：六个新于模型/提示/工具开发的T3来源，原始规则统计已见；故障机制已用于项目开发，基础模型预训练暴露未知。正常题仅在选出的完整编码记录子集合同内正常，不等于全基因组质量通过。标准答案由作者AI起草并经程序核算，未完成独立AI/真人盲审。仅两个检索工具比较，不冒称历史五工具完整系统的新成绩。外部BixBench仍只有静态可行性检查，未下载、运行或混入本题集。
