"""Stage-3 protocol/usage accounting only. Does not read or score answers."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone, timedelta
import json

from harness_common import BENCH, read_json, write_json


def summarize(root=BENCH):
    plan=read_json(root/'RUN_PLAN.json'); sha=(root/'RUN_PLAN.sha256').read_text(encoding='ascii').strip()
    models={m['name']:m for m in plan['models']}
    admitted={sha}
    if plan.get('resume_sources'): admitted.add(plan['parent_plan_sha256'])
    runs=[]; cumulative_attempts=0; cumulative_observations=0
    for path in sorted((root/'runs').glob('*/records.jsonl')):
        rows=[]
        for line in path.read_text(encoding='utf-8').splitlines():
            try: row=json.loads(line)
            except json.JSONDecodeError: continue  # Only live, incomplete trailing JSONL may be partial.
            if row.get('mode')=='api': rows.append(row)
        if not rows: continue
        attempts=[r for r in rows if r['record_type']=='attempt']
        observations=[r for r in rows if r['record_type']=='observation']
        cumulative_attempts+=len(attempts); cumulative_observations+=len(observations)
        with_usage=[r for r in attempts if isinstance(r.get('usage'),dict)]
        input_tokens=sum(r['usage'].get('prompt_tokens',0) for r in with_usage)
        output_tokens=sum(r['usage'].get('completion_tokens',0) for r in with_usage)
        model=models[rows[0]['model']]
        rates_estimate=(input_tokens*model['input_cny_per_million']+output_tokens*model['output_cny_per_million'])/1e6
        runs.append({'path':path.parent.relative_to(root).as_posix(),'group':rows[0]['group'],'model':model['name'],
            'plan_sha256':rows[0]['plan_sha256'],'current_plan':rows[0]['plan_sha256'] in admitted,
            'attempts':len(attempts),'observations':len(observations),
            'attempt_status':dict(Counter(r['status'] for r in attempts)),
            'observation_status':dict(Counter(r['status'] for r in observations)),
            'errors':dict(Counter(r['error'] for r in attempts if r.get('error'))),
            'usage_available_calls':len(with_usage),'usage_missing_calls':len(attempts)-len(with_usage),
            'provider_input_tokens_known':input_tokens if with_usage else None,
            'provider_output_tokens_known':output_tokens if with_usage else None,
            'known_usage_uncached_peak_cost_estimate_cny':rates_estimate if with_usage else None,
            'provider_returned_models':sorted({r['response'].get('model') for r in attempts if isinstance(r.get('response'),dict) and r['response'].get('model')}),
            'average_initial_input_tokens_known':sum(r['usage']['prompt_tokens'] for r in with_usage if r['attempt']==0 and 'prompt_tokens' in r['usage']) / max(1,sum(r['attempt']==0 and 'prompt_tokens' in r['usage'] for r in with_usage)),
            'completed_summary_exists':(path.parent/'summary.json').exists()})
    ledger_path=root/'runs'/('api_ledger_'+sha[:16]+'.json')
    ledger=read_json(ledger_path) if ledger_path.exists() else None
    current=[r for r in runs if r['current_plan']]
    value={'date':datetime.now(timezone(timedelta(hours=8))).isoformat(),'plan_sha256':sha,
        'runs':runs,'current_client_attempts':sum(r['attempts'] for r in current),
        'current_observations':sum(r['observations'] for r in current),
        'current_valid_observations':sum(r['observation_status'].get('ok',0) for r in current),
        'cumulative_completed_client_attempts':cumulative_attempts,'cumulative_completed_observations':cumulative_observations,
        'cumulative_reserved_calls':ledger['calls'] if ledger else plan.get('prior_ledger',{}).get('calls'),
        'cumulative_reserved_cny_not_billed':ledger['reserved_cny'] if ledger else plan.get('prior_ledger',{}).get('reserved_cny'),
        'known_provider_input_tokens_current':sum(r['provider_input_tokens_known'] or 0 for r in current),
        'known_provider_output_tokens_current':sum(r['provider_output_tokens_known'] or 0 for r in current),
        'known_usage_uncached_peak_cost_estimate_current_cny':sum(r['known_usage_uncached_peak_cost_estimate_cny'] or 0 for r in current),
        'actual_account_deduction_cny':None,'complete':all(sum(r['observations'] for r in current if r['model']==m and r['group']==g)==48 for m in models for g in ('B','C')),
        'note':'Usage is provider-reported where available. Cost is approved uncached/peak rate estimate, excludes cache/off-peak/plan/free quota; not account deduction. Original TLS failures and inflight reservations retained separately. No accuracy/H1-H3 scoring.'}
    write_json(root/'API_STATUS.json',value)
    lines=['# 阶段3真实调用状态（不计分）','',f'更新时间：{value["date"]}。当前计划：`{sha}`。','',
        '| 模型 | 组 | 当前版本 | 完成尝试 | 最终观测 | 有效JSON | 有usage | 已知input/output token | 按批准单价估费 |',
        '|---|---|---|---:|---:|---:|---:|---|---:|']
    for r in runs:
        cost=r['known_usage_uncached_peak_cost_estimate_cny']
        lines.append(f'| {r["model"]} | {r["group"]} | {r["current_plan"]} | {r["attempts"]} | {r["observations"]} | {r["observation_status"].get("ok",0)} | {r["usage_available_calls"]} | {r["provider_input_tokens_known"]}/{r["provider_output_tokens_known"]} | '+(f'¥{cost:.4f}' if cost is not None else 'unknown')+' |')
    lines+=['',f'当前版本有效观测 {value["current_valid_observations"]}/{value["current_observations"]}；累计预留 {value["cumulative_reserved_calls"]} 次，预留额度 ¥{value["cumulative_reserved_cny_not_billed"]}（不是扣费）。',
        '',value['note'],'','所有旧网络失败记录保留于TRANSPORT_RUN1.json与原JSONL。实际账单unknown；A真实服务器结果仍待回传。']
    (root/'API_STATUS.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
    print(f'current observations={value["current_observations"]}, valid={value["current_valid_observations"]}; cumulative reserved={value["cumulative_reserved_calls"]}; complete={value["complete"]}')
    return value


if __name__=='__main__': summarize()
