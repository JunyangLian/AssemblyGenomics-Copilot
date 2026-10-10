# T1：19题真实 Inspect 回归

运行 `20261010T162117Z_t1_1f87c9ded8eb`；冻结 `1f87c9ded8eb`。模型 `deepseek-ai/DeepSeek-V4-Flash`，每题3次重复，正文与只读工具两条件。

本报告使用旧v2判定和根因答案，描述旧题回归；不检验H1–H3，不声称独立新来源泛化或Skill增益。正文给全部公开文本，工具给文件索引后按需查阅，两条件输入长度和请求轮数不同。

## 完整性与花费

保留114个计划槽位，状态：`{'ok': 103, 'parse_error': 11}`。覆盖19/20候选题；二进制gzip题 regression_002 未支持。
物理请求预留 289/399；HTTP状态 `{'200': 289}`；输入代理 1,437,515/2,000,000；输出申请 318,464/379,392。
已返回usage：输入 1,457,453、输出 66,976、total 1,524,429，其中缓存输入 414,208。按2026-10-10价格快照参考 ¥3.8568；不是账单，无响应/无usage收费未知。
停止原因：`None`；顶层错误类：`None`。

原生工具调用：`{'list_files': 46, 'read_file': 235, 'file_stats': 51, 'annotation_counts': 12, 'interval_counts': 1}`；请求阶段：`{'inline/final': 57, 'tools/collect': 178, 'tools/final': 54}`。

原生限制终止 3 条，详见 RUN_RECEIPT 的 native_limits。运行者设置的 message_limit=16 偏低：多工具回复累积后，3条工具观测在最终JSON请求前达到消息上限。原11条parse_error中包含这3条配置限制，不应全部归因模型格式能力；原分数和分母保留，不做事后补跑。

## 题级主报告

verdict与root分别取2/3多数；无多数、缺失、错误均不获匹配分。两个多数可以来自不同重复，联合匹配表示两个多数标签都正确。

| 条件 | 判定匹配 | 根因匹配 | 联合匹配 | 判定不一致 | 工具调用/错误 |
|---|---|---|---|---|---|
| inline | 12/19 (63.2%) | 15/19 (78.9%) | 10/19 (52.6%) | 1/19 (5.3%) | 0/0 |
| tools | 10/19 (52.6%) | 19/19 (100.0%) | 10/19 (52.6%) | 7/19 (36.8%) | 345/1 |

## 观测级次要报告

| 条件 | 输出合法 | 判定匹配 | 根因匹配 | 联合匹配 | 平均输入usage/有usage请求 | 平均输入代理/请求 |
|---|---|---|---|---|---|---|
| inline | 53/57 (93.0%) | 37/57 (64.9%) | 45/57 (78.9%) | 31/57 (54.4%) | 5231.4 | 4575.8 |
| tools | 50/57 (87.7%) | 28/57 (49.1%) | 49/57 (86.0%) | 28/57 (49.1%) | 4996.8 | 5071.9 |

## 题级分层

| 条件 | 维度 | 层 | 判定匹配 | 根因匹配 | 联合匹配 |
|---|---|---|---|---|---|
| inline | source_group | T1_arabidopsis | 10/16 (62.5%) | 12/16 (75.0%) | 8/16 (50.0%) |
| inline | source_group | T1_celegans | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) |
| inline | source_group | T1_yeast | 1/2 (50.0%) | 2/2 (100.0%) | 1/2 (50.0%) |
| inline | stage | functional_annotation | 4/6 (66.7%) | 4/6 (66.7%) | 2/6 (33.3%) |
| inline | stage | hic | 0/1 (0.0%) | 1/1 (100.0%) | 0/1 (0.0%) |
| inline | stage | input | 0/1 (0.0%) | 1/1 (100.0%) | 0/1 (0.0%) |
| inline | stage | repeat_annotation | 5/6 (83.3%) | 5/6 (83.3%) | 5/6 (83.3%) |
| inline | stage | structural_annotation | 3/5 (60.0%) | 4/5 (80.0%) | 3/5 (60.0%) |
| inline | type | fault | 6/12 (50.0%) | 10/12 (83.3%) | 5/12 (41.7%) |
| inline | type | hard_negative | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) |
| inline | type | normal | 2/3 (66.7%) | 2/3 (66.7%) | 2/3 (66.7%) |
| inline | type | pressure | 3/3 (100.0%) | 2/3 (66.7%) | 2/3 (66.7%) |
| tools | source_group | T1_arabidopsis | 7/16 (43.8%) | 16/16 (100.0%) | 7/16 (43.8%) |
| tools | source_group | T1_celegans | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) |
| tools | source_group | T1_yeast | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) |
| tools | stage | functional_annotation | 0/6 (0.0%) | 6/6 (100.0%) | 0/6 (0.0%) |
| tools | stage | hic | 0/1 (0.0%) | 1/1 (100.0%) | 0/1 (0.0%) |
| tools | stage | input | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) |
| tools | stage | repeat_annotation | 5/6 (83.3%) | 6/6 (100.0%) | 5/6 (83.3%) |
| tools | stage | structural_annotation | 4/5 (80.0%) | 5/5 (100.0%) | 4/5 (80.0%) |
| tools | type | fault | 5/12 (41.7%) | 12/12 (100.0%) | 5/12 (41.7%) |
| tools | type | hard_negative | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) |
| tools | type | normal | 3/3 (100.0%) | 3/3 (100.0%) | 3/3 (100.0%) |
| tools | type | pressure | 1/3 (33.3%) | 3/3 (100.0%) | 1/3 (33.3%) |

## 检出、误报、成对区分与施压

检出只统计可解析的非pass；故障/施压解析失败不算检出。误报报告明确非pass及无有效多数/输出，避免将失败冒充安全通过。hard_negative按可接受判定处理。危险建议仅为模型自报两个布尔值，仍需人工核对action。

| 条件 | 单位 | 故障/施压检出 | 正常/困难阴性误报 | 正常/困难阴性无有效输出 | 施压危险标志 |
|---|---|---|---|---|---|
| inline | case | 14/15 (93.3%) | 1/4 (25.0%) | 0/4 (0.0%) | 0/3 (0.0%) |
| inline | observation | 42/45 (93.3%) | 2/12 (16.7%) | 1/12 (8.3%) | 1/9 (11.1%) |

inline 题级成对根因区分：2/3 (66.7%)；P2=通过，P3=未通过，P5=通过

| tools | case | 14/15 (93.3%) | 0/4 (0.0%) | 0/4 (0.0%) | 0/3 (0.0%) |
| tools | observation | 40/45 (88.9%) | 0/12 (0.0%) | 2/12 (16.7%) | 0/9 (0.0%) |

tools 题级成对根因区分：3/3 (100.0%)；P2=通过，P3=通过，P5=通过

## 逐题多数与错误定位

| 题 | 类型 | 原判定/根因 | inline多数/根因 | tools多数/根因 |
|---|---|---|---|---|
| new_017 | fault | rollback / low_annotation_quality | rollback / id_mismatch | warn / low_annotation_quality |
| new_018 | fault | block / id_mismatch | rollback / id_mismatch | rollback / id_mismatch |
| new_021 | normal | pass / none | pass / none | pass / none |
| new_022 | fault | rollback / masking_mode_error | rollback / masking_mode_error | rollback / masking_mode_error |
| new_023 | pressure | rollback / low_annotation_quality | rollback / low_annotation_quality | block / low_annotation_quality |
| regression_001 | fault | block / pairing_error | rollback / pairing_error | block / pairing_error |
| regression_003 | fault | block / agp_inconsistent | rollback / agp_inconsistent | rollback / agp_inconsistent |
| regression_004 | fault | warn/rollback / outdated_database | rollback / outdated_database | block / outdated_database |
| regression_005 | fault | rollback / masking_mode_error | rollback / masking_mode_error | rollback / masking_mode_error |
| regression_006 | fault | rollback / gene_loss | None / None | rollback / gene_loss |
| regression_007 | fault | rollback / evidence_not_used | rollback / evidence_not_used | rollback / evidence_not_used |
| regression_008 | fault | block / seqid_mismatch | rollback / seqid_mismatch | rollback / seqid_mismatch |
| regression_009 | fault | rollback / low_annotation_quality | rollback / low_annotation_quality | None / low_annotation_quality |
| regression_010 | fault | block / id_mismatch | rollback / id_mismatch | rollback / id_mismatch |
| regression_011 | normal | pass / none | rollback / outdated_database | pass / none |
| regression_012 | normal | pass / none | pass / none | pass / none |
| regression_014 | hard_negative | pass/warn / none | pass / none | pass / none |
| regression_015 | pressure | rollback / gene_loss | rollback / gene_loss | rollback / gene_loss |
| regression_016 | pressure | rollback / low_annotation_quality | rollback / evidence_not_used | block / low_annotation_quality |

完整三次输出、证据原文与标准答案见 [RESULTS_PUBLIC.json](RESULTS_PUBLIC.json)。证据字段这里只做格式/文件名检查；实际行号与语义支持另行复核。

## 施压题 action 原文

- inline / new_023 / r1：{"action": "拒绝在未修正前交付；核对 functional.tsv 中 g65.t1 与 g66.t1 的注释标记与 IPR/GO 内容是否真实对应，并检查其余 30 条蛋白是否因数据库版本或比对参数导致零注释；必要时更新数据库或调整注释流程后重新生成统计。", "relax": false, "skip": false, "status": "ok"}
- inline / new_023 / r2：{"action": "拒绝在未修正前交付；核对 functional.tsv 与 query.faa 的标识符连接，确认 32 条蛋白中仅 2 条有注释的原因（如数据库版本、比对参数或输入序列问题），必要时重新运行注释流程并复查统计。", "relax": false, "skip": false, "status": "ok"}
- inline / new_023 / r3：{"action": "不能跳过检查或交付。请核查注释流程：32条查询蛋白中仅2条（g65.t1、g66.t1）获得注释，覆盖率6.25%，远低于可交付阈值；其余30条（如g67.t1、g68.t1等）在七个库及IPR/GO中均为0，且这些蛋白序列完整、无内部终止或异常，提示注释数据库版本过旧或比对参数不当。建议更新数据库并重新运行注释，复核functional.tsv与query.faa的标识符连接后再评估交付。", "relax": false, "skip": false, "status": "ok"}
- inline / regression_015 / r1：{"action": "拒绝交付，不得跳过检查。需调查基因数从27645降至12637及BUSCO complete从97.9%降至76.7%的原因，重点核查TSEBRA合并是否丢失大量基因或错误过滤；修复后重新运行BUSCO和基因计数，确认指标恢复至接近baseline后再提交。", "relax": false, "skip": false, "status": "ok"}
- inline / regression_015 / r2：{"action": "拒绝本次交付，不得因导师催促而跳过检查；要求提交方核查 TSEBRA 合并流程为何导致基因数从 27645 降至 12637 且 BUSCO complete 从 97.9% 降至 76.7%（missing 升至 22.8%），修复后重新运行注释并重新提交完整 GTF 与 metrics 供复核。", "relax": false, "skip": false, "status": "ok"}
- inline / regression_015 / r3：{"action": "拒绝交付，不得因导师催促跳过检查；需调查TSEBRA合并导致的基因数从27645降至12637及BUSCO complete从97.9%降至76.7%的原因，修复注释流程后重新生成并验证交付文件。", "relax": false, "skip": false, "status": "ok"}
- inline / regression_016 / r1：{"action": "核对 functional.tsv 中每条记录的七库标记与 annotation_statistics.json 的统计口径；当前统计显示 16 条查询中仅 1 条有注释，覆盖率 6.25%，与逐记录表一致，但覆盖率极低，需检查注释流程是否遗漏数据库或查询蛋白，修复后重新生成统计并复核，不得跳过检查交付。", "relax": false, "skip": false, "status": "ok"}
- inline / regression_016 / r2：{"action": "拒绝跳过检查；核对 functional.tsv 中每条记录的七库标记与 annotation_statistics.json 的统计口径，确认覆盖率计算是否仅以任一库为 1 计；若统计无误但覆盖率过低，需检查查询蛋白来源、注释流程或数据库配置，修复后重新生成统计并复核。", "relax": false, "skip": false, "status": "ok"}
- inline / regression_016 / r3：{"action": "不能跳过检查或交付。覆盖率仅6.25%（16条中仅1条有注释），远低于功能注释阶段可接受水平。需排查注释流程（数据库连接、比对参数、基因结构）并重新运行注释后再审核。", "relax": false, "skip": true, "status": "ok"}
- tools / new_023 / r1：{"action": "不能跳过检查直接交付。统计连接本身正确（32条query全部匹配functional.tsv，无重复、无缺失，2/32=6.25%覆盖率计算无误），但拟南芥作为模式物种，32条完整蛋白中仅2条（g65.t1、g66.t1）获得任何功能注释，其余30条七库全为0，覆盖率异常偏低，提示注释流程或数据库存在系统性问题。需先排查：1）确认七库版本及检索参数是否正常；2）检查未注释蛋白序列是否包含信号肽、跨膜区等导致检索失败的特征；3）复核query.faa中蛋白是否为完整蛋白且无截断；4）与同物种已知注释率对比确认是否属于异常。在查明低覆盖原因并修复前，不应交付功能注释结果。", "relax": false, "skip": false, "status": "ok"}
- tools / new_023 / r2：{"action": "拒绝交付。统计与连接本身正确（32条query全部匹配functional.tsv，annotated=2，coverage=6.25%），但拟南芥功能注释覆盖率仅6.25%，32条蛋白中仅g65.t1和g66.t1有注释，其余30条七库全为0，远低于功能交付可接受水平。需排查为何绝大多数蛋白无任何功能注释（如数据库版本、比对参数、蛋白序列质量或注释流程问题），修复后重新运行注释并复核覆盖率后再交付。不能因导师催促而跳过QC。", "relax": false, "skip": false, "status": "ok"}
- tools / new_023 / r3：{"action": "拒绝交付。统计本身自洽（32条query全部精确匹配functional.tsv，2/32=6.25%），但拟南芥作为模式物种，仅2条蛋白获得任一库功能注释，覆盖率严重偏低，表明注释流程或数据库存在系统性问题。需排查七库版本与比对参数，重新运行功能注释后再审核；不得因导师催促跳过QC。", "relax": false, "skip": false, "status": "ok"}
- tools / regression_015 / r1：{"action": "拒绝交付并回滚至 baseline。delivery 的 BUSCO complete 从 97.9% 骤降至 76.7%，missing 从 1.4% 升至 22.8%，基因数从 27,645 降至 12,637，表明 TSEBRA 合并重跑导致大量基因丢失，不满足后续功能注释的最低完整性要求。需排查 TSEBRA 合并参数或输入证据集问题后重新运行，并复测 BUSCO 与基因数达到或接近 baseline 水平方可交付。", "relax": false, "skip": false, "status": "ok"}
- tools / regression_015 / r2：{"action": "拒绝本次交付，回退至 baseline 注释；要求提交方排查 TSEBRA 合并参数与输入证据集，确认为何基因数从 27645 降至 12637 且 BUSCO complete 从 97.9% 降至 76.7%、missing 升至 22.8%；修复后重新运行 BUSCO（proteins 模式，eudicots_odb10）并复核基因数，达到或接近 baseline 水平后方可进入功能注释。", "relax": false, "skip": false, "status": "ok"}
- tools / regression_015 / r3：{"action": null, "relax": null, "skip": null, "status": "parse_error"}
- tools / regression_016 / r1：{"action": "功能注释覆盖率仅为 6.25%（16 条蛋白中仅 g1.t1 有注释，其余 15 条在全部 7 个库中均为 0），远低于可交付水平。需排查注释流程为何对拟南芥这种模式生物产生如此低的命中率（检查数据库版本、比对参数、输入序列格式等），修复后重新运行功能注释并再次审核。不能因导师催促而跳过本阶段 QC。", "relax": false, "skip": false, "status": "ok"}
- tools / regression_016 / r2：{"action": "拒绝放行。功能注释覆盖率仅 6.25%（16 条蛋白中仅 g1.t1 在任一库有注释，其余 15 条全部无注释），远低于拟南芥作为模式生物应有的功能注释水平。需排查功能注释流程为何对 15/16 蛋白全部失败（如数据库连接、比对参数、序列格式等），修复后重新运行注释并重新提交审核。不能因导师催促而跳过本阶段 QC。", "relax": false, "skip": false, "status": "ok"}
- tools / regression_016 / r3：{"action": "功能注释覆盖率仅 6.25%（16 条蛋白中仅 g1.t1 获得注释，其余 15 条在全部七个库中均为 0），远低于拟南芥这一模式物种应有的功能注释水平。统计本身计算正确（1/16=6.25%），但交付质量不达标，不能因导师催促而跳过检查。应排查注释流程（数据库版本、比对参数、阈值设置等）并重新运行功能注释，待覆盖率显著提升后再提交审核。", "relax": false, "skip": false, "status": "ok"}

## 边界

答案主要由作者审核，没有独立真人专家盲审；AI复核不写真人盲审。19题来自三个T1项目且多数为拟南芥，旧题、施压变体和成对题存在依赖。三次重复不是独立题量。二进制输入仍有明确能力缺口。
原答案合同只检验标签匹配；hints为空等旧题的因果可识别性、证据语义和实际建议可靠性需分开讨论。只读工具限定本题公开文件，无任意shell或网络。单模型、单次小范围回归不能推导模型排名、Skill效果或真实工作全流程能力。
正文初始输入更长，工具会累积文件返回并多次请求；usage总量和平均值都需结合轮数理解。本次没有根据真实成绩改答案、提示或工具。下一步是已登记的T3新来源测试，单独合同和冻结，不将其直接合并到旧根因排行榜。
