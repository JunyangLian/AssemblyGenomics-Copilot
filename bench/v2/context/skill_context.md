## SKILL.md — intro + hard constraints

**生信流程的可靠性决策系统。** 生信分析最隐蔽的失败不是报错，而是**流程正常结束（exit 0）但结果已经不完整或不可靠**——数据库版本不合适、参数被默认值吞掉、RNA-seq 证据没有真正进入结构注释、功能注释只覆盖一小部分基因。本 skill 把真实项目里的失败模式、领域判断与 QC 标准结构化，让 Agent 不只是告诉用户"下一步运行什么"，而是根据输入数据决定流程、在每个阶段检查结果，并判定**继续、警告、还是回退修复**。

长期目标：把依赖个人经验的生信分析，变成**可复用、可检查、可验证的决策系统**——解决 Scientific Agent 的可靠性问题，而不仅是自动化问题。对新手它是手把手的护栏，对熟手它是第二双眼睛——静默缺口不挑人群。项目终点除结果外，交付一套**属于用户自己的可复用流程 SOP 包**（冻结 settings/版本/检查点）。

## 不可逾越的硬约束

这些约束由代码层（schema/校验/路由）强制，LLM 只能解释和提候选，**不得绕过**：

1. **交付表示必须显式声明**。`delivery.representation` 未填或为 `unresolved` 时阻断澄清，不静默假定；primary 不冒充分相结果，phased 交付需专门证据（D-003）。
2. **人类批准二要素缺一不可**：`approval.approved_by_human=true` 且 `submission_action` 非空。LLM 不能写出"已审核"状态，也不能复用旧版 hash 的批准。
3. **状态以磁盘结构化记录为准，不以聊天历史为准**。状态词表与迁移见 `references/qc-and-review-policy.md`。
4. **硬阻断场景直接停**：缺 R1/R2（按样本前缀成对，A_R1+B_R2 不算）、错误文库类型、样本角色冲突、多倍体路径未验证、混样、只有 Hi-C 无组装源、无法识别文库类型的 FASTQ（unknown_reads——不得默认当 WGS，须用户显式确认）、BAM 不视作组装源。告知用户缺什么、能做什么，而不是降级猜测。
5. **失败/缺失如实报告**。指标缺失、工具失败不得包装成正常通过；显示"未评估/不适用/执行失败"。
6. **不臆断环境**。本机探测不到的能力（如 bash 存根不可用）标记"需人工/需服务器"，不宣称已验证。
7. **资源预算必须显式向用户确认**（PIT-007）。线程/内存/磁盘写入 project.yaml 前先问"这台服务器你安全可用多少"——服务器可能公用或多用途，不得沿用默认值、示例命令或上一项目的预算（如 48 线程）；执行中同样不得超预算。

## references/qc-and-review-policy.md — general policy

# QC 与审核门控策略

状态机、审核门槛与失效传播的语义。实现：`scripts/state_registry.py`（状态机）、`scripts/validate_review.py`（审核）、`scripts/plan.py` 的 `invalidate_downstream`（失效传播）。

## 状态词表

```
PENDING -> READY -> RUNNING -> SUCCEEDED
RUNNING -> FAILED / WAITING_REVIEW / BLOCKED
WAITING_REVIEW -> READY / REJECTED
常驻：SKIPPED_NOT_APPLICABLE, STALE
```

语义要点：

- `SUCCEEDED` 只表示该节点执行与产物检查通过，**不代表组装科学质量通过**。
- `WAITING_REVIEW` 是正常业务状态，不是故障；进入后依赖审核结果的下游不占计算节点。
- `STALE` 表示上游输入、配置或工具版本改变后，原产物不再适用于当前任务。
- 状态以磁盘结构化记录（RunRegistry）为准，不以聊天历史为准；写入原子化。

## 重调度与恢复

- 禁止同一活跃项目重复提交。
- FAILED 后不得无界重试：须显式经 READY 才可重调度（`state_registry.py recover`）。
- 会话中断后恢复不重复提交。

## 审核门控（validate_review.py）

post-review 产物进入下一阶段前，逐项校验（任一不过即阻断，exit 1）：

1. **人类批准二要素**：`approval.approved_by_human=true` 且 `approval.submission_action` 非空，二者缺一即未批准。LLM 不能代写。
2. **hash 绑定**：`binds_to.input_assembly_hash` 与 `binds_to.review_package_hash` 必填；`stale=true` 的旧绑定拒绝复用——旧版批准不可延续到新版产物。
3. **编辑引用合法**：坐标/片段引用格式 `chr:start-end[:hap1|hap2]` 或 scaffold 引用；重复坐标须逐项可解释；缺 ref 即阻断。
4. **liftover 归属**：`liftover_from` 的 hap 与引用的 hap 标注不一致时阻断（hap1/hap2 不串用）。
5. **status 门控**：仅 `accepted`/`modified` 可继续；`rejected`/`undetermined` 阻断。

## 失效传播

上游 FASTA 或参数修改后，把项目置 `STALE`（仅对仍有效状态 SUCCEEDED/READY/RUNNING/WAITING_REVIEW 生效；FAILED/BLOCKED 已是非稳态，保持不变）。依赖旧产物的审核与指标随之失效，只重算受影响节点，历史版本保留。

## 报告如实原则（summarize_results.py）

- 数字由结构化产物确定性提取，不用 LLM 编造。
- 指标缺失、工具失败显示"未评估/不适用/执行失败"，不包装成通过。
- 污染/细胞器候选不未经批准直接删除——报告必须标出待批准项。
- 运行前交付表示未定即报告阻断；primary 不冒充分相结果（出现即警告）。

## 三种验证严格区分

| 验证类型 | 证明 | 不证明 |
|---|---|---|
| 配置/模拟 | 路由、审核门槛、状态转换、错误提示正确 | 工具真实运行与生物学质量 |
| 小样本 smoke | 接口兼容、命令与产物链路 | 完整基因组质量与资源规模 |
| 真实案例 | 指定数据/版本/目标下的表现 | 所有物种与未测组合的可靠性 |

引用能力结论时必须声明属于哪一类。

## knowledge/pitfalls/01-dfam.yaml — generic fields and exact mechanism excerpt

id: PIT-001
title: Dfam 重复序列库版本过旧，屏蔽不完整
phase: annotation
severity: warning
commands:
- RepeatModeler
- RepeatMasker
- RepeatMasker/DFAM_*.embl
root_cause: '流程可"跑通但不完整"：旧版库不存在于预期路径时报错，

  但一旦某路径下有任意旧版库，RepeatMasker 会静默使用它，不提示版本陈旧。

  新手常只下载 dfam0 而漏掉最新版，系统不警告。'

## knowledge/pitfalls/02-tsebra-intron-support.yaml — generic fields and exact mechanism excerpt

id: PIT-002
title: TSEBRA intron_support 默认 1.0 过严，合并阶段悄悄丢完整基因
phase: annotation
severity: warning
commands:
- tsebra.py
- braker3.cfg
- BRAKER3
root_cause: '官方默认 braker3.cfg 的 intron_support 1.0 要求普通模型具备完全内含子证据

  支持才保留；RNA 覆盖不均时大量真实基因被过滤。流程"成功结束"完全掩盖了

  这一步的质量损失——属于最典型的 silent gap，只有受控对照（同输入重合并 +

  BUSCO 逐 ID 对照）才能定位。'

## knowledge/pitfalls/03-busco-miniprot-stops.yaml — generic fields and exact mechanism excerpt

id: PIT-003
title: BUSCO genome 模式（--miniprot）的内部终止密码子统计不可信
phase: annotation
severity: warning
commands:
- busco
- miniprot
root_cause: 'BUSCO 6.1.0 与 miniprot 0.18-r281 输出字段兼容问题（miniprot.py

  `fields[17]` 固定索引解析）。组装层面的 C/S/D 命中选择也可能受影响，

  不只是 E 值一行。把这份报告写进论文或质控结论即引入错误数字。'

## knowledge/pitfalls/04-protein-internal-dots.yaml — generic fields and exact mechanism excerpt

id: PIT-004
title: 蛋白 FASTA 含内部 `.` / 内部 `*`，悄悄污染下游注释与分母
phase: annotation
severity: warning
commands:
- diamond
- interproscan.sh
- gffread
root_cause: '基因组 N 区/移码区的翻译产物携带歧义字符；多数流程只移除一个末端 `*`，

  不检查内部字符。隔离（quarantine）时不得把 `.` 解释为已确认的终止密码子，

  也不得改写源文件。'

## knowledge/pitfalls/05-gff3-noncoding-residue.yaml — generic fields and exact mechanism excerpt

id: PIT-005
title: 注释 GFF3 残留无编码内容的 gene/transcript，基因计数虚高
phase: annotation
severity: warning
commands:
- agat_sp_keep_longest_isoform.pl
- tsebra.py
- braker.gff3
root_cause: 'TSEBRA 合并/AGAT 最长转录本筛选后残留了无编码内容的 gene 与 transcript

  记录（具体产生机制未追溯到某软件的某行代码，不写成已证实缺陷）。'

## knowledge/pitfalls/06-softmask-lowercase.yaml — generic fields and exact mechanism excerpt

id: PIT-006
title: 传给 BRAKER 的"软屏蔽"基因组实际是硬屏蔽或未屏蔽
phase: annotation
severity: critical
commands:
- RepeatMasker
- braker.pl
- --softmasking
root_cause: 'RepeatMasker 不加 `-xsmall` 时输出为硬屏蔽；或流程链条中拿错文件

  （.masked 与 .softmasked 并存时极易混淆）。"`-s` 是敏感模式不是软屏蔽

  开关"这类参数误解也源于此。下游任何环节都不会替你检查输入屏蔽方式。'

## knowledge/pitfalls/07-shared-server-budget.yaml — generic fields and exact mechanism excerpt

id: PIT-007
title: 共享服务器上线程/资源预算未经确认即拉满
phase: general
severity: warning
commands:
- RepeatModeler
- braker.pl
- qsub
- sbatch
root_cause: '线程预算是服务器策略问题（共享/独占、配额、管理员约定），不是技术参数——

  工具文档、示例命令、甚至既往项目的 settings 都不会替你问。'

## knowledge/pitfalls/08-fasta-header-mismatch.yaml — generic fields and exact mechanism excerpt

id: PIT-008
title: BRAKER 输入 FASTA 头含空格/描述 → ETP 参考名与 BAM 不匹配，GeneMark 失败且提示误导
phase: annotation
severity: warning
commands:
- braker.pl
- gmetp.pl
context_note: '硬化规则：BRAKER 前生成 genome.id_only.softmasked.fa（头仅首字段），

  校验 ID 唯一/逐序列长度/忽略大小写序列不变，并与全部 BAM 的 @SQ 集合完全一致，

  不一致即停止。'

## knowledge/pitfalls/09-single-exon-filter-species.yaml — generic fields and exact mechanism excerpt

id: PIT-009
title: TSEBRA 单外显子过滤器是物种内含子含量依赖的——内含子贫乏物种上会滤掉绝大多数真基因
phase: annotation
severity: critical
commands:
- tsebra.py
- --filter_single_exon_genes
root_cause: '`--filter_single_exon_genes` 滤除"无起始/终止 hint 支持的单外显子基因"。'

## knowledge/pitfalls/README.md — PIT-010 generic clauses

"等效重跑"TSEBRA 合并 ≠ BRAKER3 内部合并
重跑 exit 0、数量级看似合理，只能靠 raw vs 重跑基因数对照揭露

## knowledge/baselines/README.md — purpose and dual-layer policy

# 文献基线（Literature Baselines）

回答一个新手最容易漏掉的问题：**"我这个数正常吗？"**

机制来源（用户洞察，D-015/D-016）：绝大多数物种类群的关键指标（基因数、BUSCO 完整度、
重复屏蔽比例、注释覆盖率……）有大量发表先例。除少数特殊情况（多倍化、超紧凑基因组、
极端 TE 膨胀），**与可比先例差距悬殊几乎必然有问题**——但新手没有文献量，不知道
"正常长什么样"。

本 skill 面向**所有基因组**，因此基线不是预填充的全局表，而是双层结构（D-016）：

## 双层结构

| 层 | 来源 | 权威性 | 何时确定 |
|---|---|---|---|
| **项目级锚点** | intake 确定数据来源时，选定该物种/属最近的已发表同类（发表注释、组装、基因组大小记录），写入 `project.yaml` 的 `baselines` 节 | 权威；`metric_overrides` 可 enforce（范围外按 GAP 报警） | **项目开始时**（与选 BUSCO lineage 同一动作） |
| **类群兜底带** | `knowledge/baselines/*.yaml` 全局注册表（真实案例种子逐步生长） | advisory；仅提示不强制 | 兜底：项目未覆盖的指标退回这里 |

项目未选定锚点**不阻断路由**，但对照输出会明示"仅类群兜底带"，最终报告必须如实标注——
不静默假定有锚。这正是"未声明不假定"纪律（D-003）在基线上的同构。

## 与陷阱库（pitfalls）的关系

- pitfalls 探测**过程**中的静默缺口（库版本、参数、文件格式）——问"这步做对了吗"。
- baselines 探测**结果**的合理性——问"这个数像话吗"。两者正交互补。

## knowledge/baselines/actinopterygii.yaml — all generic bands

- id: BASE-001
  metric: protein_coding_gene_count
  taxon_scope: actinopterygii
  unit: genes
  expected_range:
  - 15000
  - 85000
  source_type: case_reference
  enforce: false
- id: BASE-002
  metric: annotation_busco_complete_pct
  taxon_scope: actinopterygii
  unit: percent
  expected_range:
  - 85
  - 100
  source_type: case_reference
  enforce: false
- id: BASE-003
  metric: repeat_masked_pct
  taxon_scope: actinopterygii
  unit: percent
  expected_range:
  - 5
  - 45
  source_type: case_reference
  enforce: false
- id: BASE-004
  metric: median_protein_length_aa
  taxon_scope: actinopterygii
  unit: aa
  expected_range:
  - 300
  - 550
  source_type: case_reference
  enforce: false
- id: BASE-005
  metric: functional_any_annotated_pct
  taxon_scope: actinopterygii
  unit: percent
  expected_range:
  - 70
  - 95
  source_type: case_reference
  enforce: false

## knowledge/baselines/aves.yaml — all generic bands

- id: AVE-001
  metric: protein_coding_gene_count
  taxon_scope: aves
  unit: genes
  expected_range:
  - 12000
  - 25000
  source_type: population_reference
  enforce: false
- id: AVE-002
  metric: median_protein_length
  taxon_scope: aves
  unit: aa
  expected_range:
  - 450
  - 600
  source_type: population_reference
  enforce: false

## knowledge/baselines/fungi.yaml — all generic bands

- id: FUNGI-001
  metric: protein_coding_gene_count
  taxon_scope: fungi
  unit: genes
  expected_range:
  - 4000
  - 8000
  source_type: population_reference
  enforce: false
- id: FUNGI-002
  metric: median_protein_length
  taxon_scope: fungi
  unit: aa
  expected_range:
  - 350
  - 500
  source_type: population_reference
  enforce: false

## knowledge/baselines/insecta.yaml — all generic bands

- id: INS-001
  metric: protein_coding_gene_count
  taxon_scope: insecta
  unit: genes
  expected_range:
  - 9000
  - 20000
  source_type: population_reference
  enforce: false
- id: INS-002
  metric: median_protein_length
  taxon_scope: insecta
  unit: aa
  expected_range:
  - 420
  - 620
  source_type: population_reference
  enforce: false

## knowledge/baselines/mammalia.yaml — all generic bands

- id: MAM-001
  metric: protein_coding_gene_count
  taxon_scope: mammalia
  unit: genes
  expected_range:
  - 13000
  - 30000
  source_type: population_reference
  enforce: false
- id: MAM-002
  metric: median_protein_length
  taxon_scope: mammalia
  unit: aa
  expected_range:
  - 440
  - 600
  source_type: population_reference
  enforce: false

## knowledge/baselines/nematoda.yaml — all generic bands

- id: NEM-001
  metric: protein_coding_gene_count
  taxon_scope: nematoda
  unit: genes
  expected_range:
  - 8000
  - 35000
  source_type: population_reference
  enforce: false
- id: NEM-002
  metric: median_protein_length
  taxon_scope: nematoda
  unit: aa
  expected_range:
  - 150
  - 420
  source_type: population_reference
  enforce: false

## knowledge/baselines/viridiplantae.yaml — all generic bands

- id: PLT-001
  metric: protein_coding_gene_count
  taxon_scope: viridiplantae
  unit: genes
  expected_range:
  - 15000
  - 55000
  source_type: population_reference
  enforce: false
- id: PLT-002
  metric: median_protein_length
  taxon_scope: viridiplantae
  unit: aa
  expected_range:
  - 320
  - 450
  source_type: population_reference
  enforce: false


# C2 shared QC interpretation guidance

## Disposition and downstream use

Decide whether the delivered files can be consumed correctly before interpreting a quality statistic. A broken format or unresolved cross-file connection requires blocking consumption until repaired and validated. A completed analysis whose results are unreliable requires returning to the affected analysis step and regenerating the delivery. A usable result with a documented limitation may warrant a warning. Explain the relevant downstream consequence. Do not choose a disposition solely because a number is high or low. Distinguish a demonstrated failure from an optional additional diagnostic that has not been supplied.

## Database and run context

Evaluate a database version against the recorded run date, project specification and compatibility requirements. Do not infer obsolescence from an internally remembered latest release. A pinned version does not excuse incompatible inputs or failure to meet a stated requirement. State what the supplied version record establishes and what remains unknown.

## Coverage and identifier connections

For annotation coverage, identify the actual query set, unique identifiers, annotation flags, join operation and denominator. Compare the row-level annotations to the joined statistics. Missing annotation content with valid connections and rich annotations that cannot be connected to their queries require different remedies. Do not silently strip suffixes or rewrite identifiers without an unambiguous mapping and a subsequent connection check. Count distinct queries, not merely rows.

## Coding features and protein delivery

CDS feature rows represent coding segments; a protein can legitimately correspond to several rows. Distinguish CDS segments, transcripts, coding gene loci and unique protein identifiers. Check the parent-child hierarchy and the connection between CDS protein references and complete FAA records. A surplus of CDS rows alone does not establish extra genes, missing proteins or damaged annotation. An unresolved protein-reference connection must be repaired before extraction or downstream interpretation.

## Species and metric definitions

Interpret percentages using their actual biological unit, denominator, analysis mode and species context. Do not equate a fragment's proportion with a whole-genome measurement, or a transposable-element estimate with all masked bases. Do not manufacture a mandatory rejection threshold for a valid delivery merely because an additional optional metric is absent. Preserve nucleotide identity when downstream analyses require soft masking; compare case-insensitive sequence content as well as length and masking counts.
