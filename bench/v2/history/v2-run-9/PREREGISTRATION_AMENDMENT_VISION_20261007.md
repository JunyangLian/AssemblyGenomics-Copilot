# v2 Flash Vision 替换附录（运行后登记）

2026-10-07 用户明确回复：“那就用deepseek-v4-flash-vision吧，其他继续跑”。官方 /v1/models 同时列出 deepseek-v4-flash-0731 与 deepseek-v4-flash-vision，后者展示名 DeepSeek-V4-Flash-Vision、is_ready=true；证据为 PROVIDER_MODELS_VISION.json。本轮按用户决定将前者替换为后者，不能将两者描述为同一精确版本。

用户是在看到 dsv4-flash-vision 导致的身份暂停后选择 Vision。对新请求登记三种允许返回标识：deepseek-v4-flash-vision、DeepSeek-V4-Flash-Vision、dsv4-flash-vision；这是明确接受平台 Vision 型号及其已见返回标识，不是证明0731版本、具体权重或快照。其它型号不放行，其它四个模型的返回身份策略不变。发送的请求仍为 deepseek-v4-flash-vision；输入只含原有文本材料，不引入图片或工具。

这是第二次运行后的名单变更；冻结的预注册/授权、题目、答案、C2、门槛和分析单位保持原字节，另列 VISION_MODEL_REVISION.json 供后续报告披露。此前名单的 GLM 替代 Kimi 修订继续有效，最终五模型为 Vision、Pro、MiniMax、GLM、Qwen，至少2/5模型同方向要求不变。

旧0731请求的身份错误、原始响应及暂停全部留在历史队列审计中，不重标为成功或复用给 Vision。Vision 在同一24题上新建144个 B/C2 槽位；其它四模型的所有有效结果、超时与未知中断直接承接，不重跑。中断请求的消费未知，不返还预留。报告使用最终五模型的固定720槽位，并另报旧型号与基础设施队列。

切换前 Pro 已有34条有效观测、1条超时、2条中断未知；累计489次预留仍保留。总预算继续1440调用、28706760输入预留、11796480输出预留，达到上限停止新请求，不追加额度。名单与允许返回标识在新模型调用前锁定并跑mock；最终报告明确这不是最初五模型的纯事前预注册结果，也不把Vision输出误称0731能力。
