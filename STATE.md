# 项目当前状态

> 最后更新：2026-09-28 | 新会话先读本文件，再按需查 docs/ 细节

## 一句话

AssemblyGenomics Skill：生信流程的可靠性决策系统——解决 exit 0 但结果错/漏的静默失败。

## 已完成

| 项 | 状态 |
|---|---|
| 酵母环四段全链路 | ✅ BUSCO 99.0%，Any-Annotated 99.96% |
| 陷阱库 | 9 条真实种子（PIT-001~009），检查脚本已验证 |
| 基线双层 | 项目锚点 + 类群兜底，25 物种群体校准完成 |
| 测试 | 128 passed |
| GitHub | JunyangLian/AssemblyGenomics-Skill（public，MIT） |

## 进行中

| 项 | 状态 | 阻塞点 |
|---|---|---|
| 拟南芥段 3 | BRAKER 已启动 | 等 COMPLETE.json |
| 线虫段 3 | BRAKER 已启动（归档旧 species 后重启） | 等 COMPLETE.json |

## 暂停

| 项 | 恢复条件 |
|---|---|
| T1 拟南芥 RNA-seq 下载 | 按 use-case-004 清单 wget -c 续传 |
| T3 批量规则验证 | 检查器批量调用改造 |
| 葡萄 #001 | 拟南芥/线虫 T1 跑完后启动 |

## 服务器信息

- 唯一服务器：Lianjunyang@user（hostname: user）
- 工具路径：见 `docs/validation-roadmap.md` T1 表 + `sop/yeast_loop/` settings
- 拟南芥数据：`~/AssemblyGenomics-Skill/arabidopsis/`
- 线虫数据：`~/AssemblyGenomics-Skill/caenorhabditis/`
- 酵母数据：`~/yeast_test/`
- BUSCO 谱系：`/home/Lianjunyang/busco_downloads/lineages/` + `/home/Lianjunyang/env/busco/odb/`

## 详细文档索引

| 文件 | 内容 |
|---|---|
| docs/decisions.md | D-001~D-028 全部决策 |
| docs/error_log.md | 全部错误与修复 |
| docs/use-case-003-*.md | 酵母环实录 |
| docs/use-case-004-*.md | 拟南芥 intake |
| docs/validation-roadmap.md | 三层验证体系 |
| docs/validation-cases/ | 验证用例注册表 |
| docs/capability_matrix.md | 能力矩阵 |
| knowledge/pitfalls/ | 9 条陷阱 |
| knowledge/baselines/ | 基线带 |
