# 四题 Inspect 开发试跑：SiliconFlow Flash

本次只做一个模型、四道开发题、每题一次的只读工具演示。它验证从模型请求到文件工具、最终 JSON、评分和日志的完整链路，不作为新测试集验证，也不检验 H1–H3。四题来自已构造的拟南芥 T1 小片段；旧 v1/v2 和 v3 原草案不改动。

截至准备完成：真实供应商调用 **0 次**；未读取 API key；未生成本方案的 APPROVAL 或 FROZEN。下表与 `answers/<case_id>/expected.json` 是本次试跑的候选标准答案。用户明确批准后才冻结这些文件的 SHA-256，并执行真实调用。AI 开发盲审四题与草案一致，身份与限制见 `../reviews/`，不是独立真人专家验证。

| 题号 | 公开证据和审核范围 | 拟定 verdict | 观测缺陷 | 可确证根因 |
|---|---|---|---|---|
| dev_001 | 32 条 query 与表中 ID 精确接续，仅 2 条有注释标记，6.25% 低于题面 80% 交付要求；没有上游执行日志 | rollback | low_functional_coverage | insufficient_evidence |
| dev_002 | 输入 hints 为 0 字节、0 条 intron，不满足题面的启动条件；没有已完成流程消费该文件的证据 | block | empty_hints | insufficient_evidence |
| dev_003 | 交付窗口 ID 和长度相符，声明的三个区间共 180 个碱基为小写 acgt；reference 只用于定位 | pass | none | none |
| dev_004 | 与 dev_003 相同的审核范围，交付窗口声明区间的 180 个位置为 N，不满足软屏蔽要求 | rollback | masking_mode_incompatible | masking_mode_error |

第一题不把低覆盖率推断成已确定的生物学质量问题；第二题不把空输入推断成历史 RNA 证据已经被丢弃。第三、四题要求模型分清用于定位的 reference 与实际交付文件。

## 模型和预算

2026-10-10 用户指定改用 **deepseek-ai/DeepSeek-V4-Flash**，OpenAI 兼容接口为 `https://api.siliconflow.cn/v1`。候选方案沿用上轮四题答案和预算；明确批准冻结及调用前不执行。官网接口示例包含该 ID 与原生工具参数；实际运行仍须核对返回身份，不切换模型或模拟工具。

- 单条件 `readonly_tools`，单并发，每题一次，temperature 0，每题最多 8 次生成；显式发送 `enable_thinking: false`。官方说明 max_tokens 不含思考输出，因此本轮用非思考模式约束输出；若返回 usage 报非零 reasoning_tokens，停止后续请求。
- 整次试跑最多 **32 个实际 HTTP 请求**，每个请求最多申请 2,048 个输出 token；总输出申请上限 **65,536 token**。
- 累计输入代理预算上限 **200,000**：按每个完整请求的 UTF-8 字节数 / 3 向上取整，再加 256 估算。它是调度限制，**不是供应商实际 token 或保证的真实 token 上限**。
- 四题初始消息合计代理估算 **4,787 token**，尚不含工具定义、工具返回和后续轮次；实际 token 以供应商返回 usage 为准。此数字不能当作完整试跑费用估计。
- 按 2026-10-10 [官网定价](https://www.siliconflow.cn/pricing)中较高时段的输入 ¥3、输出 ¥9 / 百万 token，不计缓存折扣，按上述输入代理和输出申请额度参考估计约 **¥1.19**。输入代理不是实际 token，因此这不是硬金额保证；实际以供应商 usage 和账单为准。若提前出现 401、403、429，停止后续实际请求；单请求超时 60 秒。
- SDK、Inspect、格式自动重试均为 0。模型返回身份必须为已批准的精确 ID，不接受静默别名或替换。
- 同一冻结版本只允许启动一次。启动后即使失败也保留领取记录；重新运行或续跑需要重新确认范围与累计预算，不能通过重复启动重置额度。

具体参数见 `plan.draft.json`，离线估算见 `ESTIMATE.json`。批准同时覆盖以上一次性调用范围；既往已消耗的评测预算不自动延用。

## 这次如何计分

分别报告合法 JSON/schema、证据指针能定位、verdict + observed_defect + root_cause 三项联合匹配，均保留四题分母；解析或执行失败不剔除。证据指针有效只意味着字段或记录存在，不能说明模型的陈述被证据支持。证据语义与行动安全本次标为 `unadjudicated`，不输出严格成功率或安全率；原始 evidence、action 和安全标记留在日志供逐题复核。

模型初始输入只有通用审核要求、输出 schema、题面和公开文件清单。工具仅访问该题载入内存的 task/artifacts 白名单；没有任意 shell、Python 执行、联网或文件写入，不宣称操作系统沙箱。标准答案只作为 Inspect 的 scorer target。Inspect 分析日志含 target，不能作为下一轮模型输入。

## 怎样运行和学习

在仓库根目录执行。准备与 mock 可离线运行，不需要 key：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r bench/inspect_adapter/requirements-pilot.lock.txt
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.pilot --prepare
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.pilot --mock
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.tests.transport_smoke
```

mock 通过 Inspect 原生循环实际调用 `list_files`，最终只输出 mock 标记，没有 QC 预测。四条不合法 QC 回答必须全部计零，以确认失败保留和评分链路；这个结果不是模型正确率。

`transport_smoke` 再用本地假 HTTP 传输检查真实 SDK 的请求形状与预算拦截，不联网、不读环境凭证；8 次模拟请求、4 次真实文件工具执行仍不是供应商推理或真实 token 用量。

用户明确批准之后，操作者才运行 `--freeze --approval-quote <实际批准原话>`，写入 APPROVAL、FROZEN.json 和包含四个 expected.json 文件 SHA-256 的 FROZEN.md，并先提交冻结记录。随后通过本地环境变量 `SILICONFLOW_API_KEY` 提供 key，再运行 `--api`。key 不写入命令行、仓库或日志，不上传服务器。准备版本没有执行这两步，实际冻结和运行另有记录。

真实运行的 Inspect 日志、请求摘要、完整四题 RESULTS 和预算记录保存在忽略的 `work/pilot/<run_id>/`。不记录请求头；若供应商响应正文原样回显 key，在进入 Inspect 日志前只替换该凭证并保留替换后正文身份。

学习时先看一题日志：用户消息 → assistant.tool_calls → tool 返回 → assistant 最终 JSON → scorer 三项标签。框架负责供应商、循环和日志；本项目负责真实题面、有限文件工具、领域判定和证据边界。接口参考 [Inspect providers](https://inspect.aisi.org.uk/providers.html)、[tools](https://inspect.aisi.org.uk/tools.html) 和 [custom scorers](https://inspect.aisi.org.uk/custom-scorers.html)。
