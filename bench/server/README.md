# 第一轮：来源准备与回传

这是阶段 1 修订附带的服务器准备工具，不构造题库，不运行 A/B/C，不产生 expected/FROZEN。脚本尚未在你的真实服务器运行；配置里的 null 是明确缺口。第一轮只重跑允许的油菜 BUSCO proteins，不重跑组装、RNA 比对或注释。

## 配置

复制 prepare_config.example.json 为你服务器上的 prepare_config.json（不含密钥）。按实际文件修正 origin；默认路径依据你提供的记录，不宣称文件名已实测。{project}/{home} 在服务器展开；每个 glob 必须恰好匹配一个文件，多份 summary 不猜哪份正确。snapshot_path 通常保持 null：脚本按完整原产物 SHA 在快照 MANIFEST.txt 中定位同字节副本；重复同字节副本选择排序第一项，原路径仍明确记录。旧错误日志不当作现有缺失。

必须补充：

- sra.runs：两个不同 BioSample 的公开酵母双端 run。已有项目记录 SRR40431829/28 可作为待确认候选；脚本通过 ENA 实际元数据核验，当前未核验。spots 默认仅前 1,000 spots，是子集大小，不是 QC 阈值。
- busco.protein_fasta、protein_set_description、publication、lineage、executable、hmmsearch、cpu、memory_gib。明确甘蓝型油菜发表数据版本、代表蛋白/多转录本口径、引用与用户安全预算；不沿用其他项目预算。谱系必须已本地安装。需要的 normal-range 文献具体数值/定位仍在阶段 2 人工核对，不由 BUSCO 输出替代。
- siganus_agp/statistics/run_record/component_fai：同一真实参考引导挂载运行的 AGP、挂载统计、配置/日志及组件 FASTA 索引。统计文件若不是 JSON，改 extension 与方法；配置不能制造统计。新增来源 snapshot_required=false 时直接读真实原文件，前后核对完整 SHA。
- refseq_gff/proteins：选定一个小 RefSeq 正常物种的真实原文件。快照中必须有与原路径哈希相同的副本；不要临时增加大量物种。
- 可选的 arab_repeat_library_record、arab_prior_configuration：填真实库版本/事故配置记录路径；如果 QC/原 provenance 没有这些事实，阶段 2 仍须补源。酵母原运行命令和版本从 provenance/日志取，缺失时不能推测。

既有来源 snapshot_required=true：原文件、快照副本、清单三者 SHA 相同才截取。origin 的完整 SHA 与准备子集的 SHA 分别记录在 STATUS.json，不互相替代。相同源两次读取后哈希改变立即报缺口。

仅传指定段 1 QC/小片段、终稿与指定事故的 GTF 摘要/片段及 BUSCO summary、hints/GFF 片段、功能前 1,024 行及其完整匹配蛋白、相关 provenance、酵母段 1、一个 RefSeq 小对照、挂载记录，以及新 SRA/BUSCO 小输出。GTF 总基因 ID 数由原文件全量扫描获得，片段不是全量计数依据。FASTA DNA 前缀保留原坐标；蛋白按 query 选完整记录。完整来源的统计与子集分母分开，阶段 2 必须对最终可见数据重算一致口径。

## 执行与固定输出

用 scp 上传 bench/ 下的脚本和配置到服务器。只上传准备工具；不用上传本地 .env 或密钥。下面 repo 路径按你的实际位置替换。

```bash
mkdir -p ~/bench_transfer/v1_prepare
python ~/AssemblyGenomics-Skill/bench/server/prepare_sources.py --config ~/AssemblyGenomics-Skill/bench/server/prepare_config.json --inventory-only
```

inventory-only 核对与截取已有文件，生成 inventory、来源/缺口记录和 SHA 清单；不下载 SRA、不跑 BUSCO，状态必为 blocked，退出 2 是预期结果。可先回传这一包，让本地检查实际布局后修正配置。补齐配置后运行：

```bash
mkdir -p ~/bench_transfer/v1_prepare
python ~/AssemblyGenomics-Skill/bench/server/prepare_sources.py --config ~/AssemblyGenomics-Skill/bench/server/prepare_config.json
```

固定输出 ~/bench_transfer/v1_prepare/bundle/，工作目录为同级 work/。bundle 内：STATUS.json（来源路径、两类哈希、截取、缺口）、inventory.json、config.json、snapshot_manifest.txt、python_version.json、sources/、sra/、busco/、logs/、脚本副本和 MANIFEST.json/MANIFEST.sha256。末尾打印状态、文件数、大小、清单哈希与缺口。所有可回传文件均入清单；清单自身不能递归哈希，MANIFEST.sha256 包含 MANIFEST.json 哈希并覆盖其余文件。

重跑会核验完成的 SRA/BUSCO 缓存，不重复计算、不覆盖不同的 payload、不删除数据；相同输入的截取字节一致。配置、工具或输入改变，或一次工具失败留下不完整目录时，脚本拒绝复用，需要指定新的固定 output_root（如 v1_prepare_r2），保留旧输出。缺口仍返回可检查的 blocked 包；不能将“打包成功”视为“题库已齐”。工具结果日志保留原文，准备日志不含任何环境/密钥转储。

SRA 首先访问 ENA 元数据检查外网和身份，再使用 fastq-dump 的 spot 范围参数。版本与 --help 原文入日志；安装版本不支持范围则停止，不改成完整 fasterq-dump。范围调用可能使用 SRA Toolkit 自身缓存，不能保证网络传输量等于子集大小；此处不调用完整 prefetch。NCBI 文档说明 fasterq-dump 不支持 min/max spot 范围：[SRA Toolkit 官方文档](https://github.com/ncbi/sra-tools/wiki/HowTo:-fasterq-dump)。

BUSCO 使用 -m proteins、明确本地谱系、--offline、指定 CPU，并关闭运行统计上传（5.6 以前版本没有此上传功能）；无法确认版本/关闭上传则停止。记录 BUSCO/HMMER 版本、输入 SHA、整个谱系文件清单 SHA、命令和结果 SHA；只传 summary、full_table、missing list 和主日志，不传 HMM/序列目录或整个蛋白集。memory_gib 同时约束每进程虚拟地址空间，并每 0.25 秒检查整个 Linux 进程组的 RSS 总和，超预算终止该作业；采样间隔内可能短时越界，共享页求和可能保守多算。CPU/内存须由用户按公用服务器情况选定，较紧上限可能导致运行失败。BUSCO 参数口径见[官方指南](https://busco.ezlab.org/busco_userguide.html)。

## 外网受限时

blocked 包中明确保留外网/元数据/工具错误。允许你在本地安装好 SRA Toolkit 后运行同一套子集下载逻辑（不涉及模型 API）：

```powershell
New-Item -ItemType Directory -Force -Path bench/local_sra | Out-Null
python bench/server/download_sra.py --config bench/server/prepare_config.json --output-root bench/local_sra
python bench/verify_sources.py bench/local_sra/bundle --receipt bench/local_sra/verified.json
```

将完整 local_sra/bundle/ 用 scp 上传到服务器；把 sra.uploaded_subset_bundle 填成其服务器绝对路径，重跑第一轮。服务器重新验清单、配对记录与公有元数据、不同 BioSample、spot 选择及下载命令记录，然后使用上传的真实子集，不再访问外网。上传损坏或缺记录的裸 FASTQ 不会放行。

## scp 回传与本地验收

用现有 scp 主机别名传回整个 bundle 目录，保留目录结构；不要只复制终端输出。以下 SERVER_ALIAS 是你已有的主机别名占位符：

```powershell
New-Item -ItemType Directory -Force -Path bench/incoming | Out-Null
scp -r SERVER_ALIAS:~/bench_transfer/v1_prepare/bundle bench/incoming/v1_prepare
python bench/verify_sources.py bench/incoming/v1_prepare --receipt bench/incoming/v1_prepare.verified.json
```

本地重算每个文件的 SHA/大小与两份清单，拒绝额外/遗漏文件、重复条目、路径越界或 symlink；记录验收 SHA。回执写在 bundle 外，避免改变其清单。哈希一致但服务器状态 blocked，仍不准用于构题；阶段 2 从 complete 包及成功验收回执开始。完整准备包仍需逐题审查来源足够与否，不能替代生物学核验。

阶段 2 的独立临时目录重建以及服务器复现命令将在注入脚本完成后提供；两端比较 task/artifacts 字节哈希，私有时钟/绝对路径日志不混入题目。第二轮 A 服务器脚本在答案冻结后另交付，不在此处提前执行。
