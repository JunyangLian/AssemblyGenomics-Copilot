# v3阶段2汇报：七类群来源准备工具

2026-10-09。用户已确认七类群各一代表，执行到可上传的准备工具与本地验收入口，实际服务器源收集尚未执行。

## 1. 文件与完成内容

- server/prepare_sources.py、prepare_config.json、README.md：14个T3 GFF/FAA白名单，固定输出日志，gzip/格式读取，工具版本，完整SHA清单，首次复制哈希和重复缓存，缺口生成BLOCKED包；标准库独立脚本，不依赖transfer。
- verify_sources.py：本地新包所有payload重新哈希、清单、14来源/7类群、复制回执与配置匹配后才登记SOURCE_RECEIPT；实际尚无该回执。
- tests/test_source_intake.py：8个测试玩具文件的完整收集、缓存不重读、缺源、截断gzip、篡改、源改变新目录、路径边界和批准选择一致性；不用于题库。
- SOURCE_SCOPE_REVISION、来源提案/请求/候选表、STAGE_STATUS、README/CHANGELOG：七类群当前选择，原三来源历史归档。18项私有候选设计不是最终题数或答案。
- source_preparation_package.zip与PACKAGE_RECEIPT.json：仅3个白名单服务器文件，可重复生成同一zip字节；包无原数据、模型结果、答案、凭据。

7来源14文件历史大小122,240,797 B (116.58 MiB)。mock/API/规则/原分析0；不修改v1/v2冻结行为，不重扫其它历史原源。

## 2. pytest与包验证

8项针对性测试通过；全仓`python -m pytest -q`：**341 passed in 189.08s**，现有测试全部通过。准备zip双次生成字节相同、白名单3文件解压后逐字节匹配，并通过Python3.9语法检查。仅本地玩具源测试，Linux真实运行仍待用户执行，不能称已完成服务器来源验收。

## 3. 缺口与交接

用户上传准备zip至服务器bench/v3并按server/README运行，传回完整结果bundle/zip，本地运输核验通过才能构题；缺口回传诊断包而不是编造数据。原终端no_band警告与in_band表矛盾保留，不作为PASS依据。独立生信审核人未指定；可先准备来源但独立审核不称完成。最终题数、具体标准答案、门槛与新API预算均未确认；本阶段在源回传处停下。
