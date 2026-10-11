# AssemblyGenomics Copilot

基于 Inspect AI 的基因组 QC 评测与工具辅助审核。项目包含两个入口：运行生信辅助工作流的 **AssemblyGenomics Skill**，以及检验规则与模型能力的 **AssemblyGenomics Bench**。

| 你要做什么 | 启动文档 |
|---|---|
| 识别输入、制定路线、生成 SOP、审核阶段产物 | [AssemblyGenomics Skill](ASSEMBLYGENOMICS_SKILL.md) |
| 查看规则/裸模型/技能包对照，以及 Inspect AI 正文/工具评测 | [AssemblyGenomics Bench](ASSEMBLYGENOMICS_BENCH.md) |

推荐从 main 克隆完整成果，按上述文档选择入口。原 Skill/Bench 入口分支保留历史发布版本；Inspect AI 接入开发分支为 `codex/inspect-adapter`。Bench 继续复用原规则，原 Skill 行为及冻结答案不变。

## 当前交付状态

- **Skill**：完成酵母、拟南芥、线虫从参考组装起步的注释四段闭环，沉淀真实失败机制、基线、状态与人工审核门。
- **Bench v1/v2**：已有冻结题库和计分报告，保留接口失败、解析失败及名单调整；不宣称所有模型使用 Skill 后都改善。
- **Bench v3**：七类群来源验收完成，四道开发草题待审核，尚未冻结或调用模型。
- **Inspect AI 接入**：复现固定版本官方任务，迁移并核对 648 条历史观测；完成 19 道 T1 正文/只读工具回归，共 114 条观测。
- **T3 工具评测**：七来源 14 题完成 Linux 产物复现及答案冻结；GLM 后续版本完成正文/工具各三次重复，共 84 条观测，83 条合法输出、1 条超时。题层判定与根因联合正确为正文 13/14、工具 12/14；这是开发调优后的探索性结果，不宣称工具整体增益。
- **回归验证**：作者工作区 2026-10-11 的完整测试为 503 passed；来源复现类测试需要另行提供已验收的小来源包。

三物种验证覆盖参考组装后的注释流程，不代表从原始读段组装、Hi-C 或多倍体/分相路线已经端到端验证。历史 A/B/C 为静态证据包评测；Inspect 扩展允许模型通过五个只读工具检查白名单文件，不提供任意 shell 或完整分析流程执行。AI 盲审明确标为 AI，不作为真人独立审核。

## 最新结果与复现

- [Inspect AI 无密钥复现与学习](bench/inspect_adapter/REPRODUCE.md)：官方 mock、历史回放及评分一致性核验。
- [官方真实小规模复现](bench/inspect_adapter/official/REPORT.md)：原官方 Task、工具与评分器的执行记录。
- [T1 19 题真实回归](bench/inspect_adapter/t1_regression/live1/REPORT.md)。
- [T3 GLM 84 条观测报告](bench/inspect_adapter/t3_test/glm_followup1/REPORT.md)与[错误分析](bench/inspect_adapter/t3_test/glm_followup1/ERROR_ANALYSIS.md)。

失败、预算、模型接口兼容性和调优版本均保留；重复观测不视为独立题目，T3 后续运行不作为新的 Skill 增益结论。

## 代码与研究材料

| 路径 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | 原技能定义与硬约束 |
| [scripts/](scripts/)、[knowledge/](knowledge/)、[references/](references/) | 流程工具、领域知识与审核政策 |
| [sop/](sop/)、[docs/](docs/) | 可复用 SOP、真实案例和能力边界 |
| [bench/](bench/) | 冻结题库、运行/评分代码及版本化报告 |

原始大文件、来源快照、incoming、运行缓存和 API key 不随源码发布。Bench 的作者答案和元数据只供构造/评分，不进入模型请求。

项目采用 [MIT License](LICENSE)。详细安装与启动步骤请从上方两个入口选择。
