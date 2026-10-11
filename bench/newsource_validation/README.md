# 新来源 QC 小规模验证：准备阶段

2026-10-11。用户同意采用两个分开的范围：主线为 5–6 个未用于模型、提示和工具调优的来源、10–12 道 QC 题；BixBench 仅做小规模外部复现可行性检查。这里是新版本准备，不修改历史答案、分数或冻结实现。

**当前：已选六个 T3 accession，计划十二题；服务器来源待回传，尚未构题、冻结答案或调用模型。** 历史 T3 规则统计已看过，因此不能称为对原规则也完全未见的新数据。模型预训练暴露未知。

## 固定的来源请求

筛选仅使用既有位置与大小记录：排除 Git 已跟踪题目元数据中的 accession、T1 三物种和不完整配对，按类群选择记录中最小的完整 GFF/FAA 配对。不按历史 in_band/no_band 或新模型成绩筛选。选择细节及旧题元数据身份见 [SOURCE_AUDIT.json](SOURCE_AUDIT.json)。

| 类群 | 物种 | Accession |
|---|---|---|
| 辐鳍鱼 | Syngnathus floridae | GCF_059516105.1 |
| 真菌 | Saccharomyces kudriavzevii | GCF_947243775.1 |
| 昆虫 | Drosophila melanogaster | GCF_000001215.4 |
| 哺乳动物 | Monodelphis domestica | GCF_027887165.2 |
| 线虫 | Trichinella spiralis | GCF_000181795.1 |
| 植物 | Theobroma cacao | GCF_053813885.1 |

服务器记录合计 105,630,300 字节（约 100.74 MiB），不是已核实的当前文件大小。六个来源目前均未在本地验收。每来源拟一正常题、一确定性格式/连接故障题，共 12 题；三类故障的分配在 [PROTOCOL_DRAFT.md](PROTOCOL_DRAFT.md)。没有 BUSCO、覆盖率或真实事故原因类新题的来源，不能从 GFF/FAA 凭空构造这些统计或历史。

## 服务器准备与传输

上传本目录的 `source_request_package.zip` 到 `~/AssemblyGenomics-Skill/bench/`。包仅有本次配置、命令说明及已验证的标准库收集脚本，不含 API key、大数据、题目或答案。

```bash
cd ~/AssemblyGenomics-Skill/bench
python -m zipfile -e source_request_package.zip .
python newsource_validation/server/prepare_sources.py --config newsource_validation/server/prepare_config.json --bench-root .
```

来源默认是已有记录中的 `/home/Lianjunyang/临时/`。输出固定为：

```text
~/AssemblyGenomics-Skill/bench/bench_transfer/newsource_validation_sources_r1/bundle/
```

脚本仅复制这十二个来源文件；复制时一次性计算原始 SHA-256，记录工具版本、格式计数、日志、完整清单。重复运行以路径/大小/mtime 回执复用，不反复扫描原始来源哈希。任何缺文件或不完整 gzip 明确列为缺口，不自动替换物种、不下载或重跑注释。

将整个 `bundle` 用 scp 传回本地 `bench/newsource_validation/incoming/`，之后本地一次性核验运输清单，核验前不构题。不要只传终端摘要。当前包保留完整 GFF/FAA，是为了在锁定消费契约后本地提取完整 Parent 闭包与对应蛋白；题面最终只使用小片段。

## 后续边界

1. 旧开发题上完成离线信息覆盖、预算和工具参数检查，锁定新提示、工具、评分与来源选择；不使用新测试模型结果调参。
2. 收到真实来源后按事先规定构造规则提取，无法满足时记录缺口；不依据模型答错后更换题。
3. 用户审核候选答案；Windows/Linux 注入复现；确认后登记所有 expected 哈希。
4. 单模型、正文/工具各三次，十二题共 72 条观测；付费调用另行给出完整 token/费用与授权。目前没有新 API 预算。
5. 一次测试后按原冻结口径报告。失败保留分母；新增调优进入后续版本。

外部轨见 [BIXBENCH_FEASIBILITY.md](BIXBENCH_FEASIBILITY.md)，现有错误分类及演示见 [ERROR_CATALOG.md](ERROR_CATALOG.md)。独立 agent 审核只能记作 AI 审核。
