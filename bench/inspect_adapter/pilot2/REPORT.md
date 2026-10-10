# Inspect 四题试跑 2：格式成功，决定匹配 3/4

2026-10-10。SiliconFlow `deepseek-ai/DeepSeek-V4-Flash` 本次四题均给出合法 JSON，决定三元组（verdict / observed_defect / root_cause）匹配冻结答案 **3/4**。这表明新版客户端和此型号的 JSON object 最终提交方式实际跑通；仍有处置类别与证据引用错误，不能写成“完整可靠率 75%”。

## 本次运行与条件

- 用户对同模型四题、最多 24 次请求、输入代理 200,000、输出申请 18,432 token 的确认问题回复“可以”。冻结提交 `1631de0` 在实际调用之前完成。
- 运行 ID：`20261010T111451Z_deepseek-ai_DeepSeek-V4-Flash_2c90b6d19d15`。FROZEN SHA-256：`2c90b6d19d157bb67c34d10e1883b733cf304b5828996084dd5217847df1fdb6`。
- 每题一次，temperature=0，非思考、无 SDK/Inspect/格式自动重试，直连且保持 TLS 验证。四题答案、schema 和严格评分函数与前次一致。
- 收集阶段最多五轮、每轮 512 输出 token，由模型选择只读工具；最终阶段只安排一次、关闭工具、最多 2048 token，发送 JSON object 参数。
- 初始消息只有公开题面、文件清单和通用规则/schema。私有答案仅用于 Scorer target；工具只能读取当前样本白名单里的内存字节。
- 北京时间 **19:14:55–19:16:46**，约 111 秒。返回型号均与请求一致，供应商记录 reasoning_tokens=0。

## 实际计数

| 指标 | 计数 / 百分比 |
|---|---:|
| 计划题目 / 保留观测 | 4/4（100%） |
| HTTP 200 | 16/16（100%） |
| schema_valid | 4/4（100%） |
| evidence_locator_valid | 4/4（100%） |
| decision_joint | 3/4（75%） |
| 执行错误 / 解析错误 | 0/4（0%） / 0/4（0%） |
| 原生只读工具 / 工具错误 | 25 / 0 |

16 次请求含 **12 次证据收集、4 次唯一最终提交**。每题最终停止原因均为 stop，没有耗尽最终输出额度。Inspect status=success 是执行与日志状态，不代替质量标签。

证据定位器只验证路径、字段/记录/行是否存在；**不验证该位置是否支持 observation**。证据语义和 action 安全性仍为 unadjudicated，本轮没有引入新的严格证据分数，也没有回头改旧分数。

## 逐题决定与工具选择

| 题目 | 冻结决定：verdict / defect / root | 实际决定 | 联合匹配 | 收集轮 / 工具 |
|---|---|---|---:|---:|
| dev_001 低功能覆盖 | rollback / low_functional_coverage / insufficient_evidence | block / low_functional_coverage / insufficient_evidence | 0 | 3 / 6 |
| dev_002 空 hints 启动前检查 | block / empty_hints / insufficient_evidence | 与冻结决定一致 | 1 | 2 / 3 |
| dev_003 正常软屏蔽窗口 | pass / none / none | 与冻结决定一致 | 1 | 4 / 8 |
| dev_004 硬屏蔽交付 | rollback / masking_mode_incompatible / masking_mode_error | 与冻结决定一致 | 1 | 3 / 8 |

低覆盖题现在将根因保留为 insufficient_evidence，没有继续猜定上游质量原因；但题面第 7 行明确当前对象是已生成交付表，模型仍判 block。该交付已经违反 80% 的必要要求，标准答案要求撤回/重建，因此这题联合决定仍失败。原答案不增加 block 选项。

两道序列题都实际调用了 interval_counts，各一次。正常题从前轮手数坐标并耗尽额度，变成本轮完成工具核查后输出 pass。硬屏蔽题发现三段共 180 个 N，并输出 rollback。工具选择的变化可在原生日志核验，不能只凭最终正确标签声称模型调用过工具。

## 证据仍存在的问题

以下是主 Codex 对原始回答与文件的 **AI 定性核对**，不是独立真人复核，也没有改变正式评分：

dev_001 的三条 TSV 引用写错记录位置：

| 模型 pointer 与 observation | 该行实际内容 |
|---|---|
| annotation.tsv:4，称为 g1.t1 且七列均为 1 | g3.t1，七列均为 0 |
| annotation.tsv:5，称为 g2.t1 且七列均为 1 | g4.t1，七列均为 0 |
| annotation.tsv:6，称为 g3.t1 且七列均为 0 | g5.t1，七列均为 0 |

模型已通过工具得到正确记录和统计，仍在最终引用时把记录与行号错配。正确的 g1.t1/g2.t1/g3.t1 位于第 2/3/4 行；这是引用诊断，**不替模型修正输出**。该题 coverage_percent:4 与 matched_ids:5 引用支持的统计正确。单纯数值判对、行号存在，都不足以表示全部证据支持成立。

dev_004 的 action 要求每段 lowercase_acgt > 0 且 N=0。这个复核条件弱于题面要求：区间还可能混有大写碱基；应完整核对区间内每个碱基和信息保留情况。该提示属于 AI 诊断，未把本轮 action 自动改成已通过或危险建议。其余证据也未完成全项语义裁决。

## 用量、费用与预算

| 供应商实际 usage | token |
|---|---:|
| prompt_tokens（含缓存） | 70,831 |
| 缓存命中 / 未缓存输入 | 16,896 / 53,935 |
| completion_tokens | 4,671 |
| total_tokens | 75,502 |

按冻结价格快照（2026-10-10）高时段输入 ¥3、缓存 ¥0.3、输出 ¥9 / 百万 token，含报告缓存的参考费用为 **¥0.2089128**；不计缓存折扣为 ¥0.254532。实际以平台账单为准。价格来源：[SiliconFlow 定价](https://www.siliconflow.cn/pricing)。

| 预留项目 | 本次实际预留 / 批准上限 |
|---|---:|
| 请求 | 16 / 24 |
| 输入代理 | 81,703 / 200,000 |
| 输出申请 | 14,336 / 18,432 |

全部在批准范围内。输入代理和输出申请分别是请求前限制，不是供应商实际 usage；剩余额度不自动授权追加一轮。

## 与前次开发试跑的关系

| 指标 | 前次实际恢复运行 | 本次 |
|---|---:|---:|
| schema_valid | 0/4 | 4/4 |
| decision_joint | 0/4 | 3/4 |
| 原生工具 | 29 | 25 |
| HTTP 请求 | 14 | 16 |
| 供应商 total_tokens | 77,104 | 75,502 |

同四题根据前次错误修改了提示、阶段调度和输出方式。上述是开发诊断对照，多个因素同时变化、没有独立测试来源或多次重复，不能据此归因 JSON 模式单独贡献，也不能声称 Skill 增益、模型排名或 H1–H3 成立。前次格式失败不等于没有领域判断能力；本次 3/4 联合匹配不等于证据和行动整体可靠。

## 验证与学习入口

实现阶段全仓库 `python -m pytest -q`：**408 passed in 216.02s**；之后未改实现，只冻结方案并运行。离线三项原生协议 fixture 通过。旧冻结实现和答案保持一致，日志凭证模式扫描无发现。key 只进入当前进程环境，没有写到仓库、日志或服务器。

进程 exit=0；结果写入后 Windows asyncio Proactor 析构再次报告 Event loop is closed，属于退出清理提示，样本无执行错误。本轮保留该记录，未为处理它改冻结代码。

计数、usage、阶段与原始工件 SHA 见 `RUN_RECEIPT.json`。原始 completion、全部工具消息、RESULTS 与预算保留在本地忽略目录 `work/pilot/<run_id>/`，不覆盖前次日志。

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m inspect_ai view --log-dir bench/inspect_adapter/work/pilot/20261010T111451Z_deepseek-ai_DeepSeek-V4-Flash_2c90b6d19d15/logs
```

学习时先看 dev_003 的 interval_counts 请求与返回，再看最终 JSON、Scorer 和 target；随后看 dev_001 如何“统计正确、引用错误、处置错误”。已经完成 Dataset → Solver → 原生 Tools → JSON 输出 → Scorer → Log 的真实链路。下一步优先完善证据语义核查与复现说明，保留失败案例；本次没有开启新的付费调用。
