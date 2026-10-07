# bench v2：规格草案

2026-10-07。状态：阶段2题库草案已构造并在本地校验，修订版r2的Linux回传已验收，用户已确认全题单与门槛，答案和分析规格已冻结；没有v2冻结或模型结果。用户同意上一轮提出的推进方向，随后指定五模型及统一Intern Discovery端点，替代先前三模型/原厂端点草案。脱敏的授权记录与边界见`MODEL_AUTHORIZATION.json`；本阶段不调用模型。

v1完整保留，其16题是已查看结果的回归集。v2当前24题：16道原题+8道新增题；新增题包括6道非施压题和2道施压副本。主比较只用新增集合，回归集合单独报告，不能合并宣称全为未见题。题目均来自已验收的T1拟南芥/线虫/酵母和T3 GFF/FAA；不引入其他项目、不下载数据、不重跑组装/注释或BUSCO。

计划模型为用户指定的`DeepSeek-V4-Flash-0731`、`DeepSeek-V4-Pro-0813`、`MiniMax-M3`、`Qwen3.8-27B`、`Kimi-K2.6`，均通过`https://discovery-api.intern-ai.org.cn/v1`进行B（通用提示）/C2（修订的共用Skill包）比较。A继续只用原规则，覆盖不到记not_covered，不新增规则；A可以复用身份完全相同的原16题结果，新增8题需服务器执行。Kimi-K2.6是新的指定条件，不能继承v1 Kimi-K3的成功率或超时结论。五个名称按用户原文保存，不静默改成原厂别名。

## 文件与阶段门

| 当前文件 | 用途 |
|---|---|
| `CASE_PLAN.md` | 新增8题的来源、候选注入、拟定判定、配对与新旧题边界 |
| `SOURCE_AUDIT.md` | 本地已验收来源的布局与最小可用内容；沿用原清单，不重扫源哈希 |
| `PREREGISTRATION.md` / `preregistration.draft.json` | 新的H1–H3、共同成功指标和人工action编码；效果门槛留空 |
| `MODEL_PLAN.md` / `models.draft.json` | 五模型、待核对的平台参数与计费、调用量公式；不接入v1入口 |
| `MODEL_AUTHORIZATION.json` | 用户新增Pro模型许可的准确记录，不存key |
| `PHASE1_REPORT.md` | 本阶段完成内容、pytest与待决定项 |

用户“好，启动”授权进入构题阶段；预注册5个数值仍待用户填写，不按默认值处理。阶段2已在`bench/v2/`内新建注入、schema、24题、C2、review表及校验；首次任何模型调用之前必须补齐门槛，每题答案经用户确认并在独立FROZEN中记录哈希。随后阶段3冻结v2运行计划、mock流程和费用汇报；用户已允许这五模型/端点，无需重复询问相同许可，但新调用/资源预算上限仍需明确。任何模型调用（包括mock和在线身份探测）均在答案与规格冻结之后。每个阶段独立commit、完整pytest、结束停下。

v2脚本须采用独立bench根目录，不改v1的`models.yaml`、计划、账本、case、context、答案、评分程序或原始结果。禁止通过修改v1环境覆盖或清空账本运行Pro。授权与预算按v2登记，保留v1历史占额与费用记录，不把新版本登记当作重置旧批准额度。

## 主指标与回归桥接

新H1主指标为每题“多数判定可接受且多数根因正确”的共同成功率；两个多数仍独立形成，至少2/3同值。检测率、单独判定/根因正确率仍报告，避免检测率天花板掩盖处置与归因问题。主集合是新增非施压题6道，不要求它们属于新机制；轴一/轴二仍逐题标记并分层。新增题不自动等于not_exposed。

新H1还报告新增两个正常对照的误报变化，建议将“C不能以超过预设限额的新增误报换取共同成功提升”纳入成立条件。限额由用户在预注册填写，不在结果出现后选择。回归16题用于展示已知问题修复与新副作用，不能作为泛化主证据。

本轮正式B/C2均在同一批次重新运行，不能将v1历史B与v2 C2直接当成受控实验；模型版本和服务端点也已变化。C1不在主运行中；旧C1结果作为历史背景。若另加同批次C1桥接，需要事先登记独立条件与调用预算，不能临时拼入。五个模型共同使用一套C2，相同artifact和任务顺序；思考参数需依据统一平台文档冻结，不能假定原厂扩展字段被该端点接受。

## C2修订边界

C2保留C1通用内容，并新增共享原则，逐节登记来源、改写与版本：

- 输入/文件连接或格式无法正确消费时先阻断；已产生且不可靠的分析结果需要回退；可接受的限制与待补证据可警告。具体答案需结合任务的下游用途，不按一个数值机械选择动作。
- 数据库版本根据题目提供的运行日期、项目约定和兼容要求判断，不凭模型内部的“当前最新版”断定过期；版本被固定不免除检查真实不兼容或运行要求违背。
- 覆盖率核对实际查询集合、唯一ID、连接方式与分母；ID不一致不等同真实低质量，也不能未经明确映射任意剥掉后缀。
- 区分CDS片段行数、转录本数、唯一编码基因/蛋白数；多行CDS不自动表示交付缺失，连接缺失则需处理。
- 区分不同统计口径的比例和不同物种背景；将缺少额外指标与已经证明的故障分开表述，正常对照不凭空新增硬门槛。

这些原则是基于v1结果修订的干预，不能包装成原Skill未经改动的能力。原仓库知识文件不改动。C2不含题号、来源项目身份、具体统计、答案、模型反馈或与某一道题对应的样例；也不按题检索知识。v2暴露标签须对照最终C2重做，一般性的连接/口径机制可能已经明确暴露。v1标签保持原样。

## 输入、运输与计分

继续使用模型只读材料的固定packet设计，不增加agentic shell。每题可见输入含任务与产物，约30k token以内，先在构题时固定截取；不能运行途中因模型结果再改材料。统计异常由真实产物变换后重新计算，完整蛋白/完整基因块选择与切片方法在meta记录；配对指定表面字段、task、分母相同。施压副本的artifact字节等同其母题，但不加入配对。

meta/expected/source/audit/本目录设计文档均私有，不能进入B/C请求。禁词扫描沿用v1审核策略；工具原样输出例外私有登记。Windows与服务器输出均LF，构题脚本两边复现一致后才能冻结。正常例使用未修改真实记录的片段，不能伪造完整运行值。

仍每题3次最终观测，格式修复最多1次，不无限补跑网络错误。失败按计划分母保留；正常题无结果与有效误报拆开；根因、判定无多数各自报告。人工action审核与自报flags分开，规则见预注册。所有计数均n/N与百分比，零分母N/A，按集合、模型×组、两轴、阶段、type分层；混合标签配对另列。

## 边界

新实例来自与v1相关的T1/T3来源，不是独立物种/项目外部验证。现有知识包及开发过程已经知道多种机制；新实例不证明预训练或开发过程未见机制。C2仍更长，长度与知识效应未被分离。用户单人答案审核/人工action编码的限制需报告。相同题三次不是三个独立样本，不做把重复当题的显著性检验。

## 阶段2产物与复现

运行`python bench/v2/build_cases.py`构造，`python bench/v2/validate_cases.py`校验；冻结后主题库写入会拒绝。`CASE_INPUTS.json`登记任务、产物、答案、私有标签及规范化meta的哈希，`REVIEW_SHEET.csv`保留每题用户意见；重建不清空已填意见。新题meta使用v2 schema，回归题task/artifact/expected/meta全部复制原字节，仅在私有`v2_labels.json`中登记新case身份与C2暴露轴。模型可见白名单仍只有task和artifacts。

P3按既定梯度最终选32条完整蛋白（源表第65..96条），两题覆盖2/32=6.25%。017同时清空标记和IPR/GO内容；018保留注释内容，将其余终端.tN表达为.transcriptN。P4选原T3的两个多CDS基因块，蛋白记录完整、来源partial=true字段保留；任务只评价文件计数与连接，不把partial模型的生物学完整性宣称为通过。P5使用100001..112000，共12,000 bp，实际418屏蔽位点（3.483333%），不套用全基因组比例。三对分别核对相同task、共同表面统计、来源与不同必要根因证据。

`context/skill_context.md`为C1原字节加共享addendum，修订来源见PROVENANCE。原知识文件不改；新实例的C2暴露均为explicit_rule，不能作为not_exposed泛化证据。

本地构造、语义重算、schema、泄漏、配对、压力克隆及重新构造均通过；最大可见输入保守上界25,921 token。固定转移包由`python bench/v2/package_reproduction.py`生成，只列白名单，不含运行结果/凭据；实际来源包沿用服务器旧包。服务器执行与回传说明见`server/README.md`。Windows解包演练通过，Linux回传已验收，证明见REPRODUCTION_VERIFIED.json。跨主机meta只规范化已验收来源包绝对前缀，所有其它内容及真实来源绑定比较；task/artifact/expected/标签哈希严格相同。

本阶段不创建FROZEN、不调用mock、规则或API。审核表含24题，其中16题字节及旧答案已有v1批准记录；8题新答案需确认。预计的720初始调用仍只是五模型B/C2×24×3的设计量，实际余额/资源上限在后续mock汇报时另定。

## 2026-10-07服务器回传验收

本地接收`incoming/v2_cases_reproduction/bundle`，完整清单170个payload文件通过；MANIFEST.json与用户服务器公布的cb96003d2e6ee1cffbb1c25fdd668b1d7f4bd4895def7d01378f16d58354e0c6一致。服务器Linux/Python 3.9.23，构题代码、24题所有可见文件、expected、标签和规范化meta均匹配Windows参考。未重新扫描原始来源大文件。验收脚本为accept_reproduction.py，证据为REPRODUCTION_VERIFIED.json；VALIDATION的server_reproduction_status更新为pass。答案审核与门槛仍pending，未生成FROZEN或调用模型。

## 冻结前审核修订r2：new_019关键依据

按用户建议保持pass/none/P4，仅将key_evidence中的models.gff3:2替换为models.gff3:protein_id。当前metrics无cds_protein_ids_without_sequence，采用用户的三项依据备选，不新增指标或模型可见文件。所有24题的任务、产物、规范化meta和C2标签哈希不变，仅new_019 expected哈希变化；差异登记在REVIEW_UPDATES.json。partial=true不超出本题文件连接与计数审核范围，不能单独据此判block。

此前Linux验收针对r1，原证明和参考保存于history/reproduction_r1；当前REPRODUCTION_VERIFIED标pending。更新的reproduction_package.zip已在Windows解包复现通过。为符合原跨平台答案哈希一致要求，服务器使用同一来源包对修订版再运行一次，可指定输出bench_transfer/v2_cases_reproduction_r2；不重取来源、不扫描原始大文件、不调用模型。其余答案审核和门槛仍待确认。

## r2回传验收完成（2026-10-07）

完整接收incoming/v2_cases_reproduction_r2/bundle，170个payload文件运输清单通过；24题任务、产物、修订后的expected、标签、规范化meta及服务器构题代码与本地参考一致。Linux/Python 3.9.23，模型调用0。r2复现证据已更新REPRODUCTION_VERIFIED，当前VALIDATION服务器状态为pass；r1历史记录继续保留。当前版本无需再跑服务器复现，逐题审核与5个门槛仍待用户确认，未冻结。

## 阶段2冻结完成（2026-10-07）

用户在“审核表剩余题目及门槛1、0、0、1、1”的确认请求后回复“可以”，按当前r2版本登记全24题批准；REVIEW_APPROVAL记录逐题expected哈希，SPEC_APPROVAL记录C2、meta、两轴标签和采用的分析规格。preregistration.json为正式规格，原draft标已采用，PREREGISTRATION门槛均已填写。单人集中确认是审核方式，不能描述为多位独立标注。

FROZEN.md逐题列24个expected SHA-256，FROZEN.json保护195个本版文件及11个共用依赖；SOURCE_MANIFEST为已验收包清单的原字节副本，没有重扫原始大产物。执行python bench/v2/freeze.py验证，禁止create覆盖或向已冻结主题库重建；validate同时验证冻结。此前CASE_INPUTS、REPRODUCTION_VERIFIED、REVIEW_UPDATES的model_calls/answers_frozen/review字段是构造/复现/修订时点的历史快照，不回改这些原始证据；当前状态以FROZEN、批准记录和VALIDATION为准。

当前不调用mock、API或A规则。阶段3仍需独立v2 harness、提示/参数/适配锁定、mock全流程与输入token/费用或资源上限汇报，然后按既有许可及明确预算执行。固定五模型不变，数值预算没有从本次题目确认中推定；v1配置、账本、代码与结果不变。本阶段到此停下。
