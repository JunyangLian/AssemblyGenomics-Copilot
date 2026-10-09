# AssemblyGenomics Copilot

基因组流程可靠性与 QC 决策系统。项目包含两个入口：运行生信辅助工作流的 **AssemblyGenomics Skill**，以及检验规则与模型能力的 **AssemblyGenomics Bench**。

| 你要做什么 | 启动文档 | 对应分支 |
|---|---|---|
| 识别输入、制定路线、生成 SOP、审核阶段产物 | [AssemblyGenomics Skill](ASSEMBLYGENOMICS_SKILL.md) | [codex/assemblygenomics-skill](https://github.com/JunyangLian/AssemblyGenomics-Copilot/tree/codex/assemblygenomics-skill) |
| 查看和复现规则/裸模型/技能包的 QC 对照评测 | [AssemblyGenomics Bench](ASSEMBLYGENOMICS_BENCH.md) | [codex/assemblygenomics-bench](https://github.com/JunyangLian/AssemblyGenomics-Copilot/tree/codex/assemblygenomics-bench) |

main 保留完整共同代码基线。两个入口分支只调整首页，Bench 继续复用原规则；不会因为分支拆分而改变原 Skill 行为或冻结答案。

## 当前交付状态

- **Skill**：完成酵母、拟南芥、线虫从参考组装起步的注释四段闭环，沉淀真实失败机制、基线、状态与人工审核门。
- **Bench v1/v2**：已有冻结题库和计分报告，保留接口失败、解析失败及名单调整；不宣称所有模型使用 Skill 后都改善。
- **Bench v3**：七类群来源验收完成，四道开发草题待审核，尚未冻结或调用模型。
- **回归验证**：作者工作区 2026-10-09 的完整测试为 347 passed；来源复现类测试需要另行提供已验收的小来源包。

三物种验证覆盖参考组装后的注释流程，不代表从原始读段组装、Hi-C 或多倍体/分相路线已经端到端验证。Bench 当前为整理好的静态证据包评测，不是让模型自行查文件执行分析的 Agent 评测。

## 代码与研究材料

| 路径 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | 原技能定义与硬约束 |
| [scripts/](scripts/)、[knowledge/](knowledge/)、[references/](references/) | 流程工具、领域知识与审核政策 |
| [sop/](sop/)、[docs/](docs/) | 可复用 SOP、真实案例和能力边界 |
| [bench/](bench/) | 冻结题库、运行/评分代码及版本化报告 |

原始大文件、来源快照、incoming、运行缓存和 API key 不随源码发布。Bench 的作者答案和元数据只供构造/评分，不进入模型请求。

项目采用 [MIT License](LICENSE)。详细安装与启动步骤请从上方两个入口选择。
