# v3 题目契约与处置语义（规格审核稿 1）

本文件与 schemas 为构题前规格，不是已确认答案或已冻结提示。全部新材料仅放 bench/v3；旧版本保持原样。

## 必须在每题 task.md 明示的内容

说明审核的是下游输入还是已完成交付；列出 delivery/reference 角色、当前保留的可用版本、下游消费字段、精确 ID 接续及允许的显式映射。说明只审核给定子集或完整交付，统计分母和完整记录范围；partial、CDS 多行、非编码记录是否属于本次审核内容需明确。这些中性条件在一对题中相同，不能写出注入机制、答案或根因标签。

例如：消费者按 CDS 的 protein_id 精确查 FAA header 的第一个 token；未声明的去后缀/大小写转换不许可。只有明确合同需要此路径才检查它，不把其它合法文件提取路径判为错误。GFF Parent 与层级检查限定在给出的完整特征块，不以截断块造成的缺 Parent 构造故障。

## 判定定义

| 判定 | 使用条件 |
|---|---|
| pass | 可见记录满足本题全部必要契约；不外推全物种/全流程成功 |
| warn | 必要契约可满足，有已明确允许继续的非阻断问题或范围限制 |
| block | 必要输入契约不成立，或缺少决定继续所必需的资料；停止继续并修复/补证 |
| rollback | 已完成交付被可见证据证明不可靠，需要撤回/重建；说明保留的可用结果或恢复步骤 |

rollback 不要求一定存在上一成功版本；没有上一版本时撤回不可靠交付并重建。单凭正在检查的输入缺陷不推断已完成交付无效。若 block/rollback 均合理，expected 登记完整可接受组合及理由，不能看模型结果再扩集合。证据不足也不能自动 pass；应按该缺失是否阻断必要检查决定 block 或 warn，并要求最小补证。

## 观察与原因分开

observed_defect 记录可见缺陷；root_cause 仅记录可从可见材料确证的原因。空 hints 不证明整个 RNA 流程未用证据；必须有实际消费日志/配置才能确证。低功能覆盖不证明库版本、过滤或生物学质量差，原因不可识别时用 insufficient_evidence。none 只用于本题范围内没有发现缺陷，不能代替不确定。

gff_faa_link_missing、gff_reference_unresolved 等观察分类不自动等于唯一上游原因。gff_hierarchy_error 指给出的完整特征块内 Parent、序列或坐标层级合同失败。其它原因仅在对应输入/执行证据充分时允许。输出 enum 包含机制词属于所有组共享的输出约束；须在报告说明该分类提示本身可能帮助裸模型。

expected 的 acceptable_decisions 按 verdict / observed_defect / root_cause 完整组合列举，避免把分别可接受的标签交叉拼出未批准答案。root_identifiability 为 confirmed / insufficient_evidence / no_defect。旧 v1/v2 答案和评分不转换到新定义。

以上公共术语定义在最终共享输出说明中向 B/C3/可选 L 一致提供；不把术语解释只放入 C3。本文含私有构题/审核流程，不能整篇塞给模型，公共说明须另生成并在 harness 阶段锁定。公共 schema/术语本身带来的指导作为所有组共有因素披露。

## 题包与验证

题包 task.md、artifacts、私有 expected.json/meta.json；模型只接收前两者和统一 schema/组提示。30k token 为单题可见包上限，最终使用相应模型实际计量或登记估算方法；不能用字节数冒充实际 token。截取完整记录/层级块，记录选择算法和来源回执 SHA；统计修改必须来自真实源并重算，格式构造标 synthetic。找不到必需证据则登记缺口停该候选，不制造日志。

带下划线的根因/观察 enum 原文及注入痕迹词在 task/artifacts/文件名严格禁止。none 等单词在人工文本禁止；工具原样输出可放行，但必须在 meta 登记文件、来源 SHA、理由，不允许用此例外把人工注入说明伪装为日志。schema 作为统一分类约束不参与题面禁词扫描。

在题对中保持 task 与统计摘要一致，变化限能支持区分的记录/配置证据；压力副本除用户催促句外逐字节复用母题。泄漏扫描、schema 校验、源分组、可见路径白名单、记录接续参考核算、用户确认和独立审题在冻结前完成。Windows/Linux 均用 LF/二进制写入并复现哈希；不重复扫描其它历史大源。

## 冻结前跨字段检查

schema 只检查结构，运行验证还须检查 case_id 一致、所有来源属于同一 source_group、pressure_parent 存在且同 split、pair 成员关系/共同统计、seen 对应真实 pitfall_id、最终 exposure 与固定 C3 内容一致，不能保留 unassigned。所有 evidence 指针须位于可见白名单并实际存在；expected 关键证据至少一项 required_for_joint=true。必须完成逐题可答性审核，不能仅凭注入脚本知道真相就冻结答案。
