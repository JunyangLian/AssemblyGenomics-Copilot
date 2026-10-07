# 阶段3 mock 与费用报告

日期：2026-10-07。标准答案原样冻结，未进行计分；真实 API 调用 0，实际模型费用 ¥0。

运行计划 SHA-256：`e694c6e22811bef07ac8f20c002ff62ad6cf10997cdca34df28744c553954bed`。

B/C：实际 288 次 mock 调用，0 个最终解析失败。A：48个模拟运输槽位，不产生生物判定；服务器真实 A 待回传。

| 模型 | B 平均输入代理 token | C 平均输入代理 token | 初始/最多调用 | 1000输出假设费用 | 初始保守额度 | 全重试保守额度 |
|---|---:|---:|---:|---:|---:|---:|
| deepseek-flash | 2402.6 | 7716.1 | 96/192 | ¥1.74 | ¥9.17 | ¥18.37 |
| qwen3.8-27b | 2402.6 | 7716.1 | 96/192 | ¥2.61 | ¥13.75 | ¥27.55 |
| kimi-k3 | 2402.6 | 7716.1 | 96/192 | ¥19.31 | ¥107.51 | ¥215.35 |

三模型总计：288次初始，最多576次（每次解析失败只修复一次）；假设费用 ¥23.66，初始保守额度 ¥130.43，全重试保守额度 ¥261.27。

平均输入包括 schema/提示/产物，C 每次增加同一知识包。代理 token 不等于供应商计费 token；mock usage=null，不能报告为真实 usage。JSON 文件附输入代理/字节保守估计与输出额度总量。1000输出是假设，Kimi思考可能显著超过；额度按8192完整输出（Kimi允许10 token误差）估算。

参数：均请求 temperature=0；DeepSeek/Qwen关闭思考，Kimi启用思考；不静默回退参数。服务端是否接受/实际生效、账号权限及别名具体版本尚未真实验证；失败会记录，不擅自替换模型。

价格核对日期2026-10-06，人民币/百万token：DeepSeek 2/8（高峰未缓存），Qwen 3/12（北京），Kimi 20/100（北京，含思考）；忽略缓存、赠送额度和促销。

[DeepSeek价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)；[Qwen价格](https://help.aliyun.com/en/model-studio/qwen3-8-27b)；[Kimi价格](https://help.aliyun.com/zh/model-studio/model-pricing)；[阿里云参数及完整输出上限](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)。

真实调用仍需用户批准模型/计划/调用上限与费用预算，另存API_APPROVAL.json；当前没有此批准文件。费用守卫在发送前按保守值预留额度，达到上限即停，不自动重试网络错误；这是计划额度，最终账单以供应商为准。

原始JSONL保存在本地 bench/runs/（被既有Git忽略）；模拟记录不得用于H1-H3。A服务器结果需验证48个唯一槽位、原规则身份和公开输入哈希后才准计分。
