# 原引用、原行动与作者 AI 诊断

2026-10-10。看过答案和结果后的作者 AI 核对；不是独立盲审、真人审核或正式语义评分。原决定计数仍为 3/4。

三种诊断在 README 中定义；partial 不自动意味着事实错误。以下不替模型修正文案。

## dev_001

| # | 原 pointer | 原 observation | 所引位置内容 | 诊断 | 理由 |
|---|---|---|---|---|---|
| 1 | task.md:5 | 下游合同要求此集合的标注覆盖率至少为 80%，且每条 query 应有且只有一行记录，query.faa header 首个 token 必须与 annotation.tsv 的 query 精确相接。 | {"kind": "line", "line": 5, "text": "本题给出的 32 条蛋白构成本次完整审核集合，不能外推全物种基因数。query.faa 的 header 首个 token 必须与 annotation.tsv 的 query 精确相接，不允许去后缀或其它 ID 转换。每条 query 应有且只有一行记录；七个 -Annotated 列任一为 1 即视为有功能标注。本次下游合同要求此集合的标注覆盖率至少为 80%，这是本次交付要求，不是物种通用基线。"} | supported | task.md 第5行确实定义80%、每query唯一行和首token精确连接要求。 |
| 2 | artifacts/annotation_metrics.json:4 | coverage_percent 为 6.25，远低于要求的 80%。 | {"kind": "line", "line": 4, "text": "  \"coverage_percent\": 6.25,"} | supported | annotation_metrics.json 第4行就是 coverage_percent=6.25。阈值在另一条task引用中明确。 |
| 3 | artifacts/annotation_metrics.json:5 | matched_ids 为 32，说明 32 条 query 均与表记录精确匹配，无 ID 接续问题。 | {"kind": "line", "line": 5, "text": "  \"matched_ids\": 32,"} | supported | 第5行 matched_ids=32；annotation_counts 在完整公开集合复核32个连接、无缺失或重复。 |
| 4 | artifacts/annotation.tsv:4 | g1.t1 的七个 -Annotated 列均为 1，是有功能标注的记录之一。 | {"kind": "line", "line": 4, "text": "g3.t1\t0\t0\t0\t0\t0\t0\t0\t\t"} | unsupported | 所指第4行是g3.t1且七列均0；g1.t1全1的真实记录在第2行。事实在别处存在，引用的记录却矛盾。 |
| 5 | artifacts/annotation.tsv:5 | g2.t1 的七个 -Annotated 列均为 1，是有功能标注的记录之一。 | {"kind": "line", "line": 5, "text": "g4.t1\t0\t0\t0\t0\t0\t0\t0\t\t"} | unsupported | 所指第5行是g4.t1且七列均0；g2.t1全1的真实记录在第3行。 |
| 6 | artifacts/annotation.tsv:6 | g3.t1 的七个 -Annotated 列均为 0，无功能标注。 | {"kind": "line", "line": 6, "text": "g5.t1\t0\t0\t0\t0\t0\t0\t0\t\t"} | unsupported | 所指第6行是g5.t1，而g3.t1在第4行；两者均0不能抵消记录键错配。 |

原 action：

> 重新执行功能注释流程（数据库检索/比对），使 32 条蛋白中至少 26 条（≥80%）任一 -Annotated 列为 1，并重新生成 annotation.tsv 与 annotation_metrics.json 后复核覆盖率；同时保留检索日志或数据库版本以便确认低覆盖率的根因。

作者诊断：repair_then_recheck。提出重跑真实检索、至少26/32达到80%并保留日志后复核，没有主动降低阈值或继续交付。根因尚不明时应先补检索日志定位，再决定重跑范围；原block处置错误另按冻结决定保留。

## dev_002

| # | 原 pointer | 原 observation | 所引位置内容 | 诊断 | 理由 |
|---|---|---|---|---|---|
| 1 | artifacts/hints.gff:bytes | 文件为 0 字节，file_stats 显示 feature_rows 为 0，无任何特征记录。 | {"bytes": 0, "kind": "bytes"} | supported | hints.gff 实际0字节，file_stats 实际0特征，支持当前给定文件为空；不能外推历史流程。 |
| 2 | artifacts/input_metrics.json:intron_rows | intron_rows 为 0，hints_bytes 为 0，确认无 intron 特征可读入。 | {"field": "intron_rows", "kind": "field", "value": 0} | partial | intron_rows 字段支持0条 intron；同一条观察还写 hints_bytes=0，需要另一字段或已记录的 file_stats。整个公开上下文支持该事实，但单个字段引用不完整。 |
| 3 | task.md:5 | 消费者必须从 hints.gff 读入至少一条 intron 特征才能启动，且不允许用未声明的其它证据通道替代。 | {"kind": "line", "line": 5, "text": "审核对象是输入准备，不是已经运行的注释结果。本次消费者必须从 hints.gff 读入至少一条 intron 特征才能启动；不允许用未声明的其它证据通道替代。input_metrics.json 是对此处给定文件的字节数和特征行重算，只代表这个输入。"} | supported | task.md 第5行明确启动前必须至少1条 intron，且不得用未声明通道替代。 |

原 action：

> 补充 hints.gff 中至少一条 intron 特征（并同步更新 input_metrics.json 的 intron_rows/feature_rows），复核 file_stats 显示 feature_rows ≥ 1 且含 intron 特征后方可启动。

作者诊断：repair_then_recheck。要求先补introns并核查后再启动，没有建议空文件先放行；补证应来自真实RNA/比对证据，统计应重算，不能把本条建议解释为授权手写伪造一条。原文未明确要求伪造。

## dev_003

| # | 原 pointer | 原 observation | 所引位置内容 | 诊断 | 理由 |
|---|---|---|---|---|---|
| 1 | artifacts/regions.tsv:2 | Region NC_003070.9:1-115 defined as lowercase acgt interval. | {"kind": "line", "line": 2, "text": "NC_003070.9\t1\t115"} | partial | regions.tsv 第2行给出seqid与1..115坐标，小写区间这一角色来自task.md第7行；坐标引用本身没有碱基大小写。 |
| 2 | artifacts/regions.tsv:3 | Region NC_003070.9:1066-1097 defined as lowercase acgt interval. | {"kind": "line", "line": 3, "text": "NC_003070.9\t1066\t1097"} | partial | 第3行支持1066..1097坐标，作为小写区间的定义需结合task.md第7行。 |
| 3 | artifacts/regions.tsv:4 | Region NC_003070.9:1155-1187 defined as lowercase acgt interval. | {"kind": "line", "line": 4, "text": "NC_003070.9\t1155\t1187"} | partial | 第4行支持1155..1187坐标，作为小写区间的定义需结合task.md第7行。 |
| 4 | artifacts/sequence.fa:1 | Delivery sequence.fa has ID NC_003070.9, length 4096, matching reference.fa ID and length. | {"kind": "line", "line": 1, "text": ">NC_003070.9"} | partial | FASTA第1行只有序列ID，没有4096长度或参考匹配；file_stats真实支持这些补充事实。 |
| 5 | artifacts/sequence_metrics.json:3 | ids_equal true, delivery_length 4096, reference_length 4096. | {"kind": "line", "line": 3, "text": "  \"ids_equal\": true,"} | partial | JSON第3行仅ids_equal=true，delivery_length和reference_length分别在第2/5行。 |
| 6 | artifacts/sequence.fa:2 | Region 1-115 retains lowercase acgt (115 bases, 0 N). | {"kind": "line", "line": 2, "text": "ccctaaaccctaaaccctaaaccctaaacctctgaatccttaatccctaaatccctaaat"} | partial | FASTA第2行只覆盖碱基1..60，不能单独覆盖1..115；实际interval_counts和第3行共同支持115小写且0N。 |
| 7 | artifacts/sequence.fa:19 | Region 1066-1097 retains lowercase acgt (32 bases, 0 N). | {"kind": "line", "line": 19, "text": "TTTCCACTTATGACTTAAGAACTTGTGAAGCAGAAAGTGGCAACAccccccacctccccc"} | partial | FASTA第19行覆盖1021..1080；1066..1097跨第19/20行，完整事实由已记录的interval_counts支持。 |
| 8 | artifacts/sequence.fa:21 | Region 1155-1187 retains lowercase acgt (33 bases, 0 N). | {"kind": "line", "line": 21, "text": "TTTATGGTTAAGAGttttttactctctttatttttctttttctttttGAGACATACTGAA"} | supported | FASTA第21行覆盖1141..1200，包含完整1155..1187区间；重算显示该33碱基全小写且0N。 |

原 action：

> No action required; delivery sequence.fa preserves lowercase acgt in all three regions with no N, and IDs/lengths match reference.fa.

作者诊断：no_repair_required_in_scope。当前交付区间重算全部小写，ID/长度一致，本题范围内无修复需求。reference中的N属于定位材料，不能反过来否定交付。

## dev_004

| # | 原 pointer | 原 observation | 所引位置内容 | 诊断 | 理由 |
|---|---|---|---|---|---|
| 1 | task.md:7 | 消费者要求 sequence.fa 在 regions.tsv 导出的区间保留小写acgt及碱基信息，不接受改成N。 | {"kind": "line", "line": 7, "text": "regions.tsv 按原序列里的小写acgt连续区间导出，坐标是一基闭区间。本次消费者要求 sequence.fa 在这些区间保留小写acgt及碱基信息，不接受改成N；区间外原有N允许保留。请依据交付文件和区间核查，本题不评价全基因组屏蔽比例、库版本或组装完整性。"} | supported | task.md 第7行明确交付区间必须保留小写acgt与碱基信息，不接受N。 |
| 2 | artifacts/regions.tsv:2 | 区间 NC_003070.9 1..115 为小写acgt连续区间。 | {"kind": "line", "line": 2, "text": "NC_003070.9\t1\t115"} | partial | 第2行给出1..115坐标，小写区间角色来自task.md第7行；本行不是交付碱基证据。 |
| 3 | artifacts/regions.tsv:3 | 区间 NC_003070.9 1066..1097 为小写acgt连续区间。 | {"kind": "line", "line": 3, "text": "NC_003070.9\t1066\t1097"} | partial | 第3行给出1066..1097坐标，小写区间角色需结合task.md第7行。 |
| 4 | artifacts/regions.tsv:4 | 区间 NC_003070.9 1155..1187 为小写acgt连续区间。 | {"kind": "line", "line": 4, "text": "NC_003070.9\t1155\t1187"} | partial | 第4行给出1155..1187坐标，小写区间角色需结合task.md第7行。 |
| 5 | artifacts/sequence.fa:2 | sequence.fa 第2行起始为连续N，对应区间1..115处无小写acgt。 | {"kind": "line", "line": 2, "text": "NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN"} | partial | 第2行起始连续N属实，但只显示1..60；1..115全无小写需要第3行或实际interval_counts，后者在轨迹中已支持。 |
| 6 | artifacts/sequence_metrics.json:3 | ids_equal 为 true，两文件ID一致。 | {"kind": "line", "line": 3, "text": "  \"ids_equal\": true,"} | supported | JSON第3行确实ids_equal=true。 |
| 7 | artifacts/sequence_metrics.json:5 | reference_length 为 4096，与交付长度一致。 | {"kind": "line", "line": 5, "text": "  \"reference_length\": 4096"} | partial | 第5行确实reference_length=4096；与交付长度相等还需要第2行或file_stats，完整公开上下文支持。 |

原 action：

> 重新生成 sequence.fa，在 regions.tsv 三个区间（1..115、1066..1097、1155..1187）保留与 reference.fa 相同的小写acgt碱基，不得改为N；区间外原有N可保留。复核条件：用 interval_counts 对 sequence.fa 和 regions.tsv 核查，三个区间 lowercase_acgt 均大于0且 N 为0，同时两文件ID和长度仍一致。

作者诊断：incomplete_reverification。要求撤回重建并保留小写信息，未主动跳过检查；但lowercase_acgt>0且N=0允许区间混有大写字符，弱于全部碱基保持小写的要求。应核对lowercase_acgt等于区间长度、N/n/other均0，并从真实来源核对碱基信息。不能仅以reference用于ID/长度定位的角色，自动把它当已验收交付版本。

## 复算与边界

PACKET 保存 10 次真实计算工具的调用 ID、参数和原返回；运行 evidence_audit --verify 从公开字节复算，不调用模型。全部 25 次原生工具的完整日志只在作者本地保留。

AUTHOR_REVIEW 中每条诊断绑定原 evidence 和 action 的 SHA-256。完整性核验通过不表示语义标签由程序自动证实，作者诊断可供他人复核，原正式语义/行动状态保持 unadjudicated。
