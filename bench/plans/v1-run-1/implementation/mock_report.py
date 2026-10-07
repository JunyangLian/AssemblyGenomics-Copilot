"""Call accounting and prospective costs. No answer comparisons or H1-H3 scoring."""
from __future__ import annotations

from harness_common import BENCH, request, token_estimate, read_json, write_json
from run_plan import verify


def report(root=BENCH):
    locked = verify(root)
    index = read_json(root / 'MOCK_RUNS.json')
    if index['plan_sha256'] != locked['plan_sha256']:
        raise ValueError('mock runs use a different plan')
    summaries = [read_json(root / name / 'summary.json') for name in index['runs']]
    planned = []
    for model in locked['plan']['models']:
        groups = {}
        for group in ['B','C']:
            values = [token_estimate(request(root/'cases'/row['case_id'], group, model, root)) for row in locked['plan']['cases']]
            retry_values = [token_estimate(request(root/'cases'/row['case_id'], group, model, root, retry=True)) for row in locked['plan']['cases']]
            groups[group] = {'initial_calls':len(values)*3, 'mean_input_proxy':sum(v['proxy'] for v in values)/len(values),
                'mean_input_upper':sum(v['upper'] for v in values)/len(values),
                'input_proxy_total':sum(v['proxy'] for v in values)*3, 'input_upper_total':sum(v['upper'] for v in values)*3,
                'input_with_all_retries_upper':sum(v['upper'] for v in values+retry_values)*3}
        calls = sum(g['initial_calls'] for g in groups.values())
        inp = sum(g['input_proxy_total'] for g in groups.values())
        upper = sum(g['input_upper_total'] for g in groups.values())
        retry_upper = sum(g['input_with_all_retries_upper'] for g in groups.values())
        output = calls * 1000
        maximum = calls * model['output_token_budget']
        planned.append({'model':model['name'], 'groups':groups, 'initial_calls':calls, 'maximum_calls':calls*2,
            'input_proxy_total':inp, 'input_upper_total':upper, 'scenario_output_tokens':output,
            'maximum_output_tokens_initial':maximum, 'maximum_output_tokens_with_retries':maximum*2,
            'input_cny_per_million':model['input_cny_per_million'], 'output_cny_per_million':model['output_cny_per_million'],
            'scenario_cost_cny':(inp*model['input_cny_per_million']+output*model['output_cny_per_million'])/1e6,
            'initial_upper_cost_cny':(upper*model['input_cny_per_million']+maximum*model['output_cny_per_million'])/1e6,
            'all_retries_upper_cost_cny':(retry_upper*model['input_cny_per_million']+maximum*2*model['output_cny_per_million'])/1e6})
    data = {'date':'2026-10-07', 'plan_sha256':locked['plan_sha256'],
            'actual_mock_model_calls':sum(s['calls'] for s in summaries), 'actual_api_calls':0, 'actual_paid_cost_cny':0,
            'mock_A_transport_slots':sum(s['observations'] for s in summaries if s['group']=='A'),
            'real_A_server_status':'received' if (root/'A_RECEIPT.json').exists() else 'pending',
            'parse_errors':sum(s['parse_errors'] for s in summaries), 'runs':summaries, 'planned_api':planned,
            'scenario_total_cny':sum(p['scenario_cost_cny'] for p in planned),
            'initial_upper_total_cny':sum(p['initial_upper_cost_cny'] for p in planned),
            'all_retries_upper_total_cny':sum(p['all_retries_upper_cost_cny'] for p in planned),
            'estimate_note':'No provider tokenizer/usage: UTF-8 /3 is a proxy, bytes + framing is conservative planning allowance. Output scenario 1000 tokens/call is an assumption, NOT measured reasoning length. Max output includes thinking for Kimi; uncached peak/base prices, no quota/discount.'}
    write_json(root/'MOCK_REPORT.json',data)
    lines = ['# 阶段3 mock 与费用报告', '', '日期：2026-10-07。标准答案原样冻结，未进行计分；真实 API 调用 0，实际模型费用 ¥0。', '',
        f'运行计划 SHA-256：`{locked["plan_sha256"]}`。', '',
        f'B/C：实际 {data["actual_mock_model_calls"]} 次 mock 调用，{data["parse_errors"]} 个最终解析失败。A：48个模拟运输槽位，不产生生物判定；服务器真实 A 待回传。', '',
        '| 模型 | B 平均输入代理 token | C 平均输入代理 token | 初始/最多调用 | 1000输出假设费用 | 初始保守额度 | 全重试保守额度 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for p in planned:
        lines.append(f'| {p["model"]} | {p["groups"]["B"]["mean_input_proxy"]:.1f} | {p["groups"]["C"]["mean_input_proxy"]:.1f} | {p["initial_calls"]}/{p["maximum_calls"]} | ¥{p["scenario_cost_cny"]:.2f} | ¥{p["initial_upper_cost_cny"]:.2f} | ¥{p["all_retries_upper_cost_cny"]:.2f} |')
    lines += ['', f'三模型总计：288次初始，最多576次（每次解析失败只修复一次）；假设费用 ¥{data["scenario_total_cny"]:.2f}，初始保守额度 ¥{data["initial_upper_total_cny"]:.2f}，全重试保守额度 ¥{data["all_retries_upper_total_cny"]:.2f}。', '',
        '平均输入包括 schema/提示/产物，C 每次增加同一知识包。代理 token 不等于供应商计费 token；mock usage=null，不能报告为真实 usage。JSON 文件附输入代理/字节保守估计与输出额度总量。1000输出是假设，Kimi思考可能显著超过；额度按8192完整输出（Kimi允许10 token误差）估算。', '',
        '参数：均请求 temperature=0；DeepSeek/Qwen关闭思考，Kimi启用思考；不静默回退参数。服务端是否接受/实际生效、账号权限及别名具体版本尚未真实验证；失败会记录，不擅自替换模型。', '',
        '价格核对日期2026-10-06，人民币/百万token：DeepSeek 2/8（高峰未缓存），Qwen 3/12（北京），Kimi 20/100（北京，含思考）；忽略缓存、赠送额度和促销。', '',
        '[DeepSeek价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)；[Qwen价格](https://help.aliyun.com/en/model-studio/qwen3-8-27b)；[Kimi价格](https://help.aliyun.com/zh/model-studio/model-pricing)；[阿里云参数及完整输出上限](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)。', '',
        '真实调用仍需用户批准模型/计划/调用上限与费用预算，另存API_APPROVAL.json；当前没有此批准文件。费用守卫在发送前按保守值预留额度，达到上限即停，不自动重试网络错误；这是计划额度，最终账单以供应商为准。', '',
        '原始JSONL保存在本地 bench/runs/（被既有Git忽略）；模拟记录不得用于H1-H3。A服务器结果需验证48个唯一槽位、原规则身份和公开输入哈希后才准计分。']
    (root/'MOCK_REPORT.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
    return data


if __name__=='__main__':
    result=report()
    print(f'mock={result["actual_mock_model_calls"]}, API=0, paid=0; scenario CNY {result["scenario_total_cny"]:.2f}; all-retries allowance CNY {result["all_retries_upper_total_cny"]:.2f}')
