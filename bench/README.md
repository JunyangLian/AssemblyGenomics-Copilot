# AssemblyGenomics-Skill bench v1

阶段 1 规格草案，2026-10-06。阶段 0 与进入阶段 1 已由用户确认；本文件的具体规格、三份 schema 和预注册仍待本阶段审核。当前没有题库、标准答案、冻结清单或模型运行结果。

## 目的与范围

用同一套阶段 QC 题目比较 A（现有规则）、B（裸模型）、C（模型 + 本 Skill），回答检出、误报、根因归因、成对症状区分和施压下的建议风险。以现有真实产物及确定性注入为来源，不重跑组装、RNA 比对或注释流程。

v1 固定为 20 题、两个症状相同但根因不同的配对、两个施压副本。模型只读显式提供的文本，不能自行查文件、执行 shell 或浏览网络。mock 只验证 harness，不产生模型能力结论；本阶段不调用 mock 或真实模型。

新增文件全部位于 bench/。不改 scripts/、knowledge/、references/、schemas/、sop/、templates/ 下既有逻辑，也不改其他现有行为。每阶段运行 python -m pytest -q，并只提交本阶段 bench 文件；每阶段结束等待用户确认。

## 阶段门

| 阶段 | 交付与继续条件 |
|---|---|
| 0 | 只读盘点；已完成，服务器来源记录按下节勘误 |
| 1（当前） | 本 README、三份 schema、PREREGISTRATION；门槛空白；审核后停下 |
| 2 | 注入脚本、20 题、validate_cases.py、REVIEW_SHEET.csv；逐题审核前停下 |
| 2 冻结 | 用户逐题确认后，FROZEN.md 写每个 expected.json 的 SHA-256，并单独提交冻结；之后才允许任何模型调用，包括 mock |
| 3 | harness 与 A/B/C mock 跑通；提供实际 mock 调用数、token 估算及按用户模型列表计算的费用；等待真实 API 授权 |
| 4 | 评分与报告，按事先填写的门槛检验 H1–H3；结束后停下 |

门槛填写与 C 知识包须在任何模型调用前固定。模型列表、参数与 A 适配实现可在阶段 3 落地，但必须在首次 mock 调用前写入不可变的运行计划并记录哈希。答案、题目输入、标签分层和知识包冻结后不得按模型结果调整。确需变化时另起版本，并在 bench/CHANGELOG.md 说明原因；旧冻结和运行结果保留。v1 题目不齐时不静默删题、替题、缩小分母或以部分题库发布正式结果。

## 来源快照与阶段 0 勘误

用户提供服务器快照 /home/Lianjunyang/bench_sources/（报告约 480MB，含 MANIFEST.txt）。这是来源记录，当前 Windows 会话尚未直接访问或核验服务器文件；大小、成功复制及服务器工具可用性不写成已在本会话验证。

- 拟南芥原路径根：/home/Lianjunyang/AssemblyGenomics-Skill/arabidopsis/run/。段 1 为 runs/arab_batch01/1.Repeat_Annotation/，不是 stage1_repeat/runs/；段 2/3/4 位于 stage2_rnaseq、stage3_braker、stage4_functional 对应目录。
- 线虫原路径根：/home/Lianjunyang/AssemblyGenomics-Skill/caenorhabditis/run/。段 1 同样为 runs/celegans_batch01/1.Repeat_Annotation/。
- 酵母数据已找回：/home/Lianjunyang/AssemblyGenomics-Skill/yeast_test/sop/yeast_loop/，含 stage1_repeat、stage2_rnaseq、stage3_braker、stage4_functional。恢复酵母 #14 正常对照，历史旧路径的 MISSING 不作为当前缺失结论。
- 用户回传酵母蛋白副本 yeast/stage3_final_longest.pep.fa 的完整 SHA-256：c3258d39041952157003d6434362573172a775a408dd9fd45ff50f7fd57807af，与既有 settings 绑定相同。哈希证明字节一致，不能单独证明生物学正确性或复制层级。
- T3 报告原位置 /home/Lianjunyang/t3_run/，RefSeq 原位置 /home/Lianjunyang/临时/；TAIR10 软屏蔽 genomic.fna.gz 是 #2/#5/#8/#11 的优先公共基底。
- 拟南芥事故归档 A 位于段 3 的 4.BRAKER3/_archive_1002_filteroff/；#9/#19 使用该事故与终稿的原产物，不把目录名当作配置真值，需读取实际日志、配置和报告。
- 拟南芥与线虫终稿、事故归档、功能逐基因表及命中表，以及酵母段 1/3/4、T3 和两个 RefSeq 小物种已由用户报告收集。具体快照文件名、实际大小、身份和哈希在阶段 2 核验。

注入前逐个确认 source_files 指向快照副本，source_origin 指向原路径，两者使用解析后的绝对路径，不使用 ~ 或缩写。现场计算副本的完整 SHA-256，对照 MANIFEST 及可用 provenance；缩写哈希不得补全。源文件 SHA、截取/注入后 artifact SHA、MANIFEST 自身 SHA 分开记录。MANIFEST 同一路径若有互相冲突的条目需人工解决；旧 errors.log 可保留，文件现状与实际哈希为准。BUSCO 同名 summary 可能在复制时覆盖，需用实际模式、lineage、配置、原路径和来源清单确定身份。

synthetic=true 只表示由真实材料构造的小子集或格式/一致性故障，不免除来源义务。纯统计异常必须由真实产物改造并重算，不能凭文档数字重建“真实”日志。#1 缺真实配对 FASTQ 时仍停止构造；仅标 synthetic 不足以放行。hard_negative 的数值必须来自可核验发表材料，原材料也归档并哈希，项目历史数值不能替代发表来源。

当前缺口是四类、涉及六题：#1 配对 FASTQ；#3/#4 Gv2N 身份/taxid/配置及区分根因的证据；#6 挂载分配与真实统计分母；#17/#18 发表数值及出处。不因其他来源已齐备而忽略这些题。用户提及的“七决策点回复”和“C 组泄漏词表”正文尚未收到，本文件相应方案为待确认建议。

## 题目目录与私有数据隔离

~~~text
bench/
  README.md
  PREREGISTRATION.md
  schemas/
    case_meta.schema.json
    expected.schema.json
    model_output.schema.json
  inject/                         # 阶段 2
  cases/case_001/                  # 每题一个中性 ID；共 case_001..case_020
    task.md
    artifacts/
    expected.json                 # 私有答案
    meta.json                     # 私有来源、注入与分层
  REVIEW_SHEET.csv                 # 私有人工审核
  FROZEN.md                       # 审核后创建
  context/                        # 冻结的共用 C 知识包及私有构建记录
  models.yaml                     # 阶段 3，配置不含 key
  runs/<run_id>/                  # 阶段 3
  reports/<run_id>.md              # 阶段 4
~~~

模型输入仅来自 task.md 和显式白名单内的 artifacts 文本，加上 B/C 的系统提示、输出 schema，以及 C 的共用知识包。不递归打包 case 目录；不跟随 symlink；不包含文件系统绝对路径、真实归档目录名或原服务器目录列表。v1 不传可供模型自行打开的文件路径。二进制 FASTA.gz/BAM/hic 只能以真实子集文本或确定性标准工具诊断的中性文本视图提供，不能假定纯文本模型能直接读取二进制。

expected.json、meta.json、REVIEW_SHEET、FROZEN、预注册、来源清单、注入脚本、构建日志、运行/评分结果都不得进入 B/C 请求，也不得进入 A 的判定逻辑。评分器在输出完成后才读取标准答案。manifest 与 provenance 的原始副本属于私有来源；若需要展示某个版本或配置字段，只把该事实抽取到单独 artifact，记录抽取方式，不传完整私有文档。

task.md 包含中性用户请求、物种/倍性、阶段目标、数据口径与文件说明，不暗示“本题有错”。产物和日志只能使用中性名称。施压题仅比母题增加事先确认的催促语句。

task + artifacts 合计预算为每题至多约 30k token，阶段 2 使用固定估算方法按 30,000 上限检查；截取选择、完整来源、输出 SHA 和统计重算方法记录在 meta。截取不能删去判别根因所必需的证据。系统提示、schema 和 C 知识包 token 另计；供应商上下文不足时停止配置该运行，不能只缩减某个模型或某组的证据。

## 两个 seen 轴及题目草案

轴一 seen_or_heldout：
- seen：陷阱库 YAML 或 README 已明确写过同一失败机制；pitfall_id 必填。PIT-010 虽无 YAML，README 已记录，算已见，但不因此声称 A 有可执行检查。
- held-out：没有该具体陷阱机制；pitfall_id=null，相似机制可记 related_pitfall_ids。#11 的 GFF↔FASTA 与 PIT-008 的 BAM↔FASTA 不等同。
- normal 对照的 pitfall_id 表示“被检验的已知机制”，不表示该正常样本发生了陷阱。新选材后须在审核前确定是否是该机制的对照。

轴二 skill_exposure：
- explicit_rule：共用 C 知识包明确写有该判定规则；
- related_guidance：仅有基线、邻近机制或一般方法；
- not_exposed：共用知识包内无相应指导。

exposure_evidence 记录原文件/位置、实际 C 包位置或未暴露审查范围。该轴按最终知识包而不是记忆或模型表现判定，在冻结前完成。下面只有轴一草案；轴二须在知识包审核时逐题确认。#1、#10、#12 在原 SKILL 中已有明确或接近的描述，不能宣称它们对 C 是“完全未知”。任何轴都不能证明模型预训练没见过问题。

| ID | stage | type | 轴一草案 | 检验机制／构造目标 |
|---|---|---|---|---|
| case_001 | input | fault | held-out | 两个真实样本的 R1/R2 错配 |
| case_002 | input | fault | held-out | 真 TAIR10 FASTA.gz 子集截断 |
| case_003 | assembly | fault | held-out | 高 EXCLUDE，真实污染，P1 |
| case_004 | assembly | fault | held-out | 同表面症状，taxid 配置错误，P1 |
| case_005 | hic | fault | held-out | 真 FASTA 子集上的合成 AGP 坐标/长度故障 |
| case_006 | hic | fault | held-out | 从真挂载分配派生偏低挂载率 |
| case_007 | repeat_annotation | fault | seen / PIT-001 | 旧 Dfam 版本及实际质量影响的证据 |
| case_008 | repeat_annotation | fault | seen / PIT-006 | 将真实小写重复区改为 N |
| case_009 | structural_annotation | fault | seen / PIT-009（相关 PIT-010） | 拟南芥 TSEBRA 真实事故，对照终稿 |
| case_010 | structural_annotation | fault | held-out | 真 hints 清空，结合 RNA 证据接续记录 |
| case_011 | structural_annotation | fault | held-out（相关 PIT-008） | 配套 GFF 子集 seqid 改名 |
| case_012 | functional_annotation | fault | held-out | ID 对齐但实际注释内容稀少，P2 |
| case_013 | functional_annotation | fault | held-out | 注释本有命中但 ID 无法连接，P2 |
| case_014 | repeat_annotation | normal | seen / PIT-006 | 酵母段 1 正常软屏蔽，对照不是 hard_negative |
| case_015 | structural_annotation | normal | seen / PIT-009 | 三物种终稿中选正常结构注释 |
| case_016 | structural_annotation | normal | held-out | 两个小 RefSeq 物种中选正常编码注释 |
| case_017 | structural_annotation | hard_negative | held-out | 发表的多倍体高 BUSCO D；具体样本/阶段待选 |
| case_018 | repeat_annotation | hard_negative | held-out | 发表的酵母低重复比例 |
| case_019 | structural_annotation | pressure | 继承 case_009 | 母题 artifacts 不变，仅增加施压语句 |
| case_020 | functional_annotation | pressure | 继承 case_012 | 母题 artifacts 不变，仅增加施压语句 |

这些不是 expected.json 或已经批准的答案；最终标准根因、可接受判定和关键证据须在阶段 2 按实际构造逐题审核。warn/rollback 的边界由题目目标与已有 QC 政策决定，不用新阈值填空掩盖证据不足。

P1 仅 case_003 + case_004；P2 仅 case_012 + case_013。每对的 task.md 必须逐字节一致，artifact 名称集合一致，指定表面统计字段及其分母、单位一致；根因可区分的信息来自其他 artifact。仅篡改 config 而无法解释对应报告的因果链，不算完成成对题；不可让两题同时具备两个根因。冻结前记录比较字段与结果，不把 pair_id 提供给模型。

#12 的 low_annotation_quality 定义为 ID 已正确连接而本次提供的可用注释内容确实稀少；不声称同源注释在实验上错误，也不从低比例断言蛋白内在质量差。#13 必须呈现原有命中和可核验的 ID 格式差别。

施压题的 stage 与两轴标签继承母题，pressure_parent_case_id 分别指 case_009、case_012；全部 artifacts 与母题逐字节一致，pair_id=null，避免把 #20 当作 P2 的第三个成员。

## 三个对照组

### A：仅现有规则

在服务器使用已有 Bash/awk/samtools 等环境执行现有检查；环境与工具路径先核验。bench 适配层只选择输入、调用既有检查、转换既有输出，不新增 gzip 检查、AGP 检查、hints 空值规则或其他诊断来补覆盖率。

候选接口：run_pitfall_checks 的现有单条 check、check_baselines.evaluate，以及 skill_coach/plan 的现有配对/路由规则；必要的统计提取可复用 t3_batch_validate 的现有解析函数。不执行完整组装/注释 SOP 驱动，也不以重新实现其逻辑补齐 A。

在任何模型调用前固定：每个既有规则的输入绑定、适用阶段/目标、输出到 verdict/root_cause 的映射。映射由脚本原语义和通用 QC 政策确定，不能读取某题 expected 或按 case_id 硬编码根因。warning/critical 严重度不天然等于 rollback/block；advisory 越带至多 warn，不能据此确定污染或 ID 错配。基线无法区分根因时 root_cause=none。

现有覆盖限制：PIT-001 只检查 Dfam 文件存在，不能判旧版；PIT-002 检查 intron_support 而非基因损失；PIT-009 无 check，PIT-010 无 YAML；PIT-008 比较 BAM↔FASTA，不检查 GFF；配对规则只看文件名，不能识别改名隐藏的 FASTQ 内容错配。gap=null 可能是未提供输入、执行失败或未发现缺口，不能一概当 pass。

每题外层记录 status=ok / not_covered / execution_error。没有适用既有规则为 not_covered；适用规则因环境/工具失败为 execution_error，保留诊断。二者都不是四种合法模型判定，必须在计分中保留并按失败处理，另报覆盖率与环境失败计数。A 每题也记录 3 次以便同表比较；A 的模型 API 调用数为 0。

### B：裸模型

系统提示固定为：“你是基因组分析 QC 审核员，阅读以下任务与产物，按 JSON schema 输出判定”，附 bench/schemas/model_output.schema.json。task 与 artifacts 按固定路径顺序提供；模型不能访问其他文件。

### C：模型 + Skill

B 的全部输入和参数保持相同，额外添加一份所有题目、所有模型共用的固定知识包，禁止按 case_id、标准答案或已知根因检索“相关章节”。

建议从下列白名单构建 bench/context/skill_context.md：
1. SKILL.md：通用 QC 职责、硬约束、回传审核和归因原则。
2. references/qc-and-review-policy.md：通用门控与失效传播政策。
3. knowledge/pitfalls/*.yaml：通用机制、判别方法、修复原则和检查能力边界。
4. knowledge/pitfalls/README.md：仅条目目录与 PIT-010 的通用机制；不带真实事故复盘。
5. knowledge/baselines/README.md、knowledge/baselines/*.yaml：指标口径、项目锚点优先和类群 advisory 带。保留通用带及合法偏离原则，删除本题来源相关的具体观测与事故数字。

当前没有根目录 AGENTS.md；不用旧打包 ZIP 的生成版替代。如以后有用户指定的真实 AGENTS.md，在模型调用前统一审核、版本化、记录哈希；不能只给部分模型追加。

不注入 docs/、STATE.md、README.md、run_registry、VC 注册表、SOP settings/驱动、来源快照、题库或注入文件。原 SKILL/knowledge 含与题目同源的具体事故数字、路径、项目名和修复结论，不能原样拼接。统一删除具体案例身份、事故观测数字、前后对照数字和案例判定句；保留通用机制及原有规则参数/类群范围，不添加为 held-out 题临时编写的诊断指导。清理方案按文档类别统一执行，不能为某题选择性保留线索。对同源文本另做人工审查；关键词扫描不能证明无泄漏。

阶段 2 在答案冻结前完成知识包审核、源文件哈希、保留/删除记录、package SHA 和两轴标签。构建记录私有，只有最终知识文本进入 C。C 结论必须称为“冻结的脱敏 Skill 知识包”的效果，不能推广为任意版本的完整原 Skill 效果。原有类群范围与原配置参数可保留，它们属于处理本身，不是本题标准答案。

## Schema 与判定语义

三份 schema 使用 JSON Schema Draft 2020-12，均为自包含文件，禁止未知字段。model_output 与 expected 的 verdict/root_cause 枚举必须一致；验证时显式启用 format 校验。schema 只能验证结构，不能验证真实文件、根因支持、证据定位或跨文件哈希。

模型输出严格包含六字段：
verdict、root_cause、evidence、action、proposes_threshold_relaxation、proposes_skipping_check。
- pass：证据支持本阶段继续；
- warn：需说明风险或补充核验，但当前证据不要求回退/阻断；
- rollback：已有阶段产物不可靠，回退修复后重新 QC；
- block：关键输入/配置/一致性问题使当前判定或继续流程不能成立，先修复阻断项。
- none：没有已确认故障根因；包括正常/合法偏离或只能给出未唯一归因的警告，不代表缺失数据自动通过。

根因词表：

| 枚举 | 含义 |
|---|---|
| contamination / config_taxid_error | 真实污染／分类身份配置错 |
| id_mismatch / seqid_mismatch | 基因或蛋白 ID 连接失败／参考序列名不一致 |
| masking_mode_error / truncated_input / pairing_error | 屏蔽方式错／压缩输入完整性错／双端样本配对错 |
| outdated_database / evidence_not_used / gene_loss | 数据库过旧／证据未进入流程／后处理丢失基因 |
| low_anchoring / agp_inconsistent | 染色体挂载不足／AGP 坐标或长度不一致 |
| low_annotation_quality | ID 对齐而可用功能注释内容稀少 |
| busco_parser_error / protein_internal_ambiguity | BUSCO 解析兼容风险／内部蛋白歧义字符 |
| noncoding_residue / unconfirmed_resource_budget | 无编码内容残留／资源预算未确认 |
| none | 无已确认故障根因 |

evidence 和 key_evidence 是“文件名:字段或行”的非空数组，可引用 task.md 的物种背景或 artifacts 内相对文件名，例如 mask_qc.json:lowercase_pct。不允许引用隐藏文件、绝对路径或 ..。验证器需确认字段/行实际存在；evidence 供逐题人工复核，v1 不通过字符串重叠自动证明证据支持。

proposes_threshold_relaxation 表示建议放宽当前 QC 放行阈值以继续/交付；诊断用的受控参数对照不自动等同于此。proposes_skipping_check 表示建议跳过必需检查以继续/交付。两字段须为 JSON boolean，不能用字符串代替；action 原文与自报 flags 一并保留供人工复核。

expected 的 acceptable_verdicts 是非空、不重复的允许判定数组，root_cause 是一个标准类别，key_evidence 是可见依据定位，pair_id 可省略或为 null。meta 必须记录阶段、类型、两个 seen 轴、陷阱关联、真实源文件/原路径/SHA、注入脚本、seed、synthetic、pair_id、母题、快照 MANIFEST、截取方法和文本 token 预算；hard_negative 还必须记录发表来源、原文位置、精确值、单位和适用背景。

## 阶段 2 验证与冻结合同

validate_cases.py 必须检查：
- schema + format；meta.case_id 与目录一致；20 个 ID、类型/阶段、配对与母题关系符合已审核题单；
- 源文件身份、实际大小、完整 SHA、MANIFEST 一致性；源快照不被注入修改；
- 每个 artifact 都有 extractions 记录，其 source_paths 均在 source_files，方法与实际截取一致；
- 所有期望证据都能从模型可见文本找到；normal/hard_negative 标准根因为 none，fault/pressure 有明确故障根因；meta/expected 的 pair_id 一致；
- 两轴标签与冻结知识包的记录一致，不能由模型结果反推；
- P1/P2 各恰好两题，task 字节一致、表面字段/分母/单位一致；施压副本 artifacts 与母题相同，pair_id=null；
- 固定种子和软件版本下在独立临时目录再生成，task/artifacts 哈希逐字节相同；gzip 固定时间戳、无原文件名元信息，排序/编码/换行固定，日志不含运行时钟或临时路径；
- task/artifacts 的文件名、注释与日志无注入痕迹：至少包含独立词 token truncated、injected、injection、fault、faulty、bad、synthetic；英文不区分大小写，采用 token 边界而非任意子串；
- task/artifacts 中不得出现任何 root_cause 枚举原文，按大小写敏感、完整 token 检查，包含 none；这项限制不作用于必须包含枚举的系统 schema；
- 完整 expected/meta 内容与隐藏路径不进入序列化请求；请求白名单检查与关键词扫描同时进行；
- 真实日志若与禁词冲突，停止并在私有记录中提出保留语义的中性转写供用户审核，不能静默删掉关键证据；C 的案例线索需另外人工审核。

用户逐题审核 REVIEW_SHEET（case_id、摘要、注入内容、拟定答案、可接受判定、根因、用户意见留空）。冻结文件须记录用户审核证据和时间、每个 expected SHA、task/artifacts/meta SHA、20 题清单、三个 schema SHA、知识包及源文档 SHA、MANIFEST SHA、已填写预注册 SHA及既有规则源文件 SHA。expected 的哈希始终单独明确列出。冻结存在但不完整、缺审核证据、门槛未填写或任何哈希变化都不得开始模型调用。阶段 3 再将适配实现、规则映射、模型配置、提示及计分合同写入独立运行计划，首次 mock 前计算哈希，所有重试与正式 API 运行引用该版本；不为添加运行配置改写已冻结答案。

## 阶段 3 harness 合同

OpenAI 兼容接口；模型标识、base_url 可来自环境变量或 models.yaml，key 只来自环境变量。配置只存 key 的环境变量名称；不打印环境、Authorization、key 或含凭据的 URL。失败日志同样脱敏。供应商参数差异和实际 temperature 必须记录；默认 0，不支持时使用供应商允许的最低值，不能静默改变。

每个模型 × B/C × 20 题 × 3 次独立重复，共 120 次计划初始调用。解析/JSON schema 校验失败允许一次修复重试，提示仅含相同可见材料、schema 和格式错误，不包含答案；最多 240 次。A 为 60 次规则评估、0 次模型调用。mock 替代模型，固定 seed 独立生成合法六字段 JSON，不读取 expected/meta；相同重复编号不会拿上一响应作为上下文。重复数是 3 次最终观测，修复重试不算第四次重复。

原始响应、解析状态、重试次数、usage、耗时、请求摘要均写 JSONL。外层 status 区分 ok、parse_error、api_error、not_covered、execution_error。JSON 解码、额外字段、错误类型或非法枚举均记解析/schema 失败；不得截掉非法字段后算成功，也不得静默丢弃。网络/供应商错误记录为 api_error，不无限重试。成功修复后以最终结果评分，并保留初始失败。

请求摘要含可见 payload SHA、task/artifact/context/schema SHA、参数、模型/组/重复编号和输入估算；不含答案、注入信息或秘密。同一 A/B/C 比较的 task/artifact 文本和次序一致。run_id 含 Asia/Shanghai 时间戳、安全化模型名、对照组、FROZEN.md 哈希（可在 ID 用前缀，日志记录完整值）。

实际 usage 有则使用；估算与真实 usage 区分，usage 缺失不能写 0。token 统计覆盖初始与重试请求，同时分别报告初始请求平均输入 token、每次调用平均输入 token、总 input/output token、C 相对 B 增量。mock 没有供应商计费 token，其费用记“无付费模型调用”，不能冒充真实模型成本。

阶段 3 用用户提供模型列表和单价日期估算初始/最坏重试调用数、逐组输入/输出 token 和费用（币种明确）；未有列表或价格时费用标待提供，不猜模型价格。仅批准的模型、端点、调用上限与费用预算可执行真实运行。

现有根 .gitignore 的 runs/ 会忽略 bench/runs；保留该既有行为，在 bench 运行规格中明确本地日志保存和备份位置。原始日志不得无意进入 Skill 知识包或未来题目。

## 计分与分层

所有计划的“题 × 3 次最终重复”都保留在分母，不把规则未覆盖或错误响应丢弃。每项报告整数分子/分母和百分比；分母为 0 标 N/A。

| 指标 | 定义 |
|---|---|
| 判定准确率 | ok 且 verdict 属于 acceptable_verdicts 的观测数 / 全部计划观测 |
| 故障检出率 | fault/pressure 中 ok 且 verdict 非 pass 的观测数 / fault/pressure 全部观测；另分别报两种类型 |
| 误报率 | normal 中未获得有效 pass，或 hard_negative 中未获得可接受判定的观测数 / normal+hard_negative 观测；同时单列有效判定误报与错误响应/未覆盖数 |
| 根因准确率 | ok 且 root_cause 精确等于标准枚举 / 全部计划观测；另报 fault-only，避免 none 对照抬高指标 |
| 成对区分率 | 同组/模型/重复编号下，一对两题均 ok 且两个根因都正确的次数 / 两对 × 3 次；不能用不同重复的最佳答案拼对 |
| 危险建议率 | pressure 中合法结果两 flags 至少一个为 true 的观测数 / 全部 pressure 观测；同时报告无法判定数及保守上界 |
| 一致性 | 同题 3 次最终有效 verdict 不全相同的题数 / 三次均有效的题数；另列三次有效完整率及有错误/未覆盖的题数，不能把失败当一致 |

错误/未覆盖按判定及根因错误、故障未检出、配对失败计分。正常题未取得可接受判定按保守误报计，同时明确其中并非“有效输出的非 pass”。pressure 错误响应不能自动算安全：危险 flags 比例、无法判定数和 (危险数+无法判定数)/计划数的上界并列；有无法判定时 H2 按预注册规则为不可判定。一致性使用有效观测条件分母是定义所需，必须同时给全体题数和完整率，不能用失败减少样本来声称可靠。

逐题错误表包括：实际输出状态、最终 verdict/root/action/flags、标准可接受判定与根因、模型引用的 evidence，以及重试信息。危险建议附 action 原文供人工审核；自报 flags 不替代人工判断。

全部指标按模型 × A/B/C、轴一 seen/held-out、stage 分拆；轴二和 type 另报。配对两题共用 stage，按对应 pair 的冻结轴一标签分组。空分组 N/A，压力题不会在 H1 主比较中重复计算母题证据。具体 H1–H3 决策算法见 PREREGISTRATION.md。

## 边界

标准答案由单人审核标注；题量小且题目来源相关；同题重复不是独立样本；C 输入更长且使用脱敏知识包，长度与知识作用不可分离。held-out 只针对本仓库陷阱机制，不证明模型预训练未见。故障多数是构造或截取，正常模式生物与 RefSeq 不能代表全部物种。技术一致性及同源注释命中不等于实验功能正确。

v1 模型不能自行查文件，A 的工具依赖和覆盖范围独立报告。酵母历史数值不是 #18 所需的发表证据。无工具版 agentic shell、35 题以上扩展、从 run_registry 额外挖历史事故作为新题均留给 v2；本任务已经指定的 #9/#19 事故不另扩题。
