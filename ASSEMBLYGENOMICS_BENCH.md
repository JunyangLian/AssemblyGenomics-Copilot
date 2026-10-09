# AssemblyGenomics Bench

AssemblyGenomics Copilot 的评测入口：用真实产物及确定性变体比较 A（已有规则）、B（裸模型）、C（模型 + 固定技能知识包），分别衡量处置、根因、证据、误报、配对区分和危险建议。

## 从这里开始

```bash
git clone --branch codex/assemblygenomics-bench https://github.com/JunyangLian/AssemblyGenomics-Copilot.git
```

进入克隆得到的仓库目录，在 Python 3.9 或更新环境安装基础依赖：

```bash
python -m pip install jsonschema PyYAML pytest
```

先阅读报告和冻结记录。下面命令只验证版本完整性及开发草题，不调用模型 API：

```bash
python bench/freeze.py
python bench/v2/freeze.py
python bench/v3/validate_development.py
```

从源文件重新构造或做完整来源核验需要已验收的来源包，不能只用 Git 克隆替代。v3 的 `--reproduce` 在有对应 T1 小来源时使用；不从汇总表伪造原文件。

## 当前版本

| 版本 | 状态 | 阅读入口 |
|---|---|---|
| v1 | 16 题冻结，A/B/C 共 336 条最终观测已计分；失败保留分母 | [阶段4报告](bench/STAGE4_REPORT.md) |
| v2 | 24 题冻结；四个完成模型 576 条最终观测，加 A 组 72 条；退出模型记录保留 | [人工审核后的报告](bench/v2/reports/v2-run-10_four-models_human-reviewed/report.md) |
| v3 | 七类群来源已接收；四道 T1 开发草题待审，两项执行证据缺口延后；未冻结、未运行模型 | [开发阶段报告](bench/v3/DEVELOPMENT_REPORT.md) |

v2 新增主集合并未达到预设的改善门槛，不能用总体或回归题改善替代主比较。后续四模型收尾集合是结果查看后的范围调整，原预注册名单与失败记录都在报告中保留。v3 用于完善可答性、证据约束和来源分组，当前没有正式能力结论。

## 评测约束

- 模型只看题面的 task.md、白名单 artifacts 和统一输出 schema；C 额外看版本固定的公共知识包。
- 作者答案、来源元数据、注入说明、审核表和运行结果不得进入模型请求。公开仓库可包含这些研究材料，输入构造必须继续使用白名单。
- 标准答案由用户审核，冻结哈希后才能启动模型；变更另立版本。
- 默认每题三次重复；API/解析失败、不覆盖和无多数保留计划分母，不能静默删除。
- 来源、机制、指导暴露分开标记；同源变体不能跨开发与测试。统计只按相应集合/单位解释。
- 所有 API key 仅从本地环境变量读取，不写入仓库、服务器包或模型日志。真实评测需要新的明确预算；此启动指南不启动 mock 或真实评测。

## 文件导航

| 内容 | 位置 |
|---|---|
| v1 规格及历史阶段记录 | [bench/README.md](bench/README.md) |
| v2 协议、运行和报告 | [bench/v2/](bench/v2/) |
| v3 当前状态与后续阶段门 | [bench/v3/README.md](bench/v3/README.md) |
| v3 处置/消费契约 | [CASE_CONTRACT.md](bench/v3/CASE_CONTRACT.md) |
| v3 证据评分 | [EVIDENCE_SCORING.md](bench/v3/EVIDENCE_SCORING.md) |
| v3 独立人类审题 | [INDEPENDENT_REVIEW_PROTOCOL.md](bench/v3/INDEPENDENT_REVIEW_PROTOCOL.md) |

完整回归命令为 `python -m pytest -q`；作者工作区当前 **347 passed**。部分测试需本地验收来源包，原始来源、incoming 目录、运行缓存和 API key 不随源码发布。独立审核者只接收专门的盲审材料，不接收作者答案和注入记录。

Bench 分支保留 Skill 的原规则及依赖，确保 A 组能力边界可追溯；不把评测验证器当作新增 A 组规则。需要运行生信辅助工作流，请走 [AssemblyGenomics Skill](ASSEMBLYGENOMICS_SKILL.md)。

[项目主入口](https://github.com/JunyangLian/AssemblyGenomics-Copilot/tree/main)
