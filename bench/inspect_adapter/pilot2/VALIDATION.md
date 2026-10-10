# Development pilot 2 离线验证

2026-10-10。本文件记录冻结与真实调用之前的离线准备：当时未读取供应商密钥、未调用真实模型，也未生成 APPROVAL/FROZEN。后续授权、冻结和实际结果分别见 APPROVAL/FROZEN 与 REPORT.md，本文件保留原离线校验口径。

## 实际执行

- `python -m pytest -q bench/inspect_adapter/tests/test_structured_pilot.py`：14 passed in 0.79s。验证收集/最终输出上限、参数漂移拒绝、累计预算、异常后的入口恢复、批准门槛先于环境访问、答案逐字节复用、提示变更使模拟冻结失效，以及输入不含私有映射。
- 使用锁定 .venv 执行 `python -m bench.inspect_adapter.structured_pilot --prepare`：生成四题候选、新计划/schema/公开清单和估算，未生成冻结或授权。
- 使用锁定 .venv 执行 `python -m bench.inspect_adapter.tests.structured_transport_smoke`：三项原生 Inspect + OpenAI SDK / httpx2 MockTransport fixture 全通过。它们完全截获 HTTP，不访问外网：

| fixture | 模拟 HTTP 请求 | 实际只读工具 | 结果 |
|---|---:|---:|---|
| normal | 12 | 4 | 每题两轮收集后仅一次 JSON 最终提交，最终请求无 tools |
| round_cap | 24 | 20 | 每题连续五轮工具后仍有第六次最终提交；输出预留精确到 18,432 |
| malformed | 12 | 4 | 格式错误保留并评分失败，无剥围栏/修复/重试/降级 |

合计 48 个模拟 HTTP 请求、28 次实际工具执行，真实网络请求和供应商调用均为 0。fixture 的输出与 usage 都是显式测试数据，target 的可接受决定集合为空，不衡量模型质量；格式正确的 fixture 也不报告为真实 QC 答对。回执摘要见 `OFFLINE_RECEIPT.json`，原生日志位于本地忽略的 `work/pilot2_transport/`。

- 最终 `python -m pytest -q`：**408 passed in 216.02s**。
- 原 pilot 和 pilot_recovery FROZEN 所绑定实现及标准答案 SHA 检查均一致。新版 expected.json 与原用户批准的四份文件逐字节相同；没有扫描原始大来源或修改 v1/v2/v3 的答案。
- 新实现及候选文件 LF 检查通过，凭证模式扫描无发现。既有用户 tar 文件未操作。

## 能证明与尚不能证明的事

已验证：已安装 Inspect 的单步原生生成可以执行工具；五轮后预留最终回合生效；SDK 在收集阶段传 tools、不传 response_format，在最终阶段去掉 tools 并传 JSON object；严格解析和判定规则继续使用旧实现。

尚未验证：SiliconFlow 此型号是否接受并遵守该参数、新提示是否改善工具选择、根因判断或处置，以及实际 token/费用。离线 fixture 不证明这些事项；真实兼容性需要新方案批准后的小规模试跑。若参数拒绝将停止并保留错误，不能静默改实验条件。

提示是根据已观察开发错误进行修改，所有真实数据和答案保持原样；后续结果只能作为开发调试，不作为独立测试、真人盲审或 H1–H3 证据。新预算未启用，旧运行余额也不自动变成新授权。
