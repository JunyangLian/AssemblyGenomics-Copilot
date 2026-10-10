# T1 原生 Inspect 真实回归：运行 1

用户于2026-10-11回复“允许”，批准19题 × inline/tools两条件 × 3次，共114条观测。原v2答案及六字段schema不改；20题候选中的二进制gzip题记为未支持，覆盖为19/20。这是见过旧结果的回归集，来源为三个T1项目，不是19个独立项目或新来源测试。

真实请求前冻结本目录 PLAN、APPROVAL、FROZEN 和运行实现。离线 OpenAI 协议 fixture 已通过114个槽位、57次工具执行；228个模拟请求全部在本地 MockTransport 中处理，未测量模型能力。

批准上限为399次HTTP请求、输入代理2,000,000、输出申请379,392 token；按2026-10-10价格快照参考约¥9.41。输入代理不是实际token或硬金额上限；账单以平台为准。每次物理请求在发出前预留额度，无响应也计入；不自动重试、续跑或更新预算。401/403/429及协议或型号变化会阻止后续请求。

模型为 SiliconFlow `deepseek-ai/DeepSeek-V4-Flash`，temperature=0，关闭思考，直接HTTPS连接，TLS校验开启，不跟随重定向。正文条件直接提供全部公开文本；工具条件提供题面和文件清单，最多5轮证据收集，随后关闭工具并用JSON模式提交。两条件均沿用通用审核提示，没有注入完整Skill知识包；这个比较是信息获取方式的描述性对照，不是历史B/C或Skill因果增益。

```powershell
# 检查冻结及离线协议，无供应商调用
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.t1_live fixture
# 真实调用：凭据必须已在本地进程环境中，单次授权只能领取一次
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.t1_live api
```

结果和原生日志存于忽略目录 `bench/inspect_adapter/work/t1_regression_live/<run_id>/`，包括请求摘要、经凭据脱敏的响应、预算账本和114条固定槽位结果。expected/meta只供本地评分与审计，不进入请求。主单位为题，verdict和root各取2/3多数，无多数记错；次要报告保留全部114条观测，解析失败、执行失败和缺失不从分母删除。证据语义与建议安全不由旧标签自动判定，H1–H3不在此回归中检验。
