# 只读工具原型验证

2026-10-09。仅在本地现有 Inspect 0.3.277 环境运行四道未冻结开发题的工具接口演示，不加载标准答案，不产生 QC 判定，不调用供应商 API。

## 文件与实际结果

- `readonly.py`：公开字节快照、只读分页、FASTA/TSV/GFF 统计、精确 ID 接续与闭区间计数；作为工具条件的事实计算，不扩展 A 原规则。
- `tool_demo.py`：直接使用 Inspect `use_tools()` + `generate()` 的多轮工具循环；scripted mock 通过原生 ToolCall 请求工具，工具实际执行，Scorer 检查日志合同。
- `tests/test_readonly.py`：16 个隔离和计算用例。
- `TOOL_LESSON.md`：数据流、工具职责、权限边界和日志阅读方法；README 更新当前状态。
- `TOOL_RECEIPT.json`：轻量验收身份；真实原生 Inspect 日志留在忽略的 `work/readonly_tools/logs`。

实际运行：4 个公开包，37 次工具调用，其中 33 次成功、4 次访问 `../expected.json` 被拒绝。没有丢弃被拒绝记录。初次验收器错误地从工具正文寻找错误字符串；Inspect 将错误放在独立 `error.message` 字段，修改验收器后成功。两次运行日志均保留本地，未改题目、产物或标准答案。

文件工具重算功能注释子集的 32 个匹配 ID、2 个标记蛋白、6.25% 覆盖率；空 hints 的 0 字节和 0 feature；两个序列交付窗口里三个闭区间的 115、32、33 个字符。它们只是观测，未把缺失运行日志补成确定根因。

## 检查

专项测试：16 passed in 0.46s。随后完整运行：

```text
python -m pytest -q
370 passed in 228.80s (0:03:48)
```

验证包括：私密/绝对/非规范路径拒绝；载入阶段不读 expected/meta；载入后统计不再访问文件系统；精确连接与覆盖率；空 hints 只计观测；闭区间计数；正文分页；快照不可变；重复 FASTA header 与 TSV 宽度错误拒绝。新增文件 LF 与凭证模式扫描、git diff --check 通过。

本地验证了 `python -m inspect_ai view --help` 的官方入口；没有为用户启动日志查看服务。Windows 已运行，Linux 本适配尚未运行。

## 边界与后续

mock 的工具顺序由脚本安排，4/4 链路合同成功不等于模型 4/4 答对。最终输出没有 verdict，draft expected 未用于计分；mock token usage 为模拟计数，不是实际供应商费用或 token 估算。

隔离由每题不可变字节和有限 Python 函数实现，没有任意代码工具，不宣称操作系统沙箱。若后续增加 shell 或任意 Python，需要另行容器隔离。本轮不增加独立测试题、不改变 v1/v2 口径、不自动将 v3 审核升级为批准。

真实模型小试验必须先确定是否仅作开发演示或正式评测，冻结相应标准答案/条件并确认模型与调用/token 上限；不因框架接入自动继承已消耗的旧预算。
