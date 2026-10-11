# BixBench 外部轨：静态可行性检查

2026-10-11。仅检查官方目录、注册版本代码与本地命令可用性；未安装上游、拉容器、下载 capsule 或调用模型。

Inspect Evals 将 BixBench 标为外部注册任务，实际接入仓库为 `concordia-ai/concordia_evals`，注册提交为 `e99597c8a5d68c85a5bbbb00020d7d1c813ad0e1`。运行时应锁定该实现及其数据/容器版本，不以 Future-House 仓库的零样本命令冒充这一 Inspect 接入。

在该注册代码中确认的依赖与接口：

- Docker Linux 环境中运行 IPython notebook，支持 Python/R 分析；当前五个 QC 只读工具不能替代这个分析环境。
- 数据版本写在上游实现中，数据下载与环境准备需要联网。
- Scorer 另调用 LLM judge；默认评审模型是 `openai/gpt-4o`，未显式指定时可能产生未经预计的费用。解题与评审必须分别配置并计入预算，同模型评分不能称为独立专家审核。
- 按上游 Task、提示、工具与 Scorer 执行才可报告其子集结果；更换 solver、judge 或预算时完整记录差异。

本地检查发现 `uv` 可用，`docker` 命令未在 PATH 中找到。不能据此断定机器未安装 Docker，但当前终端不具备可直接执行的容器入口。未测试 daemon、镜像、数据访问或模型兼容性，因此本轮不承诺外部试跑可立即启动。

建议仅作可选后续：环境可用后，先固定 2–3 个不同 capsule 的小子集，按预先规则选题并记录所有 ID；先完成无模型的环境/数据 smoke check，再估算解题和 judge 的完整调用预算。未失败后换简单题，不立即运行上游全量脚本。报告名称必须包含“BixBench 固定版本小子集”，不等同于全量成绩、QC 新来源成绩或基础模型无污染测试。

外部 capsule 不能同时用于调优并作为 QC 封存来源。本轮六个 T3 来源与外部轨完全分开；暂无外部 capsule 选择或付费授权。该轨不阻塞主线收尾。

证据链接（读取于 2026-10-11）：[Inspect Evals BixBench 注册入口](https://ukgovernmentbeis.github.io/inspect_evals/evals/bixbench/index.html)、[注册提交实现](https://github.com/concordia-ai/concordia_evals/blob/e99597c8a5d68c85a5bbbb00020d7d1c813ad0e1/src/concordia_evals/bixbench/bixbench.py)、[原 BixBench 仓库](https://github.com/Future-House/BixBench)。
