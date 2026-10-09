# AssemblyGenomics Copilot 发布入口

用户已将 GitHub 仓库更名为 AssemblyGenomics-Copilot，并授权推送现有内容与两个启动分支。

| 分支 | 首页/入口 | 代码关系 |
|---|---|---|
| main | README 双入口导航 | 共同开发基线 |
| codex/assemblygenomics-skill | AssemblyGenomics Skill 启动说明 | 与 main 仅 README 不同 |
| codex/assemblygenomics-bench | AssemblyGenomics Bench 启动说明 | 与 main 仅 README 不同 |

两个启动文档为根目录 ASSEMBLYGENOMICS_SKILL.md、ASSEMBLYGENOMICS_BENCH.md。分支是入口视图，不删除 Bench 所需原规则、不分叉两套流程逻辑。未来功能更新以 main 为基线，发布时同步入口分支。原 SKILL.md、技能命令标识、模型冻结材料和服务器历史路径保持原样。

audit_git.py 只读扫描 HEAD 已跟踪文件及相对发布基线未推送的历史 blob，包含 ZIP/gzip 内文。匹配项只输出文件/行号，不打印值；不读取环境中的 key 或忽略目录。它是格式模式检查，不保证发现所有秘密格式。报告仅写 work/，不作为冻结答案或模型输入。

```bash
python bench/publication/audit_git.py --base origin/main
```

推送采用显式 main/两启动分支和普通快进，不用 force、不上传未跟踪归档、原始数据快照或本地运行缓存。历史运行结果/冻结证据中已跟踪的材料保留，不能为了缩短仓库改写评测结果。
