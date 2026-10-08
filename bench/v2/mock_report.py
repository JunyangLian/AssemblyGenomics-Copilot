"""Verify mock transport and estimate resources; never score mock QC answers."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
from collections import Counter
from bench.v2.runtime import V2, canonical, digest, read_json, write_json, request, token_estimate, parse_response, summary
from bench.v2.plan import verify


def report(root=V2):
    locked = verify(root); plan = locked['plan']
    index = read_json(root / 'MOCK_RUNS.json')
    if index['plan_sha256'] != locked['plan_sha256'] or index['mode'] != 'mock':
        raise ValueError('mock index differs from plan')
    observations, attempts, runs = [], [], []
    for name in index['runs']:
        directory = (root / name).resolve(strict=True)
        if (root / 'runs').resolve() not in directory.parents:
            raise ValueError('mock run outside runs directory')
        s = read_json(directory / 'summary.json')
        if s['mode'] != 'mock' or digest((directory / 'records.jsonl').read_bytes()) != s['records_sha256']:
            raise ValueError('mock records/summary mismatch')
        rows = [json.loads(line) for line in (directory / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
        for row in rows:
            if row['mode'] != 'mock' or row['plan_sha256'] != locked['plan_sha256'] or row['frozen_md_sha256'] != locked['frozen_md_sha256']:
                raise ValueError('unexpected mock row identity')
            (attempts if row['record_type'] == 'attempt' else observations).append(row)
        runs.append({**s, 'path': name})
    wanted = {(c['case_id'], rep, group, model['name']) for c in plan['cases'] for rep in range(1, 4)
              for group in plan['groups'] for model in plan['models']}
    model_obs = [r for r in observations if r['group'] != 'A']
    slots = [(r['case_id'], r['repetition'], r['group'], r['model']) for r in model_obs]
    if len(slots) != len(wanted) or set(slots) != wanted or any(r['status'] != 'ok' for r in model_obs):
        raise ValueError('mock planned slots incomplete or parsed output invalid')
    models = {m['name']: m for m in plan['models']}
    attempt_slots = set()
    for r in attempts:
        slot = (r['case_id'], r['repetition'], r['group'], r['model'], r['attempt'])
        if slot in attempt_slots or slot[:4] not in wanted or r['attempt'] not in (0, 1):
            raise ValueError('unexpected/duplicate mock attempt')
        attempt_slots.add(slot)
        case = root / 'cases' / r['case_id']
        body = request(case, r['group'], models[r['model']], root, r['attempt'] > 0)
        if r['request_summary'] != summary(case, body, root):
            raise ValueError('logged request is not the planned public packet')
        parsed, error = parse_response(r['response'], case, root)
        if error or parsed != r['parsed']:
            raise ValueError('mock response cannot be parsed again')
    a = [r for r in observations if r['group'] == 'A']
    a_slots = [(r['case_id'], r['repetition']) for r in a]
    if (len(a_slots) != 72 or set(a_slots) != {(c['case_id'], i) for c in plan['cases'] for i in range(1, 4)}
        or any(r.get('simulated') is not True or r.get('parsed') is not None or r['status'] != 'execution_error' for r in a)):
        raise ValueError('mock A must be 72 clearly simulated transport slots')
    groups = {}
    for group in plan['groups']:
        initial = [token_estimate(request(root / 'cases' / c['case_id'], group, plan['models'][0], root)) for c in plan['cases']]
        repair = [token_estimate(request(root / 'cases' / c['case_id'], group, plan['models'][0], root, True)) for c in plan['cases']]
        groups[group] = {'average_initial_input_proxy': sum(t['proxy'] for t in initial) / 24,
            'average_initial_input_byte_bound': sum(t['upper'] for t in initial) / 24,
            'max_initial_input_proxy': max(t['proxy'] for t in initial),
            'max_initial_input_byte_bound': max(t['upper'] for t in initial),
            'initial_input_proxy_per_model': 3 * sum(t['proxy'] for t in initial),
            'initial_input_byte_bound_per_model': 3 * sum(t['upper'] for t in initial),
            'all_repair_input_proxy_per_model': 3 * sum(t['proxy'] for t in initial + repair),
            'all_repair_input_byte_bound_per_model': 3 * sum(t['upper'] for t in initial + repair)}
    model_n = len(plan['models']); initial_calls = len(wanted); repair_calls = initial_calls * 2
    initial_proxy = model_n * sum(g['initial_input_proxy_per_model'] for g in groups.values())
    initial_bound = model_n * sum(g['initial_input_byte_bound_per_model'] for g in groups.values())
    repair_proxy = model_n * sum(g['all_repair_input_proxy_per_model'] for g in groups.values())
    repair_bound = model_n * sum(g['all_repair_input_byte_bound_per_model'] for g in groups.values())
    result = {'status': 'pass', 'plan_sha256': locked['plan_sha256'], 'frozen_md_sha256': locked['frozen_md_sha256'],
        'mock_index_sha256': digest((root / 'MOCK_RUNS.json').read_bytes()), 'runs': runs,
        'actual_mock_calls': len(attempts), 'actual_api_calls': 0, 'mock_model_observations': len(model_obs),
        'a_simulated_observations': len(a), 'a_reused_real_observations': plan['a_reuse']['observations'],
        'a_new_real_observations_pending': 24, 'parse_errors': 0,
        'actual_mock_input_proxy': sum(r['request_summary']['input_estimate']['proxy'] for r in attempts),
        'actual_mock_input_byte_bound': sum(r['request_summary']['input_estimate']['upper'] for r in attempts),
        'provider_usage': None, 'provider_price': None, 'provider_thinking': 'default unknown', 'groups': groups,
        'prospective': {'initial_calls': initial_calls, 'all_format_repair_calls': repair_calls,
            'initial_input_proxy': initial_proxy, 'initial_input_byte_bound': initial_bound,
            'all_repair_input_proxy': repair_proxy, 'all_repair_input_byte_bound': repair_bound,
            'output_scenario_tokens_per_call': 1000, 'output_scenario_initial_tokens': initial_calls * 1000,
            'output_requested_limit_per_call': 8192, 'initial_output_requested_limit': initial_calls * 8192,
            'all_repair_output_requested_limit': repair_calls * 8192},
        'hypotheses_scored': False, 'numeric_live_budget_approved': False,
        'execution': plan.get('execution'), 'credential_recovery': plan.get('credential_recovery'),
        'token_method': 'ceil(UTF8 message bytes / 3) + 64 + 16/message; planning byte bound = bytes + same overhead',
        'limitations': 'Not a provider tokenizer or billed bound; hidden reasoning, cache pricing and resource weights unknown.'}
    write_json(root / 'MOCK_REPORT.json', result)
    lines = ['# v2 阶段3 mock与资源估算', '',
        f'运行计划：`{plan["version"]}`，SHA-256 `{locked["plan_sha256"]}`。24题、{model_n}模型、B/C2、每题3次；不读取答案构造请求。', '',
        f'本次实际调用mock **{len(attempts)}次**，{len(model_obs)}个模型观测全部可解析，最终parse_error 0。实际API调用 **0次**，本次外部调用费用0。A 72条为明确标记的运输模拟，无规则判定；48条真实旧A可按身份复用，新增24条待服务器执行。', '',
        f'mock随机答案不用于H1–H3或QC能力计分。原始响应、解析结果、请求摘要、usage=null与耗时在MOCK_RUNS.json列出的{len(runs)}个目录；无伪造供应商用量。', '',
        '| 模型 | 初始/全修复调用数 | B平均输入代理 | C2平均输入代理 | 费用/墨点 |',
        '|---|---:|---:|---:|---|']
    for m in plan['models']:
        lines.append(f'| {m["name"]} | 144 / 288 | {groups["B"]["average_initial_input_proxy"]:,.1f} | {groups["C2"]["average_initial_input_proxy"]:,.1f} | 未知 |')
    lines += ['', '| 情景 | 调用数 | 输入代理token | 输入字节规划上界 | 输出token |', '|---|---:|---:|---:|---:|',
        f'| 初始请求，输出假设每次1000 | {initial_calls:,} | {initial_proxy:,} | {initial_bound:,} | {initial_calls * 1000:,}（假设） |',
        f'| 初始请求，完整输出限额 | {initial_calls:,} | {initial_proxy:,} | {initial_bound:,} | {initial_calls * 8192:,} |',
        f'| 所有题一次格式修复，完整输出限额 | {repair_calls:,} | {repair_proxy:,} | {repair_bound:,} | {repair_calls * 8192:,} |', '',
        f'C2相对B平均每次增加{groups["C2"]["average_initial_input_proxy"] - groups["B"]["average_initial_input_proxy"]:,.1f}代理token，约{groups["C2"]["average_initial_input_proxy"] / groups["B"]["average_initial_input_proxy"]:.2f}倍；报告必须保留这个混杂因素。B/C2最大单次输入字节规划上界分别{groups["B"]["max_initial_input_byte_bound"]:,} / {groups["C2"]["max_initial_input_byte_bound"]:,}。30k约束针对单题材料，知识包使总请求进一步变长。', '',
        '代理按UTF-8消息字节数除3向上取整，加64+16×消息数；字节规划上界为消息字节数加同一开销。没有供应商tokenizer，二者不是实测usage，字节开销也不保证覆盖平台隐藏包装或思考token。1000输出只是费用敏感性情景，不是mock输出长度或真实输出预测。', '',
        '用户回复“没有，先看 token 估算”：账户费用/墨点换算未确认，不沿用原厂价格，也不把未知当0。平台模型元数据价格不能替代最终账单。未来费用公式为各模型输入×输入单价+输出×输出单价（按百万token换算）；缓存、思考计量、权重均待实际资料。', '',
        '提出共用temperature=0、max_tokens=8192、stream=false，不发送供应商thinking扩展；实际生效及默认思考模式未知，B/C2同模型参数一致。请求ID按用户原文，平台可用性未认证；返回不同ID暂停该模型，不静默换别名。格式重试1次，网络重试0次，300秒超时。', '',
        '真实运行采用API_APPROVAL.json中明确批准的累计上限及未知价格/默认思考条件，必须绑定本次mock。完整题库全修复情景1728次；登记的凭据恢复队列仅补跑另列HTTP429槽位，范围/预算见RUN_PLAN.credential_recovery指定文件，不重复承接结果。若登记了active_model_names，API仅派发这些模型；mock仍验证全部六模型配置且不调用API。实际按剩余额度执行，到达上限保留未完成分母。累计账本不返还旧预留、不重置费用。供应商usage超过预留则暂停。']
    (root / 'MOCK_REPORT.md').write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
    template = {'approved': False, 'user_approval_quote': None, 'plan_sha256': locked['plan_sha256'],
        'frozen_md_sha256': locked['frozen_md_sha256'], 'mock_report_sha256': digest((root / 'MOCK_REPORT.json').read_bytes()),
        'models': [m['name'] for m in plan['models']], 'groups': plan['groups'],
        'max_calls': None, 'max_input_tokens': None, 'max_output_tokens': None,
        'parameters_reviewed': None, 'accepts_unknown_price': None, 'accepts_unknown_provider_defaults': None}
    write_json(root / 'API_APPROVAL.template.json', template)
    print(f'PASS: {len(attempts)} mock calls; 0 API; input proxy {initial_proxy:,}; byte bound {initial_bound:,}')
    return result


if __name__ == '__main__':
    report()
