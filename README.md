# AssemblyGenomics-Copilot

**基于 Inspect AI 的基因组 QC 评测与工具辅助审核。**

在基因组注释流程中，基因数下降、功能覆盖率偏低或文件连接失败，可能来自不同原因，也需要不同的处置。这个项目将真实分析产物、故障经验和阶段审核规则接入可复现的评测流程，检查模型能否找到证据、判断根因，并给出 `pass / warn / rollback / block` 的决定。

项目包含两个入口：

| 入口 | 用途 | 启动文档 |
|---|---|---|
| **AssemblyGenomics Skill** | 识别输入、生成 SOP、审核阶段产物，复用领域知识与规则脚本 | [Skill 指南](ASSEMBLYGENOMICS_SKILL.md) |
| **AssemblyGenomics Bench** | 比较规则、裸模型、模型加 Skill；通过 Inspect AI 评估正文阅读与只读工具条件 | [Bench 指南](ASSEMBLYGENOMICS_BENCH.md) |

## 核心实现

- **真实来源题库**：使用 T1 拟南芥、线虫、酵母的已验证产物，以及 T3 RefSeq GFF/FAA 来源；以确定性变体构造故障，保留来源与注入记录。
- **冻结答案与输入隔离**：题面与公开产物进入模型，标准答案及元数据只用于审核和评分；答案确认后记录哈希，变更另立版本。
- **Inspect AI 接入**：使用原生 Dataset、Task、Solver、Scorer、工具与日志；复现固定版本官方示例，并核对历史评分迁移的一致性。
- **五个只读工具**：`list_files`、`read_file`、`file_stats`、`annotation_counts`、`interval_counts`，用于查阅白名单文件和计算证据，不提供任意 shell。
- **失败与预算管理**：保留 API、解析、超时和规则未覆盖记录，设置调用与 token 上限，记录提示版本、工具参数错误及模型接口兼容性问题。

```mermaid
flowchart LR
    A[真实产物与确定性变体] --> B[公开题面与白名单文件]
    B --> C[Inspect Task / Solver]
    C --> D[正文阅读或只读工具]
    D --> E[结构化 QC 判定]
    F[已冻结标准答案] --> G[领域 Scorer]
    E --> G
    G --> H[报告与错误分析]
```

Inspect AI 提供评测编排、模型接口、工具循环和日志。本项目新增领域题库、受限工具、评分适配、来源复现及失败分析；原生信规则继续作为历史 A 组基线。

## 已完成的验证

| 内容 | 范围 | 证据 |
|---|---|---|
| 参考组装后的注释流程 | 酵母、拟南芥、线虫的重复注释、RNA-seq、结构及功能注释闭环 | [Skill 指南](ASSEMBLYGENOMICS_SKILL.md) |
| 历史 QC 对照评测 | v1 16 题；v2 24 题，四个完成模型 576 条观测及 A 组 72 条观测 | [v1 报告](bench/STAGE4_REPORT.md)、[v2 报告](bench/v2/reports/v2-run-10_four-models_human-reviewed/report.md) |
| Inspect 评分迁移 | 回放 648 条历史观测，并核对原评分与分层汇总 | [适配说明](bench/inspect_adapter/README.md)、[一致性凭据](bench/inspect_adapter/PARITY_RECEIPT.json) |
| 官方任务小规模复现 | 固定版本 12 个样本，保留官方 Task、工具与评分器；使用指定供应商模型 | [官方报告](bench/inspect_adapter/official/REPORT.md) |
| T1 正文/工具回归 | 19 题 × 两条件 × 三次重复，共 114 条观测 | [T1 报告](bench/inspect_adapter/t1_regression/live1/REPORT.md) |
| T3 正文/工具后续评测 | 七来源 14 题，Linux 产物复现；GLM 后续版共 84 条观测 | [T3 报告](bench/inspect_adapter/t3_test/glm_followup1/REPORT.md) |

作者工作区 2026-10-11 完整回归测试：**503 passed**。部分来源复现测试需要另行提供已验收的来源包；仅克隆源码不包含服务器原始数据。

### 最新结果：T3 GLM 后续版本

模型为 `zai-org/GLM-5.3-Flash`。14 题在两个条件下各重复三次，共 84 条观测，其中 83 条合法输出、1 条超时。下表以题为单位，按报告定义取多数结果：

| 指标 | 正文阅读 | 只读工具 |
|---|---:|---:|
| 判定正确 | 13/14（92.9%） | 14/14（100%） |
| 判定与根因联合正确 | 13/14（92.9%） | 12/14（85.7%） |
| 故障检出 | 6/7（85.7%） | 7/7（100%） |
| 正常题误报 | 0/7（0%） | 0/7（0%） |

工具条件检出了全部故障，但两题混淆了根因类别，联合正确率更低；一次正常题误报在观测层保留，题层多数仍正确。详见[错误分析](bench/inspect_adapter/t3_test/glm_followup1/ERROR_ANALYSIS.md)。

本轮是在查看先前失败后调整通用引用说明的探索性后续版本，不作为独立 held-out 测试，也不替代历史 Skill 对照结论。T1 与 T3 的多数及联合评分口径各按冻结协议执行，不跨版本合并成绩。

## 快速开始：无密钥离线复现

推荐从 `main` 克隆完整成果。以下为已验证的 Windows PowerShell / Python 3.10 路径；安装依赖需联网，随后两个入口使用本地 mock 和历史归档，不调用供应商 API。

```powershell
git clone --branch main https://github.com/JunyangLian/AssemblyGenomics-Copilot.git
cd AssemblyGenomics-Copilot
python -m venv bench/inspect_adapter/.venv
bench/inspect_adapter/.venv/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r bench/inspect_adapter/requirements-pilot.lock.txt

# 固定版本官方任务：本地 mock 执行工具循环
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.official.run

# 历史观测回放：核对领域评分迁移
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.replay
```

mock 用于验证执行链路，历史回放用于核对迁移，两者均不产生新的模型能力成绩。更多离线核验与日志查看方法见[复现指南](bench/inspect_adapter/REPRODUCE.md)，代码讲解见[面试与学习提纲](bench/inspect_adapter/INTERVIEW.md)。

已消费的真实运行不自动续跑；新的付费实验须另登记计划与预算。API key 仅从本地环境变量读取。

## 代码导航

| 路径 | 内容 |
|---|---|
| [SKILL.md](SKILL.md) | 技能定义与流程约束 |
| [scripts/](scripts/)、[knowledge/](knowledge/)、[references/](references/) | 原流程工具、领域知识与审核规则 |
| [sop/](sop/)、[docs/](docs/) | SOP、真实案例和流程记录 |
| [bench/](bench/) | 历史题库、冻结记录、调用与计分代码 |
| [bench/inspect_adapter/](bench/inspect_adapter/) | Inspect AI 接入、只读工具、官方复现及领域运行 |
| [readonly.py](bench/inspect_adapter/readonly.py)、[bridge.py](bench/inspect_adapter/bridge.py) | 工具白名单与历史评分适配 |

原 Skill/Bench 入口分支保留历史发布版本，当前完整成果以 `main` 为准；Inspect 接入开发分支为 `codex/inspect-adapter`。

## 能力边界

- 生信流程验证从参考组装开始，尚未覆盖从原始读段组装、Hi-C、多倍体或分相路线的端到端执行。
- 只读工具限定于小型公开证据包，不执行组装、注释或任意系统命令。
- 独立题量有限，同源变体与三次重复不算新增独立来源；正文/工具的输入长度及请求轮数不同。
- 标准答案主要由作者审核；agent 审题如实标为 AI 审核，不计作独立真人盲审。
- Linux 验证覆盖产物复现，Inspect 全链路在 Windows 验证；不能据此宣称全部跨平台运行通过。
- 不宣称模型使用 Skill 或工具后一定改善，也不将这些结果作为生产落地可靠性证明。

源码包含公开题目、冻结答案、结果摘录及校验材料。原始大文件、来源快照、incoming、运行缓存、完整私有对话和密钥不随源码发布。模型输入继续由白名单构造，不能直接把包含答案的研究材料整体交给模型。

项目采用 [MIT License](LICENSE)。官方示例的来源与许可记录见 [official/](bench/inspect_adapter/official/)。
