# v3阶段1汇报：错误整理与来源盘点

2026-10-09。仅执行已授权设计阶段，不进入构题或新运行。

## 1. 完成内容（文件清单）

- README、DESIGN_DRAFT、ERROR_TAXONOMY、V2_AUDIT_SUMMARY、V2_OBSERVATION_AUDIT：648条既有A/四模型观测分类；六类诊断及可答性、证据、处置/风险指标和A适配提案。自动计数只覆盖冻结判定/根因与状态；证据与范围尚未批量人工评分。
- SOURCE_AUDIT、SOURCE_INVENTORY、T3_CANDIDATES、SOURCE_SPLIT_PROPOSAL、T3_TRANSFER_REQUEST：34本地来源，27物种报表、25套服务器历史完整配对，本地只1套已用T3。提出3新来源6文件，合计21,444,811 B。仅定位/引用原清单，不重扫原源SHA。
- CANDIDATE_REVIEW、INDEPENDENT_REVIEW_PROTOCOL：16项私有候选设计，所有人类审核意见空白。未生成task/artifact/expected，不代表最终题数或已审核答案。
- CHANGELOG、STAGE_STATUS、AUDIT_MANIFEST：阶段及文件身份记录；v1/v2原内容不改。

本阶段mock/API/A规则均0，没有新下载或分析流程。

## 2. pytest

全仓`python -m pytest -q`：**333 passed in 197.33s**，现有测试全部通过。CSV行数/计数/空意见/来源角色与记录大小、无cases/expected及所有新文件LF另作一致性核对。

## 3. 缺口与需要用户决定的事项

1. 本地没有未用于开发的新T3原配对。建议确认Arxiozyma heterogenica GCF_036370985.1、Strongyloides ratti GCF_001040885.1、Anopheles gambiae GCF_943734735.2三套为封存候选（来自T3），共约20.45 MiB。确认后下一阶段统一写服务器准备脚本，用户执行并回传6文件最小包。当前位置只是历史服务器记录，不能提前声称原文件可达；不拿旧切片代替缺源。
2. 需要一位未参与开发的生信人员独立审题。建议由用户安排；若暂无人选，允许继续准备来源，但标准答案独立验证保持缺口，不能宣称完成。当前设计表含私有注入信息，不直接给盲审者。
3. 24至30题为规模目标、35为上限；最终题数/新门槛/长度对照/模型和预算后续再确认。本阶段不要求填数或批准真实调用，不恢复Kimi/GLM。原规则只改v3适配角色，不新增覆盖规则。

本阶段完成后停下，等待来源分组及审核安排，不进入构题。
