# v2 运行变更记录

## v2-run-1 — 2026-10-07，阶段3

新增独立v2 B/C2 harness、原规则A运输/复用、mock资源报告与固定累计预算门。锁定用户指定的五模型及统一OpenAI端点；共用请求协议temperature=0、max_tokens=8192、stream=false，实际思考模式登记provider_default_unknown。它是经mock验证的提议协议，真实调用还需用户审阅参数限制与资源上限。

720个初始mock请求全部解析通过，0真实API。A只做72个明确标记的运输模拟；48条真实旧A按输入/规则身份复用，24条新增A留待服务器。无标准答案、模型可见材料、C2或预注册修改；不计分mock，不接触v1累计账本。

冻结前的题单/C2与new_019关键依据修订记录仍在已冻结的CASE_PLAN、context/PROVENANCE、REVIEW_UPDATES及审核证明中。本次不重写它们。
