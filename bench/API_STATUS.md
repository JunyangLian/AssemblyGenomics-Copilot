# 阶段3真实调用状态（不计分）

更新时间：2026-10-07T12:10:20.451328+08:00。当前计划：`e33d885fa1815d510066b39a27a1909bd571cd3485728f480b0a3808c9199005`。

| 模型 | 组 | 当前版本 | 完成尝试 | 最终观测 | 有效JSON | 有usage | 已知input/output token | 按批准单价估费 |
|---|---|---|---:|---:|---:|---:|---|---:|
| deepseek-flash | B | False | 48 | 48 | 0 | 0 | None/None | unknown |
| qwen3.8-27b | B | False | 48 | 48 | 0 | 0 | None/None | unknown |
| kimi-k3 | B | False | 24 | 24 | 0 | 0 | None/None | unknown |
| deepseek-flash | B | True | 48 | 48 | 48 | 48 | 138060/11251 | ¥0.3661 |
| qwen3.8-27b | B | True | 49 | 48 | 48 | 49 | 145992/9269 | ¥0.5492 |
| kimi-k3 | B | True | 29 | 15 | 12 | 26 | 56154/45014 | ¥5.6245 |
| deepseek-flash | C | True | 48 | 48 | 48 | 48 | 349452/12365 | ¥0.7978 |
| qwen3.8-27b | C | True | 90 | 48 | 48 | 90 | 672042/20387 | ¥2.2608 |
| kimi-k3 | B | True | 63 | 33 | 32 | 62 | 192137/143399 | ¥18.1826 |
| kimi-k3 | C | True | 38 | 21 | 16 | 33 | 213929/60006 | ¥10.2792 |
| kimi-k3 | C | True | 1 | 1 | 0 | 0 | None/None | unknown |

当前版本有效观测 252/262；累计预留 488 次，预留额度 ¥202.25134500000016（不是扣费）。

Usage is provider-reported where available. Cost is approved uncached/peak rate estimate, excludes cache/off-peak/plan/free quota; not account deduction. Original TLS failures and inflight reservations retained separately. No accuracy/H1-H3 scoring.

所有旧网络失败记录保留于TRANSPORT_RUN1.json与原JSONL。实际账单unknown；A真实服务器结果仍待回传。
