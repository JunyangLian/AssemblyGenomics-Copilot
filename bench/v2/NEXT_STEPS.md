**2026-10-09收尾完成：用户40条人工编码已验收，A与四模型已计分，pending为空；下面操作步骤仅保留作历史记录，无需再执行或填写。** 最新报告：`reports/v2-run-10_four-models_human-reviewed/`，人工未知及无效输出继续保留。后续新实验需另立版本，当前不派发API或退出模型。

# 四模型收尾：下一步

**2026-10-08更新：新增A24条已回传并验收，A共72/72条，下面服务器步骤仅留作记录，无需再执行。当前只剩“再填人工action盲审”。** 最新报告在`reports/v2-run-10_four-models_A-admitted/`；原盲审表也可以继续使用。

用户已决定后续不再使用Kimi/GLM。Vision、Pro、MiniMax、Qwen FP8的576条最终观测已结束，无需追加模型调用。既有退出模型日志保留，未执行218条取消；范围变化是查看结果后的决定，已另登记。

## 先补新增题的A组

本地包：`D:\1_yanjiusheng\GenomeAssembly Copilot\bench\v2\rules_package.zip`。只把这个文件上传到服务器`~/AssemblyGenomics-Skill/bench/v2/rules_package.zip`。这是当前v2-run-10的8题公开产物和原规则包，98,753字节；不包含答案、meta、API key，不下载新数据或重跑组装/注释。

在服务器运行：

```shell
cd ~/AssemblyGenomics-Skill/bench
python -m zipfile -e v2/rules_package.zip v2/rules_package
python v2/rules_package/server/run_rules.py
python -m zipfile -c bench_transfer/v2_rules_run_1.zip bench_transfer/v2_rules_run_1/bundle
```

这只执行新增8题×3次=24条A规则判定；旧48条不用重跑。包的manifest检查只核对这个小运行包，不重新扫描原始大源文件。

把整个输出bundle或最后生成的zip用scp传回本地`bench/v2/incoming/`，告诉本对话目录/zip路径。由agent验收并计分；不要只粘贴COMPLETE摘要，评分还需原始规则日志、版本和清单。四模型退出登记不修改服务器运行身份，因此当前这个包仍有效。

## 再填人工action盲审

也可使用新增本机审核页面：运行`python bench/v2/review_ui.py`，打开打印的地址，逐条选择分类、填写理由，再点击“导出 CSV”。草稿自动保存，原表不变；详见REVIEW_UI_README。完成后在聊天回复“盲审已保存”，agent可从本地导出目录接续验收。

只打开`reports/v2-run-10_four-models_closeout/ACTION_REVIEW_README.md`与`ACTION_REVIEW.csv`。40条有效回答按说明填写coding/reason，保留task/action、review_id和行数。8条无效输出已留作未知，不需要编造action。原阶段性报告的CSV也可继续填写：同一40条、同一顺序、同一review_id，不必重做。

暂时不要看PRIVATE映射或完整报告里的逐模型action附录；那会破坏盲审。编码完成后告诉本对话CSV的本地路径，agent会生成新报告，并独立保留模型自报flags。未编码前H2不可判定。

两项回传后用四模型主表完成本轮收尾。新增实例H1/H3当前未达改善门槛，不修改答案或降低门槛；下一版的Skill改进另立版本。本轮不再为Kimi/GLM排队，也不为错误输出追加API重跑。
