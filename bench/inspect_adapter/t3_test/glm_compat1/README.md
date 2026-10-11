# 已批准的 GLM 思考兼容性试跑

用户2026-10-11回复“好”，批准这次4条协议兼容性试跑。上一轮关闭思考合同与GLM-5.3-FLASH强制思考不相容，0份合法QC决定；旧失败记录和已冻结答案保持原状。PLAN.draft.json保留原提案身份，正式授权以APPROVAL.json、PLAN.json与FROZEN.json为准。

可审核方案见PLAN.draft.json：同一模型、接口、环境变量密钥，冻结t3_001正常/t3_002蛋白ID故障×inline/tools各一次，共4槽位；只测试原生Inspect推理重放、工具和最终JSON兼容，不把开发样例作为新质量成绩。公共题面/产物/schema与gold都不改。

已批准的运行条件：enable_thinking=true，reasoning_effort=low，thinking_budget=2048；最多5轮收集，每轮max_tokens=2048，最终max_tokens=8192。每次预留max_tokens+thinking_budget；14请求、10万输入代理、81,920总输出申请，参考新增¥0.31。与已消费43请求、231,593输入代理、86,528输出申请合并，最多57请求、331,593输入代理、168,448输出申请；不增加原累计上限。

Z.AI原生接口支持低强度，但SiliconFlow对此型号路由的实际支持尚未验证。首批请求若4xx、空最终content、型号漂移、超预留用量或预算失败立即停止，不自动尝试其它参数、换模型或补跑。新版响应策略显式检查reasoning_content，不能仅依赖usage明细。

新版适配glm_compat.py已完成。原生Inspect离线fixture通过4条观测、14次最大轮数请求、50条工具回复，10个后续请求逐字回传原始reasoning_content；0外部调用。工具输入依然只有公开题面与产物，答案只进入本地scorer。新版使用独立目录和一次性启动claim，绑定历史消费记录哈希，不能重新启动刷新额度。实际平台兼容性以真实运行报告为准。

执行命令（仓库根目录，密钥只从SILICONFLOW_API_KEY读取）：

```shell
python -m bench.inspect_adapter.glm_compat fixture
python -m bench.inspect_adapter.glm_compat freeze
python -m bench.inspect_adapter.glm_compat run
```
