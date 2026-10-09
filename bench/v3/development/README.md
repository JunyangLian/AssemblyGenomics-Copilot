# 四道 T1 开发草题

这里用于完善 v3 通用模板和指导，不是封存测试集。四题均有真实来源绑定，答案/暴露/审核状态尚未冻结。

用户作者审核查看 REVIEW_SHEET.csv 与 cases 中的完整题包。独立审核者只接收上一级 development_blind_review.zip；不要同时发送私有审核表、BLIND_REVIEW_MAP、GAPS、源码、expected 或 meta。审核人的空作答表与说明也保存在 blind_review。

从仓库根运行：

```powershell
python bench/v3/inject/build_development.py
python bench/v3/validate_development.py --reproduce --report bench/v3/development/VALIDATION.json
```

生成器读取 bench/v1_prepare_t1t3_r3/bundle/sources 的四个已验收小来源；可用 --sources-root 指定同名已验收副本。固定 seed、完整蛋白和 LF/二进制写入；源 SHA 引用 SOURCE_RECORDS，不重扫服务器原源。构造器禁止覆盖已批准答案或 v3 冻结版本，校验器当前只支持这四道开发草题，不是正式题库冻结工具。

对草题的任何调整须同步确定性生成规则及版本说明，再重生成/校验；意见先写用户审核表，不直接改生成结果来规避复现差异。没有新增 API 调用；Linux 复现与独立审题仍待完成。
