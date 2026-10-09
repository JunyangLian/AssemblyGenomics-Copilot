# v3七类群来源收集（Python 3.9+，独立脚本）

把本地bench/v3/source_preparation_package.zip上传到服务器~/AssemblyGenomics-Skill/bench/source_preparation_package.zip。包只含v3/server中的脚本、配置和说明，不依赖transfer模块，不包含API key、模型结果、题目答案或原数据。

在服务器执行：

```shell
cd ~/AssemblyGenomics-Skill/bench
python -m zipfile -e source_preparation_package.zip .
python v3/server/prepare_sources.py --config v3/server/prepare_config.json
```

默认从~/临时收集7物种14个gzip原文件；路径取自既有T3记录。默认输出和日志固定在bench_transfer/v3_prepare_t3_r1/bundle/，包含sources/、records/、STATUS、SELECTION、TOOL_VERSIONS、logs/prepare.log、完整MANIFEST.json及MANIFEST.sha256。末尾打印COMPLETE或BLOCKED、缺口、路径和清单SHA；脚本BLOCKED返回exit 2。不要只复制终端输出。

COMPLETE后打包：

```shell
python -m zipfile -c bench_transfer/v3_prepare_t3_r1.zip bench_transfer/v3_prepare_t3_r1/bundle
```

用scp把zip或完整bundle传回本地bench/v3/incoming/，在聊天给路径。agent用python bench/v3/verify_sources.py <收到的目录或bundle目录>重新计算这个新运输包的SHA，并核对本地7来源配置；全部一致才登记SOURCE_RECEIPT并使用。不是对所有历史产物重新哈希。

如果BLOCKED，也可以传回完整诊断bundle；先根据缺口修正路径或补齐真实文件，不能编造数据。源位置改动时只修改source_root或配置中已有T3文件的实际文件名；本地验收配置必须同步审阅，不可换accession或加入其它项目。更换来源/文件后保留旧包，指定新目录，例如：

```shell
python v3/server/prepare_sources.py --config v3/server/prepare_config.json --output-root bench_transfer/v3_prepare_t3_r2
```

可重复执行：首次边复制边算源SHA，验证复制品gzip校验/格式/计数；重复时用源和复制品的路径/大小/mtime签名复用记录，不重读原文件或重新跑检查。这个缓存不是对同大小同mtime的蓄意改写进行密码学验证；接收端仍严格重算运输包SHA。源或复制品签名变化时报缺口，不静默覆盖旧原文件。gzip原字节保留，新JSON/日志用UTF-8+LF；本阶段不是注入脚本的跨平台逐字节复现实验。

记录工具为Python/gzip标准库版本与平台；不用bash/awk、pip安装、外网或生信工具，不运行组装/注释/BUSCO/基线，不访问环境API key。计数及in_band不等于标准答案。运行后还有独立审题和题目冻结阶段。
