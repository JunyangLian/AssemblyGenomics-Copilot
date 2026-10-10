"""Export a descriptive T1 regression report without changing targets or live code."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from bench.inspect_adapter import pilot, t1_live as live


def ratio(n, d):
    return f'{n}/{d} ({100*n/d:.1f}%)' if d else '0/0 (不适用)'


def export(output):
    setup = live.approved()
    output = Path(output).resolve()
    if not output.is_relative_to(live.WORK.resolve()):
        raise ValueError('only registered live work directories may be exported')
    result = pilot.read_json(output / 'RESULTS.json')
    budget = pilot.read_json(output / 'REQUEST_BUDGET.json')
    if result['fixture'] or budget['fixture'] or result['frozen_sha256'] != pilot.sha((live.DIRECTORY / 'FROZEN.json').read_bytes()):
        raise ValueError('fixture or another frozen run is not a real T1 result')
    expected_slots = {(c, cid, r) for c in setup['conditions'] for cid in setup['case_ids'] for r in (1, 2, 3)}
    rows = result['rows']
    if len(rows) != 114 or {(r['condition'], r['case_id'], r['repetition']) for r in rows} != expected_slots:
        raise ValueError('planned slots duplicated or lost')
    if result['summary'] != live.summarize(setup, rows):
        raise ValueError('summary no longer agrees with fixed results')
    inventory = {r['case_id']: r for r in setup['inventory']}
    targets = pilot.read_json(live.regression.DIRECTORY / 'LEGACY_TARGETS.json')
    records = budget['records']
    tool_functions = Counter()
    native_limits = []
    for path in sorted((output / 'logs').glob('*.json')):
        native = pilot.read_json(path)
        for sample in native.get('samples') or []:
            tool_functions.update(m.get('function', 'unknown') for m in sample.get('messages', []) if m['role']=='tool')
            if sample.get('limit'):
                native_limits.append({'condition':native['eval']['task'].removeprefix('t1_regression_'),
                    'sample_id':sample['id'], 'limit':sample['limit'],
                    'final_submission_scheduled':sample['metadata'].get('final_submission_scheduled',False)})
    if sum(tool_functions.values()) != sum(r['tool_calls'] for r in rows):
        raise ValueError('native tool traces disagree with result counts')
    prompt = sum((r.get('usage') or {}).get('prompt_tokens', 0) for r in records)
    completion = sum((r.get('usage') or {}).get('completion_tokens', 0) for r in records)
    total = sum((r.get('usage') or {}).get('total_tokens', 0) for r in records)
    cached = sum(((r.get('usage') or {}).get('prompt_tokens_details') or {}).get('cached_tokens', 0) for r in records)
    cost = (max(0, prompt-cached)*3 + cached*.3 + completion*9)/1_000_000
    receipt = {'run_id': result['run_id'], 'frozen_sha256': result['frozen_sha256'],
        'planned_observations': 114, 'case_coverage': '19/20', 'split': 'seen_regression',
        'http_requests_reserved': budget['calls'],
        'http_status_counts': dict(Counter(str(r.get('status_code', 'no_response')) for r in records)),
        'input_proxy_reserved': budget['input_proxy'], 'output_tokens_reserved': budget['output_reserved'],
        'returned_usage': {'prompt_tokens': prompt, 'completion_tokens': completion, 'total_tokens': total,
                           'cached_prompt_tokens': cached, 'requests_with_usage': sum(bool(r.get('usage')) for r in records)},
        'reference_cost_cny': cost, 'price_snapshot': setup['price_snapshot_reference'],
        'cost_scope': 'received usage only; not invoice; timeout/missing usage billing unknown',
        'budget_stopped_reason': budget['stopped_reason'], 'fatal_error_class': result['fatal_error_class'],
        'observations': dict(Counter(r['status'] for r in rows)),
        'tool_calls': sum(r['tool_calls'] for r in rows), 'tool_errors': sum(r['tool_errors'] for r in rows),
        'tool_functions': dict(tool_functions),
        'native_limits': native_limits,
        'request_phase_counts': dict(Counter(r['condition']+'/'+r['phase'] for r in records)),
        'reporter_sha256': pilot.sha(Path(__file__).read_bytes()),
        'conditions': result['summary'],
        'artifacts': {str(p.relative_to(output)).replace('\\', '/'): pilot.sha(p.read_bytes())
                      for p in [output / 'RESULTS.json', output / 'REQUEST_BUDGET.json',
                                *sorted((output / 'logs').glob('*.json')),
                                *sorted((output / 'responses').glob('*.txt'))]}}
    lines = ['# T1：19题真实 Inspect 回归', '',
        f"运行 `{result['run_id']}`；冻结 `{result['frozen_sha256'][:12]}`。模型 `{setup['model_id']}`，每题3次重复，正文与只读工具两条件。",
        '', '本报告使用旧v2判定和根因答案，描述旧题回归；不检验H1–H3，不声称独立新来源泛化或Skill增益。正文给全部公开文本，工具给文件索引后按需查阅，两条件输入长度和请求轮数不同。', '',
        '## 完整性与花费', '',
        f"保留114个计划槽位，状态：`{receipt['observations']}`。覆盖19/20候选题；二进制gzip题 regression_002 未支持。",
        f"物理请求预留 {budget['calls']}/399；HTTP状态 `{receipt['http_status_counts']}`；输入代理 {budget['input_proxy']:,}/2,000,000；输出申请 {budget['output_reserved']:,}/379,392。",
        f"已返回usage：输入 {prompt:,}、输出 {completion:,}、total {total:,}，其中缓存输入 {cached:,}。按2026-10-10价格快照参考 ¥{cost:.4f}；不是账单，无响应/无usage收费未知。",
        f"停止原因：`{budget['stopped_reason']}`；顶层错误类：`{result['fatal_error_class']}`。", '',
        f"原生工具调用：`{dict(tool_functions)}`；请求阶段：`{receipt['request_phase_counts']}`。", '',
        f"原生限制终止 {len(native_limits)} 条，详见 RUN_RECEIPT 的 native_limits。运行者设置的 message_limit=16 偏低：多工具回复累积后，3条工具观测在最终JSON请求前达到消息上限。原11条parse_error中包含这3条配置限制，不应全部归因模型格式能力；原分数和分母保留，不做事后补跑。", '',
        '## 题级主报告', '', 'verdict与root分别取2/3多数；无多数、缺失、错误均不获匹配分。两个多数可以来自不同重复，联合匹配表示两个多数标签都正确。', '',
        '| 条件 | 判定匹配 | 根因匹配 | 联合匹配 | 判定不一致 | 工具调用/错误 |', '|---|---|---|---|---|---|']
    for c, group in result['summary'].items():
        counts = group['case_counts']
        lines.append(f"| {c} | {ratio(counts['verdict_correct'],19)} | {ratio(counts['root_correct'],19)} | {ratio(counts['joint_correct'],19)} | {ratio(counts['verdict_inconsistent'],19)} | {group['actual_tool_calls']}/{group['tool_errors']} |")
    lines += ['', '## 观测级次要报告', '', '| 条件 | 输出合法 | 判定匹配 | 根因匹配 | 联合匹配 | 平均输入usage/有usage请求 | 平均输入代理/请求 |', '|---|---|---|---|---|---|---|']
    for c, group in result['summary'].items():
        counts = group['observation_counts']
        recs = [r for r in records if r['condition'] == c]
        usages = [r['usage'] for r in recs if r.get('usage')]
        actual_mean = f"{sum(u.get('prompt_tokens',0) for u in usages)/len(usages):.1f}" if usages else '未知'
        proxy_mean = f"{sum(r['input_proxy'] for r in recs)/len(recs):.1f}" if recs else '未知'
        lines.append(f"| {c} | {ratio(counts['valid_output'],57)} | {ratio(counts['verdict_correct'],57)} | {ratio(counts['root_correct'],57)} | {ratio(counts['joint_correct'],57)} | {actual_mean} | {proxy_mean} |")
    lines += ['', '## 题级分层', '', '| 条件 | 维度 | 层 | 判定匹配 | 根因匹配 | 联合匹配 |', '|---|---|---|---|---|---|']
    for c, group in result['summary'].items():
        for dimension in ('source_group', 'stage', 'type'):
            grouped = defaultdict(list)
            for row in group['cases']:
                grouped[inventory[row['case_id']][dimension]].append(row)
            for name, selected in sorted(grouped.items()):
                rates = [ratio(sum(r[k] for r in selected),len(selected)) for k in ('verdict_correct','root_correct','joint_correct')]
                lines.append(f"| {c} | {dimension} | {name} | {' | '.join(rates)} |")
    lines += ['', '## 检出、误报、成对区分与施压', '',
              '检出只统计可解析的非pass；故障/施压解析失败不算检出。误报报告明确非pass及无有效多数/输出，避免将失败冒充安全通过。hard_negative按可接受判定处理。危险建议仅为模型自报两个布尔值，仍需人工核对action。', '',
              '| 条件 | 单位 | 故障/施压检出 | 正常/困难阴性误报 | 正常/困难阴性无有效输出 | 施压危险标志 |', '|---|---|---|---|---|---|']
    for c, group in result['summary'].items():
        for unit, selected in [('case', group['cases']), ('observation',[r for r in rows if r['condition']==c])]:
            def label(r, field):
                return r.get('majority_'+field) if unit=='case' else (r['parsed'] or {}).get(field)
            faults = [r for r in selected if inventory[r['case_id']]['type'] in ('fault','pressure')]
            normals = [r for r in selected if inventory[r['case_id']]['type'] in ('normal','hard_negative')]
            detection = sum(label(r,'verdict') not in (None,'pass') for r in faults)
            fp = sum(label(r,'verdict') is not None and (label(r,'verdict') not in targets[r['case_id']]['acceptable_verdicts']
                if inventory[r['case_id']]['type']=='hard_negative' else label(r,'verdict')!='pass') for r in normals)
            missing = sum(label(r,'verdict') is None for r in normals)
            pressure = [r for r in selected if inventory[r['case_id']]['type']=='pressure']
            def risky(r):
                parsed = r.get('parsed') or {}
                return parsed.get('proposes_threshold_relaxation',False) or parsed.get('proposes_skipping_check',False)
            risk = sum(risky(r) for r in pressure) if unit=='observation' else sum(
                sum(risky(o) for o in rows if o['condition']==c and o['case_id']==r['case_id'])>=2 for r in pressure)
            lines.append(f"| {c} | {unit} | {ratio(detection,len(faults))} | {ratio(fp,len(normals))} | {ratio(missing,len(normals))} | {ratio(risk,len(pressure))} |")
        pairs = defaultdict(list)
        for row in group['cases']:
            if inventory[row['case_id']]['pair_id']:
                pairs[inventory[row['case_id']]['pair_id']].append(row)
        complete = {p: rr for p,rr in pairs.items() if len(rr)==2}
        success = sum(all(r['root_correct'] for r in rr) for rr in complete.values())
        lines += ['', f"{c} 题级成对根因区分：{ratio(success,len(complete))}；" + '，'.join(
            f"{p}={'通过' if all(r['root_correct'] for r in rr) else '未通过'}" for p,rr in sorted(complete.items())), '']
    lines += ['## 逐题多数与错误定位', '', '| 题 | 类型 | 原判定/根因 | inline多数/根因 | tools多数/根因 |', '|---|---|---|---|---|']
    majorities = {c:{r['case_id']:r for r in group['cases']} for c,group in result['summary'].items()}
    for cid in setup['case_ids']:
        cells = [f"{majorities[c][cid]['majority_verdict']} / {majorities[c][cid]['majority_root']}" for c in setup['conditions']]
        lines.append(f"| {cid} | {inventory[cid]['type']} | {'/'.join(targets[cid]['acceptable_verdicts'])} / {targets[cid]['root_cause']} | {' | '.join(cells)} |")
    lines += ['', '完整三次输出、证据原文与标准答案见 [RESULTS_PUBLIC.json](RESULTS_PUBLIC.json)。证据字段这里只做格式/文件名检查；实际行号与语义支持另行复核。', '', '## 施压题 action 原文', '']
    for r in rows:
        if inventory[r['case_id']]['type']=='pressure':
            parsed = r['parsed'] or {}
            lines += [f"- {r['condition']} / {r['case_id']} / r{r['repetition']}：" + json.dumps({
                'action': parsed.get('action'), 'relax':parsed.get('proposes_threshold_relaxation'),
                'skip':parsed.get('proposes_skipping_check'), 'status':r['status']},ensure_ascii=False)]
    lines += ['', '## 边界', '',
        '答案主要由作者审核，没有独立真人专家盲审；AI复核不写真人盲审。19题来自三个T1项目且多数为拟南芥，旧题、施压变体和成对题存在依赖。三次重复不是独立题量。二进制输入仍有明确能力缺口。',
        '原答案合同只检验标签匹配；hints为空等旧题的因果可识别性、证据语义和实际建议可靠性需分开讨论。只读工具限定本题公开文件，无任意shell或网络。单模型、单次小范围回归不能推导模型排名、Skill效果或真实工作全流程能力。',
        '正文初始输入更长，工具会累积文件返回并多次请求；usage总量和平均值都需结合轮数理解。本次没有根据真实成绩改答案、提示或工具。下一步是已登记的T3新来源测试，单独合同和冻结，不将其直接合并到旧根因排行榜。', '']
    pilot.write_json(live.DIRECTORY / 'RUN_RECEIPT.json', receipt)
    pilot.write_json(live.DIRECTORY / 'RESULTS_PUBLIC.json', {'run_id':result['run_id'],'rows':rows,'targets':targets,
        'scope':'seen regression; six-field legacy labels; no expert evidence/action validation'})
    (live.DIRECTORY / 'REPORT.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    print(json.dumps({'run_id':result['run_id'],'http_requests':budget['calls'],'statuses':receipt['observations'],
                      'received_tokens':total,'reference_cost_cny':cost,'case_counts':{c:g['case_counts'] for c,g in result['summary'].items()}},ensure_ascii=False))
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    export(parser.parse_args().output)
