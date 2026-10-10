# 离线审计交付验证

2026-10-10，Windows PowerShell / Python 3.10。本轮未发起新的供应商请求，不改变已冻结实现、答案或正式评分。新增实现仅用于离线审计，现有 scripts/knowledge/references/schemas/sop/templates 逻辑未改。

| 检查 | 实际结果 |
|---|---|
| 最终全仓 `python -m pytest -q` | **424 passed in 224.86s** |
| 新增审计测试 | **16 passed in 1.38s**；含缺私有日志、冻结来源绑定、证据/计算改写、漏题与审核身份误标 |
| 文档指定环境的 evidence_audit --verify | 4 题、24 条原 evidence、10 次实际计算重现；3 个本地私有工件身份一致 |
| 导出身份 | 原 MODEL_RESULTS 字节绑定 RUN_RECEIPT；公开材料绑定原 FROZEN 与 packet manifest |
| 原正式计数 | schema 4/4；locator 4/4；decision_joint 3/4；未改 |
| 作者 AI 诊断 | supported 8、partial 13、unsupported 3；非独立、非盲、非真人、非正式评分 |
| Inspect 教学入口 | Dataset → 本地 mock generate → match → 日志实际通过 |
| Inspect 历史回放 | 648 观测、216 个组×题、810 分层面板、108 跨层配对面板核对一致 |
| 原生协议 fixture | 3 项通过；48 次假 HTTP、28 次实际工具、0 网络/供应商请求 |
| 新材料提交前检查 | 11 个文件凭据模式无发现，全部 LF；5 份学习/审计文档无失效本地链接 |

历史回放保留 ok 530、api_error 55、parse_error 40、not_covered 21、interrupted 2，合计648，未删除失败。回放汇总复用旧函数，不代表新增独立评分实现。

“没有私有日志”的验证通过临时目录只复制提交的审计文件、原冻结和凭据，保留公开题库完成；明确返回 private_native_logs_reverified=false、private_artifacts_reverified=0。这验证了缺少作者私有工件时的路径，不声称在另一台机器、Linux 或重新安装依赖后实测。

本地原生完整日志仍在忽略目录；公开摘录不包含所有工具消息或 HTTP 原文。完整性通过不裁定作者语义诊断正确，也不把行动安全性从 unadjudicated 改成通过。未重跑服务器原始大文件哈希。

全仓测试通过后只补写本验证记录并做本地提交。未来发布需扫描待发布树和未发布历史；现有原始源包、环境及密钥不随提交。
