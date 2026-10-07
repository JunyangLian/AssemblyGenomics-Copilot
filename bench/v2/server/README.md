# v2阶段2：服务器复现

上传本地`bench/v2/reproduction_package.zip`到服务器的`~/AssemblyGenomics-Skill/bench/v2/reproduction_package.zip`。包只含已冻结v1回归材料、纯Python构题代码、C2与v2比较清单；不含模型响应、API凭据或规则执行入口。代码依赖明确打包，避免先前缺少transfer模块的问题。

服务器执行：

```bash
cd ~/AssemblyGenomics-Skill/bench
python -m zipfile -e v2/reproduction_package.zip .
python v2/server/reproduce_cases.py
```

默认读取先前已验收来源包`bench_transfer/v1_prepare_t1t3_r3/bundle`。若已将来源包移动，请给脚本加`--bundle /实际位置/bundle`，不能将原始bench_sources目录冒充prepared bundle。脚本不会下载、重跑分析、执行A规则或调用模型，也不重新扫描服务器原始大文件哈希。

固定输出为`~/AssemblyGenomics-Skill/bench/bench_transfer/v2_cases_reproduction/bundle`，含cases、RESULT.json、REPRODUCED_INPUTS.json、versions.json、reproduction.log、MANIFEST.json和MANIFEST.sha256。可重复执行，不删除来源或用户文件；新包解压会更新指定的构题文件，v1任务/产物/答案/上下文文件必须与原FROZEN一致。脚本先检查传输代码与回归材料清单，再构题。

将整个输出bundle用scp传回本地`bench/v2/incoming/reproduction/bundle`，不要只复制屏幕摘要。Windows上的解包演练已通过，不代表Linux验证完成；接收端验清单后才记录服务器复现通过。

比较规则：所有task、artifact、expected与v2_labels的文件哈希必须完全相同。新meta的来源包绝对路径随主机不同，跨平台仅把这一固定前缀规范化为SOURCE_BUNDLE再逐字节计算哈希；真实source_origin、原始/子集SHA、截取与所有其它字段保留并比较。v1回归meta直接复制原字节，另写v2_labels，不改原meta。输出完整运输清单仍记录每个文件的实际字节哈希。

本阶段结果为人工审核草案，没有FROZEN。服务器复现成功也不等于人工批准标准答案。
