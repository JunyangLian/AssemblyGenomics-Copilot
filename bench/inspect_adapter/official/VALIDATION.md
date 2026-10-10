# 官方原代码复现验证

2026-10-10，Windows。本机已安装的 Inspect 0.3.277 与官方标签/提交绑定一致。

- `official.run` 实际通过：未改的 addition_problem Task → use_tools(add) → generate → match(numeric=True) → 原生日志。1样本、1次实际add执行、0供应商调用。模型消息由本地mock产生，不计真实模型准确率。
- 原 upstream/tool_use.py、LICENSE 用 `git show` 获取并按原字节保存；SOURCE.json 记录固定提交、SHA-256、路径和许可证。没有运行上游安装脚本或本地shell/写文件任务。
- 最终 `python -m pytest -q`：**426 passed in 221.17s**。新增两项检查确认版本漂移或原代码改变时，在加载任务前拒绝。
- 新增材料凭据模式扫描无发现。未读取环境密钥；没有正式答案或评分变更，没有新增生信数据审计。
- `MOCK_RECEIPT.json` 保存实测摘要。完整原生日志在本地忽略工作目录；日志中的模拟得分只检查框架链路，不是供应商评测结果。

本轮只完成官方工具示例的离线流程复现。官方 benchmark 的真实模型结果尚未复现；现有生信四题真实接入结果继续保留，不以本mock示例替代。
