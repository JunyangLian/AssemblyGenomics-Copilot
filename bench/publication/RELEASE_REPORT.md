# 双入口发布准备与验证

2026-10-09。用户将仓库更名为 JunyangLian/AssemblyGenomics-Copilot，并授权推送现有内容及 Skill/Bench 两个入口分支。

1. 新增根目录 ASSEMBLYGENOMICS_SKILL.md、ASSEMBLYGENOMICS_BENCH.md；main README 改为双入口导航。两个入口分支共享源码，分别使用对应指南作为 README；保留原 SKILL.md 与全部冻结内容。
2. `python -m pytest -q`：**347 passed in 208.18s**；`python bench/freeze.py`、`python bench/v2/freeze.py`、`python bench/v3/validate_development.py` 均 exit 0。所有验证均为本地，没有新增模型 API 调用。
3. 发布前已检查 48 个未发布提交和当前树，共 1,037 个唯一 blob，未发现所扫描模式的凭据或超过 GitHub 单文件限制的内容。发布工具在文档提交之后再次扫描；报告只保存于忽略的 work/，不打印匹配值。此检查不保证发现所有秘密格式。
4. 未跟踪的用户归档、来源快照、incoming 和运行缓存不上传。历史上已跟踪的报告和评分证据保留，不改评测成绩或历史服务器路径。
5. origin 更新为新地址，写入权限和普通快进条件通过 dry-run。正式发布显式推送 main、codex/assemblygenomics-skill、codex/assemblygenomics-bench，不 force；以推送完成后远端引用核对为最终依据。

v3 仍为四道未批准开发草题，两个执行证据缺口延后；独立审题、Linux 复现及正式冻结尚未完成。发布代码不代表 v3 已完成验证。无需将技能命令或原分析流程改名为 Agent。
