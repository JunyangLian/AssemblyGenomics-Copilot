# 从“阅读摘要”到“调用工具寻找证据”

本轮是四道开发题的**离线工具原型**，不是正式 v3 测试或新的准确率结果。标准答案未载入，mock 最终返回 `{"mock_complete":true,"qc_verdict":null}`，不会输出伪造的模型 QC 判断。

## 先运行一次

仓库根目录，使用上一轮安装的 Inspect 环境：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.tool_demo
```

实际通过：4 个公开题目包，37 次工具请求，4 次私密路径探测被拒绝，0 次供应商 API 调用。mock 按脚本选择工具，不能把这个成功率解释成模型会自己规划。

## 一次工具调用发生了什么

以功能注释子集为例：

1. Dataset 初始消息只给任务说明和公开文件名/大小/哈希；产物正文要用工具读取。它不加载 expected、meta 或 reviewer mapping。
2. `use_tools()` 注册只读工具，`generate()` 请求下一条模型消息；mock 在这里模拟工具请求。
3. 模型消息给出工具名 `annotation_counts` 和参数 `query_path` / `table_path`。
4. **Inspect** 调用受信任的 Python 工具，从该题已载入的公开字节重算精确 ID 接续和标记数。
5. 工具结果作为一条 tool 消息返回。此题得到 32 个蛋白、32 个表行、32 个匹配 ID、2 个有标记的蛋白，覆盖率 6.25%。
6. `generate()` 再请求模型消息，直到不再请求工具；本轮以 mock 完成标记结束。
7. Scorer 检查工具请求与返回是否齐全、结果是否对应文件、私密路径是否拒绝；不检查生物学判断是否正确。

以后接入真实模型，第 2 步由模型选择工具，第 6 步输出 QC JSON；这些结果需要新的冻结与预算批准。本轮没有替模型完成真正的推理评测。

## 你需要分清的三个部分

| 部分 | 职责 | 文件 |
|---|---|---|
| 框架 | 模型消息、工具请求执行、多轮循环、日志 | Inspect 的 `use_tools()` 与 `generate()` |
| 领域工具 | 读取文件、精确计数、ID 接续和区间统计；不输出 verdict/root_cause | `readonly.py` |
| 评测设计 | 给哪些材料、审核哪种合同、怎样比较最终判定 | 现有题面；正式工具评测规格尚未冻结 |

`annotation_counts` 是给模型的计算工具，不是 A 组新增规则。这轮没有改 A 的覆盖率，也不把辅助工具的算术正确性当成模型能力。

## 工具能读到什么

`PublicFiles` 先用原公开白名单载入 task.md 和 artifacts，之后以不可变内存字节提供服务。模型传入的路径只是字典键，工具不再打开操作系统路径。

- `list_files`：列公开文件与大小、哈希。
- `read_file`：最多 200 行 / 16,000 字节的正文页，带一基行号；截断时给 next_line。
- `file_stats`：FASTA 的 ID/长度、TSV 行数、GFF feature 数。
- `annotation_counts`：按 FASTA 第一个 token 与 query 精确连接并计数。
- `interval_counts`：按一基闭区间计数小写 acgt、N、n 和其他字符。

每个文件最多 128,000 字节、每题最多 256,000 字节，仅支持 UTF-8 文本。不提供写文件、网络、任意 Python 或 shell。标准答案、元数据、其他题目和宿主文件都不在工具能力范围。这是受限函数接口，**不是操作系统/容器沙箱**；未来如增加任意代码执行，需要另接 Inspect sandbox。

空 hints 只能证明当前输入为空，不能证明旧作业没有使用 RNA；覆盖率低也不能单凭计数确证上游原因。工具提供观测，模型仍要遵守题面范围和证据边界。

## 怎样看日志

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m inspect_ai view --log-dir bench/inspect_adapter/work/readonly_tools/logs
```

打开命令输出的本地地址，选一条 sample：先看初始 user 消息，再找 assistant 的 tool_calls、对应 tool 结果和错误字段，最后看 mock 完成标记与 Scorer。工具错误存放在单独的 error 字段，正文可能为空；不能靠正文为空推断工具成功。

请验证自己能解释：为何 `../expected.json` 被拒绝？为何覆盖率重算用完整 32 条而不是只看正文第一页？为何 reference.fa 的 N 不自动构成交付错误？为何四次 mock 成功不能写成四道真实模型答对？

资料：[Inspect 工具基础](https://inspect.aisi.org.uk/tools.html)、[自定义工具](https://inspect.aisi.org.uk/tools-custom.html)。本轮运行验收记录见 `TOOL_VALIDATION.md`；日志与临时文件留在忽略的 work 目录。
