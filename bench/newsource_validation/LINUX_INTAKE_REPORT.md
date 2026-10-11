# Linux 回传验收汇报

2026-10-11。

1. 完成：新增 reproduction_intake.py 和5项专项测试，验收用户回传的 bench/v4/incoming/newsource_validation_cases_r1/bundle；保存 LINUX_REPRODUCTION.json，更新 CURRENT_STATUS.json、PLAN.draft.json、README、REVIEW_GUIDE、CHANGELOG；FREEZE_REQUEST.md 列出待确认的十二份候选决定及每份expected SHA。全部新增/修订仅位于bench。
2. 结果：12题、72个题库文件与Windows原版逐字节一致，73个运输载荷及SHA sidecar清单一致。协议、真实子集、复现包输入身份一致。服务器回执Linux、Python3.9.23、jsonschema4.25.1；运行环境是用户执行回执，不宣称远程主机认证。仅验证相同真实子集生成题目的跨平台一致，不声称重新从完整来源独立提取。没有原始大文件重扫或API调用。
3. 测试：新增专项5/5通过，拒绝篡改/缺失文件、自洽修改的答案、伪造包身份、路径越界、额外文件和sidecar改动。完整 `python -m pytest -q`：532 passed，41个Inspect第三方弃用警告，354.78秒。
4. 待用户决定：是否确认现有12份候选答案并批准冻结。按最初硬约束，外部AI复核与复现通过不自动代表用户授权。当前draft、answer_approval=false、answers_frozen=false；没有FROZEN文件。确认范围仅为答案封存，不包括新API预算/运行；正式模型调用须独立准备累计保护及预算授权。题目、答案/meta、评分器、锁定协议、原评审/复现包字节均未修改。
