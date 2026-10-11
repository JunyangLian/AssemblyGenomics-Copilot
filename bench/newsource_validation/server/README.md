# 新来源收集请求

本脚本与 `bench/v3/server/prepare_sources.py` 字节一致，本轮只更新六来源配置，不修改旧实现。

从服务器 `~/AssemblyGenomics-Skill/bench/` 执行：

```bash
python newsource_validation/server/prepare_sources.py --config newsource_validation/server/prepare_config.json --bench-root .
```

`prepare_config.json` 固定十二个既有 T3 文件，默认位于 `/home/Lianjunyang/临时/`。输出为 `bench_transfer/newsource_validation_sources_r1/bundle/`，包含 source、records、STATUS、工具版本、日志和 MANIFEST。不调用外网或模型，不扫描其它来源，不运行分析流程。

首次复制时计算来源 SHA，后续以路径/大小/mtime 回执复用。若缺文件，请返回 bundle 内 STATUS，而不是手动造文件或换物种。若服务器布局改变，仅修正本轮配置的 source_root，并保留原配置和变更说明；不要重新修改旧版本来源记录。

将完整 bundle 用 scp 传到本地 `bench/newsource_validation/incoming/`。本地须核验运输清单后才可使用；当前没有新题或答案。
