# Inspect 开发试跑准备验证

2026-10-10，Windows Python 3.10.1。准备实现、候选答案和有界运行方案；未生成生产 APPROVAL/FROZEN，未读取本地 API key，真实供应商调用 0 次。原 v1/v2 冻结与结果、v3 四题原草案和公共产物均未改动。

## 本阶段文件

- `pilot.py`：生成候选；真实用户批准后的四个 expected.json 文件哈希冻结；付费入口批准检查、原生 Inspect task/provider/tools/scorer/log；一次性领取和累计 HTTP/输入代理/输出申请限制。
- `pilot/`：四个候选 expected.json、汇总、公共文件身份、schema、参数方案、估算和审核说明。候选只保存在独立试跑目录，没有把 AI 审核改成真人审核。
- `requirements-pilot.lock.txt`：Inspect 0.3.277 + OpenAI SDK 3.28.0 + httpx2 2.13.1 的独立锁文件；不覆盖历史回放的依赖锁。`pip check`：No broken requirements found。
- `tests/test_pilot.py`：19 个批准门槛、私密输入隔离、参数偏移、请求及 token 代理限制、失败计分、答案文件哈希和一次性领取测试。
- `tests/transport_smoke.py`：可复现的离线假 HTTP 集成校验；不会访问外网或环境凭证。
- `README.md`：链接当前候选方案和验证记录。

## 实际执行

`--prepare`：生成四个候选，没有批准/冻结/调用。批准测试只在 pytest 临时目录使用明确标为模拟的授权文本，不是生产授权。

`--mock`：真实 Inspect Task 和原生工具循环，4 个 Sample、4 次实际 `list_files`，4 个 mock 标记输出全部按无效 QC 回答计零，四题分母完整保留。没有模型准确率结论。

`tests.transport_smoke`：真实 OpenAI 兼容 provider 与 SDK、完全本地 httpx2.MockTransport；8 次假传输请求、4 次实际文件工具调用、0 外部网络请求、0 供应商调用。验证原生 tool-call 响应接续、max_tokens/temperature/模型 ID 请求形状、累计预算保留和错误分母。假 usage 只是夹具，不作为实际 token。四个首轮完整序列化请求为 6,045 / 5,649 / 6,117 / 6,117 字节；包含工具定义后的首轮代理合计 9,000，八个模拟请求代理累计 19,037。真实模型会选择不同工具和轮次，此数值不能预测完整真实用量。

离线 provider 构造检查确认 SDK 和 Inspect 重试均为 0；禁止网络的假客户端未发送请求。首次检查把配置属性误定位到 provider API，改为 Model.config 后通过；未以这个失败检查宣称通过。

专项：19 passed in 1.13s。最终完整回归：

```text
python -m pytest -q
389 passed in 296.68s (0:04:56)
```

候选文本 UTF-8/LF、凭证字面量扫描、无生产批准/冻结检查通过。运行日志与工作目录被忽略，不提交 SDK 请求头、凭证或用户的数据压缩包。Windows 已运行；此新适配未在 Linux 执行。

## 当前边界

这四题是已有开发题，只有一个工具条件和一次重复，不支持新来源泛化、Skill 增益或 H1–H3 结论。Scorer 只做 schema、定位有效性和三项判定匹配；证据语义和行动安全仍未裁决，不把定位有效当成证据正确。

平台当前可用性、原生 function calling、真实返回型号和价格尚未在线验证。须用户同时确认四题试跑答案冻结及一次性调用上限，先提交冻结身份，再执行付费入口；不自动继承历史预算，不在失败后偷偷重置调用上限。
