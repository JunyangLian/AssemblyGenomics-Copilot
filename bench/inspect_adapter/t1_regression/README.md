# T1：19题工具回归

2026-10-11。真实回归已完成：[完整报告](live1/REPORT.md)、[失败解释](live1/ERROR_NOTES.md)、[阶段汇报](live1/PHASE_REPORT.md)。19题×两条件×三次，114条观测，289次请求、345次工具执行，参考约¥3.86。题级根因匹配正文15/19、工具19/19，联合匹配均10/19；3条受消息上限影响，原分数保留。以下准备规格与mock记录仍保留历史身份，mock不作为模型成绩。v1/v2冻结输入/答案、四题开发试跑和官方任务记录保持原样。

## 覆盖与缺口

| 来源 | v2中的T1候选 | 可运行回归题 | 缺口 |
|---|---:|---:|---|
| 拟南芥 | 17 | 16 | regression_002：截断gzip，现有工具不支持二进制 |
| 酵母 | 2 | 2 | 无 |
| 线虫 | 1 | 1 | 无 |
| 合计 | 20 | 19 | 1 |

全题覆盖表见 [CASE_INVENTORY.csv](CASE_INVENTORY.csv)。19题包含12道fault、3道normal、1道hard_negative、3道pressure，覆盖输入配对、AGP一致性、重复/结构/功能注释审核。AGP题沿用真实序列上的合成构造，不声称拥有真实Hi-C运行。

19题不是19个独立项目：来源只有三个T1物种/项目，题对、施压副本和共享材料存在关联，且旧题及模型结果已被查看。全部标为seen_regression，不叫新held-out测试。gzip题保留not_supported状态；两条件都排除它，明确报告候选覆盖19/20和可运行19题的质量分母，不把摘要读取伪装成gzip工具核验。

## 旧合同保持原样

直接使用v2的六字段model_output schema和已批准的expected值/字节，私有副本见 LEGACY_TARGETS.json；原答案SHA列于覆盖表。Task仅把答案放到Scorer target，初始消息和只读工具只加载task/artifacts。按原verdict、root和joint口径判分，格式/API失败留在运行分母；不会把旧root转换为v3的observed_defect/insufficient_evidence。

旧题根因标签反映原回归合同，部分机制在新版证据契约下未必可确证。这里检验原合同一致性，不升级为独立生物学真值；T3新来源按可见证据另定合同，不把两套根因准确率合并。

## 两个条件与计划

- inline：初始提供完整公开文本，关闭工具，提交旧六字段JSON。
- tools：初始提供相同公开文件的目录/摘要，注册原五个工具；最多5轮收集，每轮512输出token，再关闭工具，最多2048输出token提交JSON。

同一通用system、输出schema和最终提交说明；每题每条件3次，19×2×3=114个计划观测。不是增加Skill知识包的C组，也不与旧B/C成绩直接作因果比较。两条件的数据范围相同，但呈现方式、初始长度和多轮费用不同，报告这些混杂因素；inline组不会只收到无法作答的文件名。

提议使用SiliconFlow deepseek-ai/DeepSeek-V4-Flash，temperature0、非思考、60秒超时、并发1，无SDK/Inspect/格式自动重试。计划见 [PLAN.draft.json](PLAN.draft.json)，目前api_call_authorized=false；本入口只支持--prepare/--mock，不能发真实请求。

| 预算项 | 提议值 |
|---|---:|
| 计划独立题 / 观测 | 19 / 114 |
| 最大HTTP请求（含工具多轮） | 399 |
| 累计输入代理上限 | 2,000,000 |
| 累计输出申请上限 | 379,392 |
| 沿用2026-10-10未缓存高时段价格的参考额度 | 约¥9.41 |

输入代理不是供应商实际token，输出申请也不是实际生成量；¥9.41是上述代理额度的参考，不是账单保证。模型、价格快照和key_env均记录，但没有密钥。初始输入代理均值inline约4,066、tools约1,277，工具返回后的累计输入需要真实日志记录。实际执行已在独立live1中经用户批准并冻结，原草案api_call_authorized=false仍保留；旧批准不自动授予其他运行额度。

## 已实际完成的验证

原生Inspect mock执行：inline57个样本、tools57个样本；全部进入最终旧schema/文件白名单校验，工具条件114次实际Python工具调用，无工具错误。模拟模型生成228次，真实供应商调用0，费用0。脚本模拟最终回答，不将mock的判分报为模型能力。

模拟文本/工具描述输入代理合计514,611，输出申请291,840；这不是真实token，也不是实际API请求预测。凭据见 [MOCK_RECEIPT.json](MOCK_RECEIPT.json)。另核对513条相关历史观测的旧标签，保留失败状态，不修旧分数。2026-10-11最终全仓440项通过；8项新增检查覆盖私有输入隔离、二进制缺口、标签一致性、草案覆盖和重复准备字节一致性。

仓库根目录，沿用 [Inspect环境](../REPRODUCE.md)：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.t1_regression --prepare
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.t1_regression --mock
```

--prepare只允许重复写入完全相同的草案；变动时另起版本。mock日志写入被忽略的work/t1_regression_mock，不覆盖真实运行记录。下一步在T1回归结果检查后锁定新来源模板，方案见 [T3_NEXT_PLAN.md](T3_NEXT_PLAN.md)。
