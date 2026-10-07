# 阶段3汇报（实现与mock，2026-10-07）

1. 已完成文件：run.py、harness_common.py、model_adapter.py、rule_adapter.py、run_plan.py、models.yaml、RUN_PLAN.json/sha256、mock_report.py、MOCK_RUNS.json、MOCK_REPORT.md/json、make_rules_package.py、server/run_rules.py、import_rules.py、tests/test_harness.py、tests/test_rules_transport.py；README、server/README、CHANGELOG、bench/.gitignore已更新。原仓库scripts/knowledge等行为不变；原冻结122个文件及答案保持一致。

2. pytest：阶段末 `python -m pytest -q`，221 passed，22.18秒（新增28个离线测试）。覆盖解析失败与一次重试、API错误不丢槽位、输入白名单、B/C相同输入、预算/并发守卫、脱敏、服务器运输篡改/重复/身份拒绝。所有HTTP测试均为本地fixture，不用真实key/API。

3. 实际bench运行：288次B/C mock调用，288个模型最终观测，0最终解析失败；另48个A模拟运输观测，parsed=null。原始JSONL本地保存于bench/runs，实际付费调用0、费用¥0。A真实规则尚未在服务器运行；不以模拟A结果计分。计划身份 `e694c6e22811bef07ac8f20c002ff62ad6cf10997cdca34df28744c553954bed`。

4. 预估（非实际usage）：每模型B/C各48初始调用；平均输入代理B 2402.6、C 7716.1 token，知识包使C每次增加约5313.5代理token。每模型初始输入约485,694代理token；三模型共约1,457,082（精确合计见MOCK_REPORT.json）。输出情景每调用1000 token，共288,000；完整上限约236万输出token，含全部解析修复重试约472万。完整预算按UTF-8字节+包装估算输入，不把代理当供应商计费token。价格来源、逐模型输入/输出总量、费用和假设详见MOCK_REPORT。

5. 待用户决定/执行：

- 服务器A：上传rules_package.zip到 ~/AssemblyGenomics-Skill/bench，执行下列命令，scp回传 bench_transfer/v1_rules_run_1/bundle 整目录。无需keys、模型配置或原始大数据。
- API批准：建议保守上限人民币270元、最多576次B/C调用（正常288次）。假设1000输出的情景约¥23.66，初始完整额度¥130.43，全修复完整额度¥261.27；批准前不创建API_APPROVAL、不使用聊天提供的key。
- 阿里云账号业务空间/地域、端点权限、模型别名实际版本和temperature生效值未验证；保持用户指定型号，无静默替换。需要业务空间专属地址时，在真实调用前另登记计划版本，不修改答案。Kimi思考模式与另外两模型不同，报告保留这个边界。
- 观察到REVIEW_SHEET用户意见列再次变为空白，冻结守卫拒绝继续；已确认只有意见列变动，并恢复已批准提交的原字节。原因尚未定位，题目/标准答案未变。正式调用仍先完整核验冻结，任意不一致直接停止。

```bash
cd ~/AssemblyGenomics-Skill/bench
python -m zipfile -e rules_package.zip rules_package
python rules_package/server/run_rules.py
```

本地收到结果后：`python bench/import_rules.py <回传bundle目录>`。阶段3在此等待回传和API批准，未进入计分/报告阶段4，没有检验H1-H3。
