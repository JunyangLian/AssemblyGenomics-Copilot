# 无密钥复现与学习入口

以下从仓库根目录执行，使用已验证的 Windows PowerShell / Python 3.10 环境。安装依赖需要联网；其后的示例、回放、mock 和证据核验均不访问供应商 API。Linux 的 Inspect 适配尚未实测，不能把来源题库的跨平台复现等同于框架全链路跨平台验证。

## 1. 准备环境

```powershell
python -m venv bench/inspect_adapter/.venv
bench/inspect_adapter/.venv/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r bench/inspect_adapter/requirements-pilot.lock.txt
```

此锁包含本项目实际验证的 Inspect AI 0.3.277 和真实试跑所用客户端依赖。虚拟环境、日志和本地源包不提交。无需设置 API key，也不要把 key 写入命令、配置或日志。

## 2. 依次运行四条离线链路

按最新的“官方复现在前、领域扩展在后”路线，先运行原官方示例并阅读 [组件对照](official/README.md)：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.official.run
```

这是固定版本官方 Task / use_tools / generate / match 的原始实现。模型使用本地 mock，实际执行一次官方 add 工具；不等于真实模型 benchmark 复现。随后再运行下列领域教学和归档链路。

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.example
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.replay
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.tests.structured_transport_smoke
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.evidence_audit --verify
```

| 入口 | 应核对的结果 | 证明范围 |
|---|---|---|
| example | 本地 mock 的教学 Sample / Solver / Scorer | 最小组件调用可用，不是真实模型答对 |
| replay | 648 条归档观测、216 个组×题结果与旧口径一致 | 迁移保持原分母与结果；汇总复用旧函数，并非独立评分实现 |
| structured_transport_smoke | 3 个协议 fixture、48 次假 HTTP、28 次实际 Python 工具操作、0 网络请求 | 正常、收集上限、格式错误的真实客户端链路可用；模拟回答不计模型质量 |
| evidence_audit --verify | 4 题、24 条 evidence、10 次计算重现、原决定计数 3/4 | 导出的真实回答未改、计算可重现；作者语义诊断不升级为正式分数 |

回放使用已提交的历史结果归档，不需要服务器的大型来源包。审计使用已提交的公开四题和导出结果，不需要本地私有日志。原运行的全部原生对话只在作者本地保留，因此新克隆的最后一项会显示 `private_native_logs_reverified=false`，仍可验证摘录与凭据的身份及公开计算。

输出位于 `bench/inspect_adapter/work/`（已忽略）。重复离线运行生成自己的日志；不重做已消费的真实调用，不覆盖冻结标准答案。协议 fixture 的 usage 是模拟值，不能计入真实 token 或费用。

## 3. 看懂一个成功案例和一个失败案例

先阅读 [TOOL_LESSON.md](TOOL_LESSON.md)，再看 [pilot2 的真实报告](pilot2/REPORT.md) 与 [逐条诊断](audit/pilot2/DETAILS.md)。

对 dev_003，从 `PACKET.json` 找到 `interval_counts` 的参数与结果：区间使用一基闭区间，由完整内存序列计算，不受 `read_file` 分页影响。对照 `MODEL_RESULTS.json` 的最终 pass 和原 Scorer 标签，理解工具提供事实、模型负责决定、评分器比较冻结合同。

对 dev_001，沿 `annotation_counts` → 最终 evidence → 引用行内容追踪：2/32 的统计正确，引用的 g1/g2/g3 行却错位，block 也没有匹配 rollback。你应能解释为何“计数正确”“引用存在”“决定正确”“行动可执行”需要分别检查。

可查看自己刚生成的 Inspect 日志：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m inspect_ai view --log-dir bench/inspect_adapter/work/v2_replay/logs
```

复制命令实际打印的本地地址打开。服务进程须保持运行；端口随这次启动确定，不沿用历史临时 URL。该界面展示的是历史回放，原供应商重试、耗时和 token 以历史日志/报告为准。

## 4. 你应能自己讲清楚的流程

1. Sample 的公开消息与私有评分 target 如何分开？为何工具读不到 expected/meta？
2. Solver 怎样选择工具、接收 tool 消息，再进入关闭工具的最终 JSON 阶段？
3. 为何格式错、API 错和规则未覆盖仍留在分母里？为何三次重复不能当三道独立题？
4. Scorer 的决定匹配、证据位置检查与作者语义诊断分别证明什么？
5. 一个模型在四道开发题上改善，为什么还不能证明 Skill 增益或新来源泛化？

现有真实试跑版本已执行完。再次付费运行须另登记方案与预算；这些离线入口不会隐式续跑。当前交付范围和后续边界见 [PROJECT_STATUS.md](PROJECT_STATUS.md)。
