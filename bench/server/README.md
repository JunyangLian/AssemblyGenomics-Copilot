# 第一轮：仅准备已有 T1/T3 来源（规格 1.2）

本工具只核对、截取已有文件，不下载 SRA、不运行 BUSCO/组装/注释、不执行 A/B/C。产物限定为 T1 拟南芥、线虫、酵母和已验证 T3 的 GFF/FAA。文献可继续作为正常范围的答案依据，不作为可见运行产物。上一版的油菜、褐篮子鱼及下载入口已移除。

## 配置与来源范围

复制 prepare_config.example.json 为 prepare_config.json（不用密钥）。默认来源依据用户提供的路径及既有 T1 SOP 记录；服务器当前文件仍须核验，不能把历史记录当作现存证据。{project}/{home} 在服务器展开。

- source_scope 固定 T1_T3；cohort 仅四个值：T1_arabidopsis、T1_celegans、T1_yeast、T3。每个原文件必须位于对应 scope_roots，指向其他项目即报缺口。
- 既有快照来源先完整哈希原产物，再按 MANIFEST.txt 定位同字节副本；snapshot_path 默认 null。原产物、快照、清单不一致则停止该来源。摘要 glob 必须恰好匹配一个文件，多份结果不猜身份。
- T1 原读段可能未进入 480MB 快照：仅在已记录的 yeast_test/0.Raw_Data/rnaseq/ 两个迁移前后位置查 WT_Rep1/2 各 R1/R2。配置明确 snapshot_required=false，原文件前后全量 SHA 核对，并与 T1 RNA-seq provenance 输入哈希绑定；截取前 64 条真实记录，不生成读段。子集再检查各样本双端标识；缺文件或来源记录就报告，不下载补齐。
- T3 默认从既有 t3_batch_report.tsv 的 in_band 条目中，选快照和原目录都保存完整 GFF/FAA 的一对，按合计原文件大小最小、accession 排序打破平局。可填 t3_accession 固定选一个已有批次成员；未验证或只有 FAA 的条目不选。文件名被改写、复制版本歧义或对应原文件缺失时报告，不能猜配对。
- T3 历史判定表和汇总只作私有身份核验；其中 in_band 等判定不能进入模型题目，模型只看白名单产物。该来源选择在模型调用前记录/审核，不能根据结果改选。

脚本只传实际题目需要的 T1 QC/provenance、真实基因组小片段、指定 TSEBRA 事故和终稿 GTF 片段/全量计数、BUSCO 既有摘要、hints/GFF 片段、功能表前 1,024 条记录及按 query 匹配的完整蛋白、线虫正常终稿、酵母段 1/原读段，以及一对现有 T3 GFF/FAA。不打包整个快照，不重跑生信流水线。正常对照的拟南芥重复产物与酵母 hard_negative 分开。

GTF 全量 gene_id 计数与截取行范围分开记录；完整原产物统计不能冒充片段统计。T1 DNA FASTA 前缀保持原序列名/坐标，末条序列可为前缀；功能蛋白按 query 选择完整记录。最终题目分母/字段在阶段 2 本地重算与核验。

## 执行与固定输出

用现有 scp 通道上传 bench/ 脚本和配置，保留 bench/server/prepare_sources.py 与 bench/transfer.py 的相对布局。不要上传 .env/API key。Python 3.10+，仅标准库；此轮不需要新增计算预算或可执行生信工具。

```bash
mkdir -p ~/bench_transfer/v1_prepare_t1t3
python ~/AssemblyGenomics-Skill/bench/server/prepare_sources.py --config ~/AssemblyGenomics-Skill/bench/server/prepare_config.json
```

旧 --inventory-only 参数保留兼容，但此版本所有操作本来就离线；不再自动增加“下载/计算未执行”的缺口。真实来源齐全才 complete（退出 0）；存在必需缺口则 blocked（退出 2），仍回传摘要、清单和已核验来源。可选来源缺失作为记录保留，不等于该题证据足够；阶段 2 还须逐题检查。

输出固定 ~/bench_transfer/v1_prepare_t1t3/bundle/：

- STATUS.json：cohort、真实路径、原产物与子集 SHA、截取、题号和缺口。
- sources/：明确选择的小来源包。
- inventory.json、snapshot_record.json、snapshot_manifest.txt、t3_selection.json；原读段齐全时另有 t1_read_pairing.json。
- config.json、python_version.json、scripts/、logs/prepare.log。
- MANIFEST.json 和 MANIFEST.sha256：所有回传文件的完整 SHA/大小；后者包含前者哈希，避免自引用。

Python 版本实测记录；历史生信工具版本/命令从原 provenance/日志回传，不能用今天安装的版本替代原运行。末尾打印状态、来源数量、文件数、字节数、清单哈希及缺口。不打印环境或密钥。

相同配置重复执行得到相同截取字节与清单；已存在且内容不同的 payload 拒绝覆盖，不删除任何数据。脚本、源数据或选择改变时，指定新的固定 output_root（例如 v1_prepare_t1t3_r2），保留旧包。本轮的 output_root 已与旧 SRA/BUSCO 准备目录分开。

## scp 回传与本地验收

回传完整 bundle 目录，不复制终端输出。SERVER_ALIAS 使用你已有的 scp 主机别名：

```powershell
New-Item -ItemType Directory -Force -Path bench/incoming | Out-Null
scp -r SERVER_ALIAS:~/bench_transfer/v1_prepare_t1t3/bundle bench/incoming/v1_prepare_t1t3
python bench/verify_sources.py bench/incoming/v1_prepare_t1t3 --receipt bench/incoming/v1_prepare_t1t3.verified.json
```

本地逐文件重算 SHA/大小，核对两份清单，拒绝额外/遗漏文件、重复条目、越界路径和 symlink。回执写在包外。哈希一致但服务器 blocked 仍不准构题；complete + 验收成功后才能进入逐题来源核验。缺 T1 原 FASTQ 就列缺口，由用户在冻结前决定，不自行删题、扩源或替题。

阶段 2 的本地/服务器独立重建命令随注入脚本交付，两端 task/artifacts 哈希必须一致；第二轮 A 脚本仅在答案冻结后提供。所有模型 key 只在本地环境变量，本轮没有模型调用。
