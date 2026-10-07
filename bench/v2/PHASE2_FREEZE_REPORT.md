# v2阶段2冻结汇报

2026-10-07。用户回复“可以”批准当前r2题单/答案及五个建议门槛1、0、0、1、1。此次为单人对整套当前答案的集中确认，保留new_019此前的具体审核与修订，不宣称独立多标注者验证。

1. 完成文件：

- REVIEW_APPROVAL.json：24题expected SHA-256与原话/确认范围；REVIEW_SHEET填写每题确认，保留new_019意见。
- SPEC_APPROVAL.json、preregistration.json、PREREGISTRATION.md：正式规格与五个门槛，至少2模型方向一致维持。原draft标已采用。
- SOURCE_MANIFEST.json：已验收来源包原清单副本，没有重扫原始来源大文件。
- freeze.py、FROZEN.json、FROZEN.md、FREEZE_VERIFIED.json：冻结/防篡改校验，24题答案哈希逐一登记，保护195个本版文件与11个共用依赖。
- validate_cases.py加入冻结核验；新增5项冻结保护测试，覆盖改答案、改C2、改门槛、加未登记文件及覆盖冻结。
- README与CHANGELOG同步。24题task/artifact/expected/meta/标签、C2内容、Linux r2证明和v1全部保持原字节。

2. 验证：

- 全仓python -m pytest -q：267 passed in 76.79s (0:01:16)，包含全部原有测试。
- v2冻结与本地构题校验PASS，Linux r2状态PASS；v1冻结及运行计划PASS。
- FROZEN.md SHA-256：b30dee32bf94c9c36ebe8f55b4f177205021685ce60623500dbecb92fd393188。
- 本阶段mock/真实模型/A规则调用均0，API费用0。

3. 后续事项：

- 阶段2已完成，题目审核和门槛不再待确认；不得根据后续模型结果修改冻结内容。如需改版，另起版本并记录原因。
- 阶段3另建v2 harness并锁定提示、实际请求参数/ID、规则适配与运行预算，完成A/B/C2 mock和token/费用或资源预估后停下汇报。指定五模型及端点已有许可，不重复请求同一许可；本次没有数字预算，也不把v1余额当新额度。
- 统一平台的实际思考控制、返回身份及费用/墨点换算仍是阶段3事项；没有在线探测或读取密钥。无来源或复现缺口，当前无需再跑服务器构题。

原CASE_INPUTS、REPRODUCTION_VERIFIED和REVIEW_UPDATES里的状态是其生成时点快照，已冻结保留；当前采用与冻结状态由批准记录、FROZEN、VALIDATION给出。每阶段独立commit，本阶段结束停下。
