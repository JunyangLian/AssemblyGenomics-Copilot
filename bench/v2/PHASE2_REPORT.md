# v2阶段2汇报：题库草案，等待复现与人工审核

2026-10-07。用户“好，启动”授权推进构题；本阶段模型调用0次、API费用0，没有生成v2 FROZEN。五模型名称/统一端点沿用已授权方案，数值门槛没有代填。

1. 完成内容（全部在bench内）：

- `cases/`：24题。`regression_001..016`的任务、产物、答案与meta复制原v1字节；`new_017..024`包含6道新非施压题和2道压力克隆。
- `build_cases.py`、`inject/functional.py`、`structural.py`、`masking.py`、`pressure.py`：确定性选择与变换，固定seed=0，无模型客户端。
- `schemas/`：v2 meta、expected、model_output及私有C2标签schema；根因枚举与v1一致。回归meta按原schema校验，暴露变化另记v2_labels。
- `context/`：冻结C1原字节加共享C2原则及来源登记。原Skill/knowledge不改，新题均explicit_rule，不宣称未指导机制检验。
- `CASE_INPUTS.json`、`REVIEW_SHEET.csv`、`VALIDATION.json`：哈希参考、逐题审核表、本地校验结果。意见列留空；重新构造保留已填意见。
- `server/`、`package_reproduction.py`、`reproduction_package.zip`、`LOCAL_PACKAGE_REPLAY.json`：最小代码/回归材料转移包、运行说明及Windows独立解包复现记录；服务器使用已验收的旧来源包。
- 8项新增校验测试。README、CASE_PLAN、预注册草案状态与CHANGELOG同步；v1答案/题目/上下文/运行计划保持原样。

2. 验证结果：

- 全仓`python -m pytest -q`：**256 passed in 47.45s**，包含全部原有测试。
- 构题校验PASS：24题schema、真实来源绑定、泄漏扫描、关键依据、配对表面字段、压力母题、实际统计重算及本地字节复现通过。
- 单题可见输入保守上界最大25,921 token；所有新增文本/复制题目为LF。P3从预定64→32→16梯度固定32条真实完整蛋白，2/32=6.25%；P5真实窗口12,000 bp、418屏蔽位点。无伪造全量统计。
- 113文件的独立解包包在Windows演练PASS，24题0差异；Linux复现仍pending。task/artifact/expected/标签哈希严格相同，跨主机meta只规范化来源包绝对前缀，来源origin与其余字段均比较。
- v1冻结及运行计划验证PASS；未改原仓库分析脚本。转移包哈希见`server/PACKAGE_RECEIPT.json`。

3. 缺口与需要用户决定的事项：

- **人工审核**：请填写REVIEW_SHEET的“我的意见”，重点审new_017..024。原16题沿用已批准原字节，v2暴露轴另列，整个v2题单仍待批准。建议逐题明确“通过”或修改理由；不将“真实来源无误”自动当成处置答案已审核。
- **new_019范围**：真实多CDS记录带partial=true，保留全部标记。拟pass针对文件连接与计数；任务明确不评价模型生物学完整性。建议在此范围内接受pass；如希望部分模型一律warn，可在冻结前明确接受判定并登记，不能在模型结果后改变答案。
- **预注册门槛**：五个数值仍空，建议1、0、0、1、1（共同成功增量、最多新增误报、最多危险题、最低区分对数、区分增量）。仅在用户明确填写/采纳后登记；至少两模型方向一致仍固定。
- **Linux复现**：把reproduction_package.zip上传至服务器bench/v2，按server/README运行并用scp传回整个`bench_transfer/v2_cases_reproduction/bundle`。本地验收回传结果后才能记跨平台通过。
- **模型运行**：本阶段没有调用mock、在线探测或API。答案审核、门槛确认与独立冻结之后进入阶段3，先mock并汇报token/资源预算；五模型全B/C2设计为720初始请求，实际平台参数/资源上限仍需登记，不能借用v1余额假设。

本阶段到此停下；没有发布任何v2模型表现或假设结论。

## 2026-10-07回传验收补充

已接收用户指定的incoming/v2_cases_reproduction/bundle，完整运输清单170个payload文件通过，MANIFEST.json匹配用户公布的服务器哈希。24题可见文件、expected、C2标签、规范化meta、参考清单及12个构题代码文件哈希均一致；Linux/Python 3.9.23。接收证明写入REPRODUCTION_VERIFIED.json，VALIDATION服务器复现更新为pass。新验收脚本拒绝不符的运输哈希、假报Linux、答案/来源origin被改但重写清单的包；五项验收测试加入全仓检查。

本次完整pytest：261 passed in 54.91s；v1冻结/运行计划仍PASS。人工题目审核和5个门槛仍待确认，无标准答案修改、无v2 FROZEN、0模型调用。此补充属于阶段2验收，不进入阶段3。

## 冻结前人工审核修订r2

new_019维持pass/none，仅把关键依据models.gff3:2改成models.gff3:protein_id，采用用户在缺少cds_protein_ids_without_sequence字段时给出的三项备选。没有增加metrics字段。确定性生成器、CASE_INPUTS、REVIEW_SHEET与REVIEW_UPDATES已同步；核对24题的task/artifact/meta/标签哈希全部不变，仅该题expected哈希变化。原partial=true保留，本题限定文件连接与计数，不按生物学完整性阻断。

完整pytest：262 passed in 57.59s；v1冻结与计划验证PASS。r2 Windows独立解包复现24题零差异，新包已准备。r1真实Linux验收和参考存档于history/reproduction_r1，当前服务器复现标pending而不是沿用旧答案哈希。按server/README在新输出目录v2_cases_reproduction_r2补跑即可；无需重取数据或扫描原始大文件。当前仍无v2模型调用或冻结，其他题与五个门槛待用户确认。

## r2回传验收完成

2026-10-07收到incoming/v2_cases_reproduction_r2/bundle：170个payload文件运输清单完整；24题任务、产物、修订后的expected、标签、规范化meta及12个构题代码哈希与Windows参考一致，Linux/Python 3.9.23。MANIFEST.json哈希由传回的MANIFEST.sha256核对，完整payload再独立对照本地草案，不冒充用户已在消息中公布该哈希。验收写入REPRODUCTION_VERIFIED，VALIDATION服务器状态为pass，r1档案保留。

完整pytest：262 passed in 58.27s；v1冻结/运行计划PASS。未修改任何题目、答案或C2，模型调用与费用0，未创建v2 FROZEN。当前版本不再需要服务器复现，下一步仅待用户完成剩余答案审核及5个预注册门槛确认；阶段2继续停在审核处。
