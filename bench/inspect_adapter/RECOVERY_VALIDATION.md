# 连接故障恢复准备验证

2026-10-10。初次已批准运行的原生 Inspect 日志和预算全部保留；报告见 `PILOT_TRANSPORT_REPORT.md`。本文件只记录恢复准备，没有新的真实模型调用。

- `recovery.py` 复用原 Inspect 调用入口，独立绑定新方案目录和自身实现哈希；读取并绑定前次 FROZEN、预算和结果身份，拒绝改写或重置预算。计划扣除 4 / 9044 / 8192 次请求、输入代理和输出申请，剩余为 28 / 190956 / 57344。
- `pilot_recovery/` 包含候选答案、schema、公开文件清单、参数、估算和说明；四题 expected.json 与原已冻结答案逐字节一致，没有新生产 APPROVAL/FROZEN。
- `tests/test_recovery.py` 3 个累计扣减及非法/耗尽预算用例：3 passed in 0.34s。
- 前次日志凭证模式扫描无发现。TLS 探测不带凭证，不发送 HTTP：系统与默认 SSL context 的直连 TLS 均成功。恢复拟只在当前进程设置 api.siliconflow.cn 的 NO_PROXY；保持证书验证。

首次完整回归为 1 failed, 393 passed in 218.91s：既有 `bench/v2/tests/test_v2_review_ui.py` 的 localhost POST 出现一次 ConnectionResetError。没有修改它或旧逻辑；原样专项重跑 1 passed in 0.84s。最终完整回归 `python -m pytest -q`：394 passed in 216.36s，保留上述失败记录。

原方案约定单次领取、失败后重跑另需明确授权，因而这次运输恢复也发出一次确认；累计总预算不增加。确认前不读取 key 或调用模型；候选和离线检查可以先提交。原冻结代码与四题答案不变。

用户已明确回复：**批准直连续跑，累计预算不增加**。先生成本次 APPROVAL/FROZEN 并提交，再启动实际续跑。此记录截至续跑之前，尚无新请求。
