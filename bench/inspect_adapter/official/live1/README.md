# 官方任务真实小规模复现 1

2026-10-10。用户明确授权：“可以，小规模跑完，看看够不够写简历，如果不够就跑全量”。本轮沿用用户此前指定的 SiliconFlow `deepseek-ai/DeepSeek-V4-Flash`，先完成有上限的小规模任务，之后评估是否还需要扩跑。

## 预先固定的范围

- 原官方 `addition_problem` 与 `parallel_add` 各1题，原 `theory_of_mind(critique=False)` 按数据原顺序前10/100题；每题一次，共12个计划样本，不按结果挑题。
- Inspect 0.3.277 / 官方提交 aa20052a；源码、官方完整题库、选择和原target哈希冻结。没有新编标准答案；原供应商模型并非上游示例 main 中的 gpt-4o，故不声称复现其模型分数。
- 原 Task、Solver、工具和 Scorer 不改；使用框架原生 `eval`/日志。通过 eval 的 limit 控制子集；Theory of Mind 的原 `model_graded_fact` 使用被评模型自评，通常解题/评分各一次。
- temperature=0、供应商 enable_thinking=false、最大输出2048、并发1、超时60秒、SDK/Inspect/格式自动重试均为0。原 chain_of_thought 提示仍在，解题的文本推理不等于供应商 reasoning 模式。
- 最多32次HTTP，输入代理100,000，输出申请65,536；最大未缓存参考费用 **¥0.889824**（输入¥3、输出¥9/百万token，2026-10-10 [价格来源](https://www.siliconflow.cn/pricing)）。代理限制不是精确供应商token上限，实际费用以账单为准。
- 沿用同一账户key，但只在本地当前进程环境读取，不写到仓库/日志。直连该域名且保留TLS校验。auth/quota/不符模型身份会停止后续请求，不自动换key、模型或重试。

`PLAN.json`/`TARGETS.json`/`APPROVAL.json`/`FROZEN.json`/`FROZEN.md` 都在真实请求前保存并提交。一个冻结身份只能领取一次实际运行；失败也保留旧记录。

## 运行与判断边界

官方mock与本轮完整假HTTP fixture已实际通过。全仓测试结果在验证记录登记。真实结果另写 REPORT.md、RUN_RECEIPT.json；没有结果时不把这里的方案当作执行成功。

这里的复现目标是官方数据 → 官方推理Solver → 模型回答 → 官方模型Scorer → 日志/结果的流程。不是新的生信QC评测、不是跨模型排名，也不能把同模型自评叫真人或独立专家复核。

简历是否够用主要检查：来源固定、12个计划结果完整保留、实际解题/评分/工具可追溯，加上已有真实四题领域接入与648条评分回放。即使官方分数较高，也不能称新来源泛化；若接入或日志缺失，应先修复具体问题，扩大题数不会自动解决。

全量指这个官方 Theory of Mind 的100题，**不是把 Inspect 的所有任务全跑一遍**。本入口不自动扩成100题。需要时另固定运行计划并估算剩余90题与评分调用；前10题与失败保留，不重新选题。此前已有生信结果不改。

作者复现命令（会真实消费已批准的一次运行，普通学习不要执行）：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.official.live --api
```

默认学习先运行无密钥的 official.run 或 tests.official_transport_smoke。真实调用必须满足本冻结与依赖版本，且当前进程环境有 SILICONFLOW_API_KEY。
