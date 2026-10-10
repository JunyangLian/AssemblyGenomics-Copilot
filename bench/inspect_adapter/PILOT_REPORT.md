# Inspect 四题真实工具试跑

2026-10-10。真实模型已通过 Inspect 执行只读工具循环，四题最终输出全部违反已冻结的 JSON 输出合同，因此严格计分为 **0/4**。调用与日志链路完成，不等于 QC 任务成功。

## 固定条件与审计身份

- SiliconFlow `deepseek-ai/DeepSeek-V4-Flash`，返回型号与请求完全一致；temperature=0，`enable_thinking=false`，每请求最多 2048 输出 token，每题一次。
- 仅四道已有 development 题；不是新的 held-out 集，也不检验 H1–H3。初始输入只有中性题面、公共文件清单和共同 schema；产物正文由工具读取。答案作为 Scorer target，不进入模型消息或工具白名单。
- 答案经用户“确认答案并批准这次试跑”后冻结。首次代理 TLS 失败另存于 `PILOT_TRANSPORT_REPORT.md`；收到“批准直连续跑，累计预算不增加”后另起恢复身份，没有删除或覆盖原记录。
- 恢复运行 ID：`20261010T094801Z_deepseek-ai_DeepSeek-V4-Flash_33e92693dc16`。冻结 SHA-256：`33e92693dc16ce45c9c67fa8e80f270793512934fea1cf2d7d63036f82020495`。
- 冻结提交 `71e9170` 先于恢复调用；原冻结实现、标准答案、提示、模型与参数不改。无 SDK、Inspect、格式自动重试；没有为补救本次成绩追加调用。

## 实际结果

| 项目 | 计数与比例 |
|---|---:|
| 计划题目 / 保留最终观测 | 4/4（100%） |
| HTTP 200 响应 | 14/14（100%） |
| 样本执行错误 | 0/4（0%） |
| 最终输出解析失败 | 4/4（100%） |
| schema_valid | 0/4（0%） |
| evidence_locator_valid | 0/4（0%） |
| decision_joint | 0/4（0%） |
| 原生工具执行 / 工具错误 | 29 / 0 |

`decision_joint` 要求合法输出中 verdict、observed_defect 和 root_cause 同时符合已冻结答案。输出不合法时三项标签均为零，不能据此声称模型完全无法识别生物学缺陷。证据语义与 action 安全性仍标为 `unadjudicated`，不把定位器或决定匹配当成严格证据支持。

Inspect 日志 status 为 success，表示四个样本的执行与记录完成；上述任务标签另计。运行开始 09:48:06 UTC，结束 09:50:31 UTC，约 145 秒。进程 exit=0；退出清理时 Windows asyncio Proactor 析构报告 `Event loop is closed`，发生在结果已写入后，不是样本错误，记录在 receipt。

## 逐题失败诊断

下表来自原始 completion 的人工阅读（本轮 Codex 的 AI 诊断），**不修改正式解析或评分，不是独立真人复核**。三份有围栏的 JSON 只用于描述模型表述，不提取后计为答对；正常序列题没有完整最终 JSON。

| 题目 | 冻结决定：verdict / defect / root | 原回答及失败点 | 工具调用 |
|---|---|---|---:|
| dev_001 低功能覆盖 | rollback / low_functional_coverage / insufficient_evidence | 解释文字后附围栏 JSON；写出 rollback 和正确缺陷，却将 root 写成 low_annotation_quality。已承认缺数据库、命令和检索日志，仍猜定质量原因。 | 8 |
| dev_002 空 hints 启动前检查 | block / empty_hints / insufficient_evidence | 解释文字后附围栏 JSON；其中决定三元组与冻结答案一致，正式输出仍不合法。需要区分当前文件为空与历史流程是否消费证据。 | 4 |
| dev_003 正常软屏蔽窗口 | pass / none / none | 读取文件后手工按 FASTA 行号数坐标，没有调用 interval_counts；最终 stop_reason=max_tokens，未给出完整决定。 | 6 |
| dev_004 硬屏蔽交付 | rollback / masking_mode_incompatible / masking_mode_error | 解释文字后附围栏 JSON；用 interval_counts 正确找到 115+32+33=180 个 N，但写成 block；证据指针还包含本轮定位器不接受的行范围。 | 11 |

dev_003 是工具选择与完成预算的具体失败：合适的区间计数工具已经提供，但模型没有用它，手工计数中出现坐标疑问，随后耗尽单次输出额度。不能因为 dev_004 使用了该工具，就替 dev_003 自动计算并补写答案。

dev_001 展示“看到异常”与“有证据确定根因”的区别。缺少运行材料时，覆盖率与 ID 接续可以核验，上游机制仍应保持 insufficient_evidence。dev_004 则展示发现问题之后的处置类别也需要单独检查。

## 调用、token 与费用

供应商 HTTP usage 汇总：

| 项目 | 实际数量 |
|---|---:|
| 恢复 HTTP 请求 | 14 |
| prompt_tokens（含缓存） | 70,616 |
| 其中缓存命中 | 12,032 |
| 其中未缓存输入 | 58,584 |
| completion_tokens | 6,488 |
| total_tokens | 77,104 |
| reasoning_tokens | 0 |

Inspect 的 input_tokens=58,584、input_tokens_cache_read=12,032，与 HTTP prompt_tokens=70,616 相符；不要把缓存漏掉，或在 prompt_tokens 上再次加缓存。正文里出现分析文字，不改变平台 reasoning_tokens=0 的记录。

按冻结时记录的高时段输入 ¥3、缓存 ¥0.3、输出 ¥9 / 百万 token，含已报告缓存估算为 **¥0.2377536**；完全不计缓存折扣的参考估算为 ¥0.27024。价格依据：[SiliconFlow 定价](https://www.siliconflow.cn/pricing)，快照日期 2026-10-10。这些是价格参考计算，实际以平台账单为准；第一次无 HTTP 响应的尝试未返回 usage，其收费情况未知。

| 累计预留项目 | 首次失败 | 本次恢复 | 累计 / 原批准上限 |
|---|---:|---:|---:|
| 请求 | 4 | 14 | 18 / 32 |
| 输入代理 token | 9,044 | 71,670 | 80,714 / 200,000 |
| 输出申请 token | 8,192 | 28,672 | 36,864 / 65,536 |

预留代理不是供应商 usage，输出申请也不是实际输出。全部累计检查通过。剩余额度不自动授权再试，冻结方案仍是一次性领取。

## 验证与材料

`python -m pytest -q`：**394 passed in 216.36s**。前次完整回归的 localhost ConnectionResetError 与原样重跑记录保留在 `RECOVERY_VALIDATION.md`。新增提交安全审计通过，运行日志凭证模式扫描无发现。key 仅通过隐藏输入进入本次进程环境，未写入仓库或日志。

`PILOT_RECEIPT.json` 保存实际计数、token、累计额度和私有日志身份 SHA。原始输出、工具轨迹、预算、RESULTS.json 保留在本地忽略目录 `work/pilot/<run_id>/`；Git 不包含这些私有运行日志。首次失败记录也完整保留。

## 学习入口与下一步

用已锁 Inspect 环境打开本次日志：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m inspect_ai view --log-dir bench/inspect_adapter/work/pilot/20261010T094801Z_deepseek-ai_DeepSeek-V4-Flash_33e92693dc16/logs
```

先看 dev_001：初始文件清单 → 模型请求 annotation_counts → 工具重算 32 个 ID 与 6.25% → 模型最终 completion → Scorer 的格式失败。再比较 dev_003 与 dev_004 的工具选择。这样能解释 Dataset、Solver、Tool、Scorer、Log 各自承担哪一步。

下一版本可优先研究供应商支持的结构化输出约束，并离线验证它与原生 tools 的兼容性；同时明确处置类别和证据不足时的根因表达。应另登记新提示/参数与版本，保留本轮失败，经过必要批准再做小规模试验。当前没有修改这些条件，也没有启动下一轮付费调用。

本轮只证明真实模型可进入受限工具循环，并记录了具体失败；四题开发集、单模型、单次重复不能支持泛化、Skill 增益或模型排名结论。工具接口只读公开内存字节，不是任意 shell 或操作系统沙箱。AI 开发审核与诊断不标成真人专家盲审。
