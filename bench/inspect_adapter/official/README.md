# 先复现官方流程，再接入生信数据

2026-10-10。用户明确希望先学懂并复现开源项目，再将已有数据接上去，缩短交付周期。本项目后续主线调整为 **Inspect 官方原流程 → AssemblyGenomics 领域扩展**，旧题审计材料作为归档，不再作为新增功能的主线。

## 这里复现了什么

来源为 Inspect AI 官方仓库标签 `0.3.277`、提交 `aa20052a65b13516f1ee79d10ccceda00c205cc6` 的 [examples/tool_use.py](https://github.com/UKGovernmentBEIS/inspect_ai/blob/aa20052a65b13516f1ee79d10ccceda00c205cc6/examples/tool_use.py)。`upstream/` 保存该文件与 MIT 许可证的原始字节，归属和哈希见 `SOURCE.json`。

`run.py` 加载原文件，**只运行原 addition_problem()**：原 Sample → 原 use_tools(add()) → 原 generate() → 原 match(numeric=True) → Inspect 原生日志。不修改原 Task、Solver、工具或评分器；不运行同文件中的 local sandbox、shell 或写文件示例。

本地 mock 请求 add(1, 1)，Inspect 实际执行官方 Python 工具并返回 2，再将最后回答交给官方评分器。模型请求是脚本模拟，因而本轮证明官方工具协议与日志链路可复现，**不证明真实模型能力、不复现官方 benchmark 分数、也不表示整个 Inspect 项目已经复现完成**。

仓库根目录运行，环境沿用 [REPRODUCE.md](../REPRODUCE.md)：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.official.run
```

实际输出 PASS；1 个官方样本、1 次真实 Python 工具调用、0 次供应商 API。原生日志和验证凭据写入 `bench/inspect_adapter/work/official_tool_use/`。版本或保存的上游代码改变，入口会拒绝加载。

## 怎样把我们已有的东西接进去

Inspect 是评测框架。融合位置就是它的 Task 组件接口，已有领域代码继续复用：

| 官方流程的组件 | AssemblyGenomics 接入 | 已有实现 |
|---|---|---|
| dataset / Sample | 中性任务与真实产物；冻结答案留在评分 target | bridge.py、structured_pilot.py:make_task |
| tools | 文件只读、精确 ID 接续、覆盖与区间统计 | readonly.py |
| solver | Inspect generate/use_tools；真实 QC 在收集后单独提交 JSON | structured_pilot.py:collect_then_submit |
| scorer | 判定/根因/格式与冻结答案比较 | pilot.py:score_output |
| eval / log / view | 使用 Inspect 运行、记录和查看 | 原生 Inspect；领域入口调用其 API |

这部分已有真实执行：第二次四题运行由 Inspect 编排，16 次真实请求、25 次工具调用，格式4/4、决定匹配3/4。因此现在缺的是官方基线的学习/复现顺序与更清晰的组件对照，不需要再重写一个评测引擎。

学习时并排阅读 `upstream/tool_use.py` 的 addition_problem 与 `structured_pilot.py` 的 make_task：每个组件如何替换、哪里必须保留领域合同、哪里直接交给框架。然后看 dev_003 的真实工具日志，确认数据和工具进入的是同一类原生消息循环。

## 后续收敛顺序

1. 官方流程：先运行上述原代码，读懂工具请求、执行、最终输出和评分的边界。
2. 领域扩展：复用现有四题接入，整理一份官方组件与领域组件的对照；不扩题、不追加旧结果审计，不重写调用/日志管理。
3. 真实小规模复现已完成：官方两个工具样本及Theory of Mind前10题，原实现不改；最终2/2工具任务通过、QA同模型自评分9/10，保留首轮超时和预算内恢复。见 [REPORT.md](REPORT.md)。默认run.py仍只有mock，不隐式调用模型；已消费的live版本不能重新调用。

现在已有官方原流程真实复现和生信扩展的证据，本轮不为增加题数继续100题。整体目标是能够展示并解释“我学会了开源框架，并实现了一个生信 QC 扩展”，不是复制 Inspect 的全部任务与基础设施。工具教程参考 [官方说明](https://inspect.aisi.org.uk/tutorial.html#custom-tools)。
