# v2 阶段3汇报

2026-10-07。用户“可以”授权本阶段；随后答复“没有，先看 token 估算”，本阶段完成mock与资源报告，停下等待下一阶段/真实执行预算确认。

1. 完成文件：runtime.py、plan.py、RUN_PLAN.json/sha256、models.yaml、adapter.py、run.py；mock_report.py、MOCK_RUNS.json、MOCK_REPORT.md/json、API_APPROVAL.template.json；rules_package.py、RULES_PACKAGE.json及可传输rules_package.zip、server/run_rules.py、import_rules.py、A_REUSE_RECEIPT.json；tests/test_v2_harness.py、HARNESS.md、CHANGELOG.md，更新README/MODEL_PLAN/.gitignore。所有改动在bench/v2。24题答案与规格仍受原FROZEN保护，没有修改；原v1计划、规则和账本验证不变。

2. 完整pytest：**278 passed in 76.99s (0:01:16)**。新增11项检查覆盖公共输入/C2一致、私有内容排除、格式修复1次且无答案反馈、重复键/越界证据拒绝、网络错误不重试、批准前不读key、累计预留/重启不重置、供应商越额标记、型号不符拒绝、A身份/缺失重复槽位、服务器固定输出及路径逃逸拒绝。测试中的服务器演练使用明确测试替身，未作为真实A观测。真实Linux复现仍沿用已验收r2，不重新扫描原始来源。

3. 实际运行：**720次mock、0 API调用、0最终parse_error**；720条B/C2模型观测和72条明确模拟A运输记录，11个运行目录。48条真实v1 A已核对可复用（27 ok、21 not_covered），0新规则执行；新增24条真实A等待用户运行服务器包并回传。mock未检验QC能力，未判定H1–H3。原始记录含请求摘要/响应/解析、usage=null与实测耗时；输出文件LF。

4. token规划与待决定项：

| 情景 | 调用次数 | 输入代理 | 输入字节规划上界 | 输出 |
|---|---:|---:|---:|---:|
| 初始请求；每次输出1000是假设 | 720 | 4,810,530 | 14,292,540 | 720,000 |
| 初始请求；完整8192输出请求限额 | 720 | 4,810,530 | 14,292,540 | 5,898,240 |
| 每个初始请求都格式修复1次；完整输出请求限额 | 1,440 | 9,669,300 | 28,706,760 | 11,796,480 |

每模型144初始/最多288次；B平均输入代理3,571.1、C2为9,791.5（2.74倍）。计算为消息UTF-8字节/3向上取整+64+16×消息数；字节规划上界为消息字节数+同一开销。这不是实际供应商用量，平台隐藏包装、思考token和限额计量未核对；max_tokens请求值不保证覆盖全部隐藏资源。

- **费用缺口**：统一平台无五模型计费/墨点权重，用户也暂无说明，正式运行费用仍未知，不借用原厂单价。本次外部调用费用0来自没有API调用。建议先审阅上述估算，再明确允许的调用次数、累计输入/输出规划预留上限；若要保证货币上限，先取得平台计费资料。
- **请求协议待审阅**：五模型名称按用户原文，平台未认证可用性；统一temperature=0、max_tokens=8192、stream=false，默认思考unknown，不发送未证实支持的扩展字段。不声称实际参数生效。建议接受此限制后执行已登记的初始请求，或先提供平台参数/ID资料，再登记新运行版本并重跑mock。不得结果出现后静默改参数、降级别名或修改标准答案。
- **真实A仍缺回传**：将rules_package.zip传到服务器bench/v2，按HARNESS.md运行，回传bench_transfer/v2_rules_run_1/bundle。原脚本随包携带，避免旧布局错误；无API/key/答案/meta。规则只覆盖执行日志显示的范围，不新增规则迎合新题。
- **阶段4未进入**：报告计分与人工action编码将在下一阶段进行。本次保留答案、C2、预注册和原结果；用户审阅后再推进。

运行计划SHA-256：84fab8e1221048662e61349d788ba7e858be1e9432fa955206d2f2b93f42b417。
答案冻结SHA-256：b30dee32bf94c9c36ebe8f55b4f177205021685ce60623500dbecb92fd393188。
## 六模型修订阶段汇报（2026-10-08）

完成：SIX_MODELS_REVISION.json、PROVIDER_MODELS_SIX.json、预注册修订附录、register_six.py、revision_snapshot.py；plan/parallel支持六模型六请求并发，mock_report/api_progress动态864槽位，README/HARNESS/CHANGELOG更新。父运行history/v2-run-6保留全部229条观测；旧Qwen144条仅审计，四模型85条承接。Qwen FP8按用户确认独立标注，Kimi加入，数字门槛及冻结题库不覆盖。

验证：完整python -m pytest -q为300 passed in122.88s；mock864次全部解析成功、峰值6；冻结195文件/11依赖通过；本机环境凭据泄漏扫描通过。原48条A身份复用，新24条A包更新计划绑定。

真实队列按已批准授权启动，六不同模型同时在途。预算仍1440调用/28706760输入预留/11796480输出预留，旧543次预留保留；全修复1728次超过原上限，实际按余额停止。不把未知费用当0；暂未全部完成或开始阶段4计分。新主体实际调用前的名单/并发修订及模型分母变化另行披露，无新增待批准事项。
## 第二凭据恢复阶段汇报（2026-10-08）

完成：credential_recovery.py、register_credential_recovery.py、CREDENTIAL_RECOVERY.json、凭据变更收据/预算提案和预注册事后附录；history/v2-run-7保留原864条结果。resume/ConcurrentBudget仅对全部623条最终HTTP429允许一次人工批准的恢复，其余241原样承接；adapter仅接受登记的新增累计上限，不通用放开限制。新429停止派发并等待在途结束，待运行槽位保留。模型、提示、参数、题库、答案和C2未变。

验证：最终python -m pytest -q为306 passed in143.56s；最终mock864次全部解析通过、峰值6；冻结195文件/11依赖通过；第二个key仅在本机环境，新响应/日志泄漏扫描通过。原48条A复用，新24条A包仅更新身份。

执行：用户批准全部623条429恢复及所需累计预算2636/52724811/21594112，保留旧1390次预留。第二key真实六并发已启动，首检查点取得有效响应，尚未全部完成；原始与恢复队列分别报告。HTTP429原因未由正文确认，费用/账户墨点仍未知；无需再次批准已授权范围。
## 第三凭据、四模型优先阶段汇报（2026-10-08）

完成：register_priority.py、PRIORITY_FOUR_REVISION.json、CREDENTIAL_RECOVERY_THIRD.json、第三凭据变更收据和事后附录；父history/v2-run-8完整保存376观测。parallel仅派发四个active模型，GLM31/Kimi39观测保留而不调用；credential_recovery逐槽位核对原/最新429祖先与重复预留；api_progress区分四模型576目标和六模型864总目标。README/HARNESS/CHANGELOG更新。

pytest：最终python -m pytest -q为308 passed in149.77s。mock864次全解析通过，峰值4、API调用0；冻结195文件/11依赖通过；第三key环境泄漏扫描通过。原48条A继续复用，新24条A包只更新运行身份。

真实执行：第三key四并发已启动并获得有效响应，GLM/Kimi新增调用0。四模型已有305条结果承接，剩271条恢复调用，累计预算沿用已批2636/52724811/21594112，不退还旧1578次预留、不增加预算。答案/知识/参数/数字门槛不改；暂停两模型尚不完整，不能宣布六模型主分析完成。无需新增批准；新429会自动暂停。
## 第四凭据续跑阶段汇报（2026-10-08）

完成：register_priority支持明确第四凭据继续配置；CREDENTIAL_RECOVERY_FOURTH、PRIORITY_FOUR_CREDENTIAL4、第四凭据收据与事后附录新增。父history/v2-run-9完整保存609观测/1911预留；38个Vision/MiniMax恢复槽位登记，其余608承接。Pro/Qwen各144已结束、GLM31/Kimi39保留暂停，不新增调用。README/HARNESS/CHANGELOG与阶段报告更新。

pytest：python -m pytest -q最终309 passed in196.67s。mock864次全部解析通过，峰值4、API调用0；第四key泄漏扫描通过；冻结题库195文件/11依赖及原48条A身份复用验证通过。新24条A包只更新运行身份。

执行：第四key真实队列已启动，仅Vision/MiniMax有待调用槽位，实际峰值2。累计2636/52724811/21594112额度沿用、不增加或退还旧预留；题目、答案、提示、模型参数和数字门槛不变。新429仍自动暂停，原始与恢复队列分别报告；四模型尚未结束，暂停两模型更不能标为六模型主分析完成。无需新增批准。
