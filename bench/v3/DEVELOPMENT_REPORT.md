# v3 开发材料阶段汇报

2026-10-09。用户明确选择先构造四题、两题保留证据缺口。本阶段在开发材料审核处停下。

## 1. 文件与完成内容

- inject/build_development.py：固定 seed=0 的确定性来源截取、标记修改、空输入和屏蔽角色构造；来源只读已验收 T1 小包，不读取七个新 T3 原始记录。
- development/SOURCE_RECORDS.json：复用四个已验收来源的路径、来源 SHA、原产物 SHA 和截取记录，没有原始大文件重扫。
- development/cases/dev_001..004：每题 task.md、artifacts、未批准 expected.json、私有 meta.json；四题都属于开发组，轴二待固定 C3 后分配。
- validate_development.py / development/VALIDATION.json / CASE_MANIFEST.json：schema、泄漏、来源绑定、关键证据存在、统计/ID/角色核算及本地逐字节复现。参考计算仅用于构题验证，不增加 A 组规则。
- development/REVIEW_SHEET.csv：私有作者审核表，含构造与拟定答案，用户意见留空。
- development_blind_review.zip、development/blind_review、BLIND_PACKAGE_RECEIPT.json / BLIND_REVIEW_MAP.json：四题随机顺序的独立审题材料、共享 schema、说明和空答案表。仅 zip 可以交审核者，私有映射、答案和注入脚本不在包中。
- development/GAPS.json：两项真实执行证据缺口和用户延后决定；状态/候选/README/CHANGELOG/小文件清单同步登记。

| 开发题 | 可见内容与审核目标 | 私有拟定处置 / 原因 | 可见 UTF-8 字节 |
|---|---|---|---:|
| dev_001 | 32 个真实完整蛋白与逐条表，ID 均相接，2/32 有标记；本次交付要求至少 80% | rollback / insufficient_evidence | 13,806 |
| dev_002 | 启动前 hints 输入，0 字节、0 intron；没有实际消费记录 | block / insufficient_evidence | 739 |
| dev_003 | 同一真实窗口交付保留小写；参考 N 表示只用于 ID/长度定位 | pass / none | 9,389 |
| dev_004 | 相同任务/区间/表面统计，交付与参考表示交换 | rollback / masking_mode_error | 9,389 |

上述表是私有审题说明，不能作为模型输入。覆盖门槛 80% 是明确的本次下游合同，不冒称物种基线；6.25% 来自真实表修改和重算，不是编造统计。软屏蔽正常交付本身来自真实窗口，参考格式构造和空输入均标 synthetic。字节数用于控制小包体积，不当作供应商实际 token 用量；真实 token 在 mock/运行规格阶段另估算。

## 2. pytest 与校验

全仓 `python -m pytest -q`：**347 passed in 219.68s**。新增六项测试检查真实来源草题、错误统计、答案词泄漏、无效证据指针、配对契约漂移及已批准答案的写入保护。

`python bench/v3/validate_development.py --reproduce`：四题通过，本地再生成后的 task/artifacts/expected/meta 哈希全部一致。这是 Windows 本地检查；Linux 复现仍待执行，不称跨平台已通过。盲审 zip 的成员白名单和哈希与回执核对，不含私有答案或来源注入材料。

## 3. 缺口与需要决定的事项

1. 四份拟定答案等待用户逐题审核。建议在 REVIEW_SHEET 的 user_opinion 栏记意见；当前 user_approved 均为 false，没有冻结或模型结果。
2. “低覆盖可确证上游原因”缺真实执行证据；“空 hints 实际进入已完成流程”缺消费绑定记录。用户同意本轮延后，不能从正常 provenance 生成事故日志。最终是否补齐/排除会影响最终题数；28 仍为暂定目标，未自动改为 26。
3. 独立生信审核人未指定。建议只交 development_blind_review.zip，让审核者先独立填写答案与不确定项，再核对拟定答案；用户单人审核则如实标内部审核。
4. 下一阶段在开发审题意见上完善通用 C3/模板，再锁定后构造七来源测试题。Linux 复现、最终 exposure、门槛、全部 expected 用户确认和冻结必须在 mock/真实模型前完成；本阶段不申请 API 或沿用旧预算。

API、mock、A 规则与原分析调用均为 0；未修改 v1/v2 或现有脚本逻辑。标准答案仍是草案，本阶段单独提交后停下。
