# Inspect development pilot 2：待批准的改进方案

本版本根据第一轮四题失败改进共同提示和提交方式，仍是同四题、同模型、每题一次的开发调试，不能称为独立验证或泛化提升。原 pilot、pilot_recovery、答案、日志、评分函数和报告保持原样。

## 具体改动

1. 收集证据：最多五轮，每轮 512 输出 token，原生 tools + tool_choice auto；优先用精确计数/ID 接续/区间计数工具，避免按 FASTA 展示行号推算坐标。模型自行选择工具与参数，框架不按题号预先执行工具。
2. 唯一最终提交：关闭工具，最多 2048 输出 token，发送 `response_format: {"type":"json_object"}`。这是提前安排的提交阶段，所有题都执行；不读取 Scorer 或标准答案决定是否追加请求，不是解析失败后修复或重试。
3. 共同提示解释 pass/warn/block/rollback、观察与原因区别、有效单点 pointer，以及未知原因的补证要求。提示不含题号、真实数值、成对映射或答案。改动经过第一轮结果启发，明确登记为开发调优。

JSON object 模式只约束 JSON 语法，字段和枚举仍由原 schema 校验；不声称供应商支持 schema 强约束。供应商文档描述该参数，[接口文档](https://docs.siliconflow.cn/docs/api/chat-completions-post)；已安装 Inspect 0.3.277 的兼容 provider 通过 extra_body 传输它。有关原生生成配置见 [Inspect structured output](https://inspect.aisi.org.uk/structured.html)。当前未向真实端点测试此型号的 JSON 模式；离线 fixture 只能验证客户端传输。若供应商拒绝参数，保留错误、停止新增请求，不自动改参数或降级到旧方式。

## 不变的答案与评分

四份 expected.json 与第一次用户批准并冻结的答案逐字节相同。schema、严格 JSON 解析、证据定位器及 decision_joint 复用旧实现，继续拒绝解释文字、代码围栏和无效定位；不从旧错误回答中抽取 JSON 来改变旧成绩。证据语义和 action 安全性仍为 unadjudicated。

`system.txt`、`final.txt`、实现、方案、公开文件身份和四份答案均加入新版冻结身份。答案未变，新提示与两阶段采样会影响行为，所以新运行条件和费用必须单独批准；旧预算的剩余额度不会自动授权新版本调用。

## 拟定实际调用方案

| 项目 | 候选上限 / 条件 |
|---|---|
| 模型 | SiliconFlow deepseek-ai/DeepSeek-V4-Flash |
| 题目 / 重复 | 4 道 development / 每题 1 次 |
| 阶段 | 最多 5 次收集 + 1 次最终请求 / 题 |
| 总请求 | 最多 24 次，无自动重试 |
| 输入代理预算 | 200,000 token；按序列化 UTF-8 字节 / 3 上取整再加 256 / 请求 |
| 输出申请预算 | 18,432 token，4 × (5 × 512 + 2,048) |
| temperature / 思考 | 0 / enable_thinking=false |
| 网络 | 本进程 NO_PROXY=api.siliconflow.cn，保留 TLS 校验 |
| 重试 / 格式修复 | 全部 0；一份批准只领取一次 |
| 费用参考 | 使用已记录高时段未缓存价约 ¥0.765888，实际看 usage 与平台账单 |

输入代理不是实际 token 或硬金额上限；价格记录见 plan/ESTIMATE，来源快照日期 2026-10-10。模型、温度、schema 和四题来源保持不变；收集输出上限、最终格式、共同提示和阶段调度是本版本改变的条件。没有独立拆分这些因素，本轮不能归因哪个改动带来提升。

## 可运行入口

```powershell
# 离线准备，无模型调用
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.structured_pilot --prepare
# 原生 Inspect + SDK 离线协议 fixture，无网络
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.tests.structured_transport_smoke
```

APPROVAL/FROZEN 尚未生成，真实请求为 0。`--api` 会先核验新冻结与一次性领取，再读取本地 SILICONFLOW_API_KEY；只有明确批准本方案后才生成冻结。密钥不写入文件、日志或服务器。

`bindings()` 在当前进程临时把新 Task、预算器和目录绑定到旧调用入口，并在返回/异常时恢复；不修改旧源文件。工具调用、消息、HTTP、日志仍由 Inspect 与其原生 OpenAI 兼容 provider 执行。新代码负责领域提示、阶段安排、限制及审计，未另写供应商调用框架。

## 学习顺序

阅读 system.txt 的工具选择规则 → `structured_pilot.make_task` 的两阶段 Solver → `RequestBudget.reserve` 的每阶段参数检查 → `pilot.score_output` 的原严格评分。运行日志包含 target，仅用于分析，不能再作为输入。
