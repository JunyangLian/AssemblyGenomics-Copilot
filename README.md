# AssemblyGenomics Skill

AssemblyGenomics Copilot 的领域技能入口：根据输入制定路线、生成阶段 SOP、核查回传产物，并作出继续、警告、阻断或回退建议。规则、状态机和人工审核门约束模型的操作。

## 从这里开始

```bash
git clone --branch codex/assemblygenomics-skill https://github.com/JunyangLian/AssemblyGenomics-Copilot.git
```

进入克隆得到的仓库目录，在 Python 3.9 或更新环境安装基础依赖：

```bash
python -m pip install jsonschema PyYAML pytest
```

下面仅演示文件名识别和方案生成，示例不是实际分析数据：

```bash
python scripts/skill_coach.py SM_WGS_1.fq.gz SM_WGS_2.fq.gz SM_hic_all_1.fq.gz SM_hic_all_2.fq.gz --repr primary_reference
```

需要安装技能包时先生成包：

```bash
python scripts/package_skill.py
```

安装步骤、已有全局指令的合并要求以及完整操作约束见 [SKILL.md](SKILL.md)。本指南不会自动安装技能、运行基因组分析或调用模型 API。

## 实际工作循环

识别输入及交付要求 → 校验配置与环境 → 确认资源预算 → 生成 SOP → 用户在服务器执行 → 回传结果 → 规则与领域 QC → 人工审核 → 下一阶段或修复。状态以落盘记录为准，不能用聊天中的“已完成”代替。

| 组件 | 位置 |
|---|---|
| 完整技能定义 | [SKILL.md](SKILL.md) |
| 输入、路由与状态工具 | [scripts/](scripts/) |
| 真实失败机制及基线 | [knowledge/](knowledge/) |
| 交付表示与审核约束 | [references/](references/) |
| 三物种可复用流程 | [sop/](sop/) |
| 能力边界与案例 | [docs/capability_matrix.md](docs/capability_matrix.md) |

## 已验证的范围

T1 从参考组装和公共 RNA-seq 起步，完成酵母、拟南芥、线虫的重复注释、RNA 比对、结构注释和功能注释闭环。

| 物种 | 结构注释 BUSCO | Any-Annotated |
|---|---:|---:|
| 酿酒酵母 | 99.0% | 99.96% |
| 拟南芥 | 97.9% | 97.99% |
| 秀丽线虫 | 98.1% | 97.12% |

这些是相应真实案例的技术指标，不证明每个功能推断正确，也不代表从原始读段组装、Hi-C 或多倍体/分相路线已完成端到端验证。T3 的 27 物种历史报告提供规则和来源记录；其汇总判定不直接充当 Bench 标准答案。

## 测试与评测

作者工作区在 2026-10-09 的完整回归为 **347 passed**，包含 Skill 和 Bench。部分来源/复现测试需要另行提供已验收的小来源包；原始大文件不在 Git 仓库中。

```bash
python -m pytest -q
```

需要研究规则、裸模型与技能包的差异，请走 [AssemblyGenomics Bench](ASSEMBLYGENOMICS_BENCH.md)。两个分支共享代码和历史，分支首页只改变启动入口；原 Skill 命令与资产标识保持兼容。

[项目主入口](https://github.com/JunyangLian/AssemblyGenomics-Copilot/tree/main)
