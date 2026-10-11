# T3 七来源 Inspect 测试草稿

2026-10-11。14题、7个同源题对，已构造和离线验证；答案未获批准、未冻结，没有真实模型结果。沿用已验收的 `bench/v3/SOURCE_RECEIPT.json`，只读取其中七套T3 GFF/FAA；没有重跑注释或引入其它本地物种。不是旧v3 28题计划的自动替代。

| 来源 | 正常题 / 变体 | 唯一改变 | 原始特征行 / 蛋白条数 |
|---|---|---|---|
| Arxiozyma heterogenica，GCF_036370985.1 | t3_001 / t3_002 | 一个CDS所有片段的protein_id版本后缀 | 12 / 2 |
| Strongyloides ratti，GCF_001040885.1 | t3_003 / t3_004 | 一条mRNA的Parent | 12 / 2 |
| Anopheles gambiae，GCF_943734735.2 | t3_005 / t3_006 | 一个CDS所有片段的protein_id版本后缀 | 26 / 3 |
| Carica papaya，GCF_054855325.1 | t3_007 / t3_008 | 一条mRNA的Parent | 20 / 2 |
| Ornithorhynchus anatinus，GCF_004115215.2 | t3_009 / t3_010 | 一个CDS所有片段的protein_id版本后缀 | 40 / 3 |
| Gallus gallus，GCF_016699485.2 | t3_011 / t3_012 | 一个CDS片段移到自身mRNA末端之外，片段长度不变 | 41 / 3 |
| Zeus faber，GCF_960531495.2 | t3_013 / t3_014 | 同上 | 22 / 2 |

拟定判定：每对正常题为pass；变体为block。protein_id不能接续为文件级id_mismatch；Parent缺失或父子区间不满足为文件级gff_hierarchy_error。这些只是候选答案，具体证据见各题expected.json及[审核表](REVIEW_SHEET.csv)。作者AI草拟，独立审核pending，没有真人专家盲审记录。

## 输入合同与来源

每题审核待启动的下游输入，两套完整编码gene块及所有子记录、关联完整FAA蛋白序列。Parent必须接续、类型正确、同seqid/链、子闭区间位于父内；CDS的protein_id必须与FAA首token精确连接。不按Name或CDS ID兜底，不去版本号。允许异构体、多片段CDS和partial=true，不能据此推断全长或生物学质量；真菌和线虫原始块确实含partial=true。

截取算法固定为GFF顺序中前50个满足闭包、大小及多片段条件的候选；保留其中最先能接上完整FAA且总公开材料≤30,000字节的两个块。不是按模型成绩选样，也不是注释产物总体的随机样本。GFF原特征行照录、FAA完整原序列按60字符LF重排；基因数、蛋白数、残基数由子集直接计算，不借用全物种统计。所有格式子集标synthetic=true，不声称生成新生物学数据。

`selection/SOURCE_SUBSETS.json`保存私有原子集及来源绑定；meta保存运输包源路径、原服务器路径、已有SHA-256、选样/变换方式及来源凭据SHA。没有反复重扫完整源哈希。生成和验证核对Parent/区间/连接并进行泄漏扫描；参考核算只用于候选答案校验，不是A组新规则，也不向模型提供决定工具。

同源题对的task、FAA、计数逐字节相同，仅GFF指定字段改变。模型输入只含task、artifacts，以及共用说明/schema；不含题号、pair_id、meta、expected或私有子集。私有标准答案作为Inspect Sample.target仅在评分端使用；原生日志会含target，不能作为未来模型输入。

## Inspect条件与评分草案

inline提供全部公开正文；tools提供任务和公开文件索引，由现有五个只读函数访问不可变公开字节。没有添加GFF缺陷判定工具、shell或网络能力。两条件使用同一新七字段schema及共用处置定义；不包含Skill知识包，不对应历史B/C条件。新任务区分observed_defect与可确证文件级root_cause，不改变T1冻结的六字段口径。

tools最多5次收集生成（每次512输出token），随后关闭工具并单独提交JSON（2048）；最多6次生成，480秒。取消旧message_limit=16，以轮数限制运行；一次生成可产生多条工具回复，消息数不能当生成次数。[Inspect官方限制定义](https://inspect.aisi.org.uk/reference/inspect_ai.util.html)与[工具解析](https://inspect.aisi.org.uk/reference/inspect_ai.solver.html)说明了该区别。原工具输出分页/体积限制仍适用；新真实运行还需独立的物理请求/累计token预算保护。原T1受限失败与分数保留。

主分析单位拟为题：每题3次中至少2次完整匹配某个可接受的verdict/observed_defect/root_cause组合，才算决定共同成功；逐字段正确率和观测层结果另报。解析错误或缺失槽位留在分母中；配对成功需两题都达到题级共同成功。另按7个来源组报告，重复与同源题对不视为独立来源。

严格schema及引用位置存在仅证明格式/定位；自动决定评分不证明证据语义和action安全。这两项需单独人工或明确标注的AI编码复核；自报booleans不作安全保证。新来源不等于模型预训练未见，连接机制也可能在旧指导中相关出现。meta的guidance_exposure目前unassigned，冻结前解决；不用于旧H1–H3检验或声称Skill提升。T1与本版合同、schema、来源不同，分开报告。

## 已做的离线验证

- [VALIDATION.json](VALIDATION.json)：14题schema、来源绑定、引用位置、连接参考事实、泄漏扫描和成对表面一致性通过。
- [MOCK_RECEIPT.json](MOCK_RECEIPT.json)：28条原生模拟观测、98次模拟生成、350条实际Python工具回复，28条最终JSON合法，零供应商调用；脚本回答不读取target，不计作质量成绩。另有3次模拟生成的旧16消息上限负对照，复现最终提交未到达。
- [WINDOWS_REPRODUCTION.json](WINDOWS_REPRODUCTION.json)：实际展开分发包重新生成，14题、84个题目文件哈希一致；重复打包逐字节一致。
- Linux复现尚待用户执行回传，不能写成已通过。没有FROZEN或真实API入口。

本地命令（无需密钥）：

```powershell
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.t3_packets build
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.t3_task --prepare
bench/inspect_adapter/.venv/Scripts/python.exe -m bench.inspect_adapter.t3_task --mock
bench/inspect_adapter/.venv/Scripts/python.exe -m pytest -q
```

## 服务器复现与下一步

将[复现包](reproduction_package.zip)传到 `~/AssemblyGenomics-Skill/bench/inspect_t3_reproduction_package.zip`，在服务器执行：

```bash
cd ~/AssemblyGenomics-Skill/bench
python -m zipfile -e inspect_t3_reproduction_package.zip .
python t3_reproduction/reproduce_cases.py
```

脚本只需Python和jsonschema（缺依赖时先用 `python -m pip install jsonschema`）；无需Inspect或API key。重建所有题目，比较参考manifest，固定输出 `bench_transfer/inspect_t3_cases_reproduction/bundle/`，登记Python/平台版本及完整SHA-256清单，可重复执行，不扫描原大文件。请回传该bundle目录。

此复现证明同一运输子集在两端生成相同字节，不是再次验证完整原GFF/FAA提取。当前包含私有候选答案构造逻辑，专用于复现/审核，不能交给被评测模型。

待Linux回执验收及答案审核后，再登记guidance分组、冻结答案/提示/实现并单独批准真实预算。[PLAN.draft.json](PLAN.draft.json)仅拟定14题×2条件×3次=84槽位，最多294请求、输入代理150万、输出申请279,552；不是已批准调用。初始正文输入代理均值约4,855，工具索引约1,622，累计工具声明和回复另计。费用待价格复核；不继承T1剩余额度。
