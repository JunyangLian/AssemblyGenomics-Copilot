# 项目当前状态

> 最后更新：2026-10-05 | 新会话先读本文件，再按需查 docs/ 细节

## 一句话

AssemblyGenomics Skill：生信流程的可靠性决策系统——解决 exit 0 但结果错/漏的静默失败。

## 已完成

| 项 | 状态 |
|---|---|
| 酵母环四段全链路 | ✅ BUSCO 99.0%，Any-Annotated 99.96% |
| **拟南芥段 3** | ✅ 2026-10-05，BUSCO 97.9% [S:96.9, D:1.1]，27,645 基因（真值 27,655，Δ=0.04%） |
| 陷阱库 | 10 条真实种子（PIT-001~010），检查脚本已验证 |
| 基线双层 | 项目锚点 + 类群兜底，25 物种群体校准完成 |
| 测试 | 128 passed |
| GitHub | JunyangLian/AssemblyGenomics-Skill（public，MIT） |

## 进行中

| 项 | 状态 | 阻塞点 |
|---|---|---|
| 线虫段 3 redo | 跳过 TSEBRA 重跑（braker.gtf 直连）+ 阈值回 95，待归档 v1 COMPLETE.json 后 resume | COMPLETE.json 归档 |
| 拟南芥段 4 | 段 3 已收官 | 等 SOP 编写 |
| 线虫段 4 | 段 3 redo 后启动 | 同上 |

## 拟南芥段 3 关键结论（2026-10-05）

- TSEBRA 重跑在 ET 模式下有害：intron0.8+filter 76.7% / intron0.8 89.5% / intron1.0 80.5%，内部合并直连 97.9%（PIT-009/010，单因素归因完整入档）
- 驱动新能力：`tsebra_rerun=false` 分支 + AGAT 基因数保持校验 + 导出器 UTR 白名单
- 详见 docs/use-case-004-arabidopsis-T1.md

## 暂停

| 项 | 恢复条件 |
|---|---|
| T3 批量规则验证 | 检查器批量调用改造 |
| 葡萄 #001 | 拟南芥/线虫段 4 跑完后启动 |

## 服务器信息

- 唯一服务器：Lianjunyang@user（hostname: user）
- 工具路径：见 `docs/validation-roadmap.md` T1 表 + `sop/yeast_loop/` settings
- 拟南芥数据：`~/AssemblyGenomics-Skill/arabidopsis/`
- 线虫数据：`~/AssemblyGenomics-Skill/caenorhabditis/`
- 酵母数据：`~/yeast_test/`
- BUSCO 谱系：`/home/Lianjunyang/env/busco/odb/`（eudicots_odb10、nematoda_odb10 等）

## 详细文档索引

| 文件 | 内容 |
|---|---|
| docs/decisions.md | D-001~D-028 全部决策 |
| docs/error_log.md | 全部错误与修复 |
| docs/use-case-003-*.md | 酵母环实录 |
| docs/use-case-004-*.md | 拟南芥 T1（含段 3 归因全记录） |
| docs/validation-roadmap.md | 三层验证体系 |
| docs/validation-cases/ | 验证用例注册表 |
| docs/capability_matrix.md | 能力矩阵 |
| knowledge/pitfalls/ | 10 条陷阱 |
| knowledge/baselines/ | 基线带 |
