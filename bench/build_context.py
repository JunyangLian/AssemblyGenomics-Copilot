"""Build one shared, auditable Skill treatment without project observations."""
from pathlib import Path
import argparse
import re
import yaml
from inject.common import digest, json_bytes

BENCH = Path(__file__).resolve().parent
REPO = BENCH.parent

# Exact source excerpts, selected once for all cases; never selected by case ID.
PIT_FIELDS = {
    'PIT-001': {'root_cause': None},
    'PIT-002': {'root_cause': '官方默认 braker3.cfg 的 intron_support 1.0'},
    'PIT-003': {'root_cause': None},
    'PIT-004': {'root_cause': None},
    'PIT-005': {'root_cause': 'TSEBRA 合并/AGAT 最长转录本筛选后残留'},
    'PIT-006': {'root_cause': None},
    'PIT-007': {'root_cause': '线程预算是服务器策略问题'},
    'PIT-008': {'context_note': '硬化规则：BRAKER 前生成'},
    'PIT-009': {'root_cause': '`--filter_single_exon_genes`'},
}
END = {
    'PIT-002': '才能定位。', 'PIT-005': '这属于',
    'PIT-007': 'skill 若', 'PIT-008': '不一致即停止。',
    'PIT-009': '支持的单外显子基因”。',
}


def build():
    chunks, records = [], []

    def add(path, selector, text, policy):
        text = text.strip() + '\n'
        begin = 1 + sum(c.count('\n') for c in chunks)
        chunks.append(f'## {path.as_posix()} — {selector}\n\n{text}\n')
        records.append({'source': path.as_posix(), 'source_sha256': digest((REPO / path).read_bytes()),
                        'selector': selector, 'context_start_line': begin,
                        'retained_sha256': digest(text.encode()), 'retained_text': text,
                        'omission_policy': policy})

    skill = (REPO / 'SKILL.md').read_text(encoding='utf-8').replace('\r\n', '\n')
    add(Path('SKILL.md'), 'intro + hard constraints',
        skill.split('# AssemblyGenomics Skill\n', 1)[1].split('## 入口与用户旅程', 1)[0],
        'Drop front matter, SOP commands, project records, status and case examples after hard constraints.')
    policy = (REPO / 'references/qc-and-review-policy.md').read_text(encoding='utf-8')
    add(Path('references/qc-and-review-policy.md'), 'general policy',
        policy.split('当前项目仅完成第一类。')[0], 'Drop dated capability conclusion; keep general state/review policy.')
    for p in sorted((REPO / 'knowledge/pitfalls').glob('*.yaml')):
        d = yaml.safe_load(p.read_text(encoding='utf-8'))
        selected = {k: d[k] for k in ('id', 'title', 'phase', 'severity', 'commands')}
        for field in PIT_FIELDS[d['id']]:
            value = d[field]
            if d['id'] in END:
                end = END[d['id']]
                if d['id'] == 'PIT-009':
                    value = value.split('\n', 1)[0]  # exact first sentence; all species observations dropped
                else:
                    value = value.split(end, 1)[0] + (end if end.endswith('。') else '')
            selected[field] = value.strip()
        add(p.relative_to(REPO), 'generic fields and exact mechanism excerpt',
            yaml.safe_dump(selected, allow_unicode=True, sort_keys=False),
            'Drop symptom, case context, check implementation and all observed values/identities; retain title, commands and generic mechanism excerpt.')
    pitread = (REPO / 'knowledge/pitfalls/README.md').read_text(encoding='utf-8')
    row = next(l for l in pitread.splitlines() if l.startswith('| PIT-010 |'))
    fragments = ['"等效重跑"TSEBRA 合并 ≠ BRAKER3 内部合并',
                 '重跑 exit 0、数量级看似合理，只能靠 raw vs 重跑基因数对照揭露']
    if any(s not in row for s in fragments):
        raise ValueError('PIT-010 generic excerpt changed')
    add(Path('knowledge/pitfalls/README.md'), 'PIT-010 generic clauses', '\n'.join(fragments),
        'Drop all case names, numbers, dates and case repair conclusions in directory index.')
    base = (REPO / 'knowledge/baselines/README.md').read_text(encoding='utf-8')
    add(Path('knowledge/baselines/README.md'), 'purpose and dual-layer policy',
        base.split('## 条目格式', 1)[0], 'Drop examples, observations, citations to internal projects and commands.')
    for p in sorted((REPO / 'knowledge/baselines').glob('*.yaml')):
        ds = yaml.safe_load(p.read_text(encoding='utf-8'))
        selected = [{k: d[k] for k in ('id', 'metric', 'taxon_scope', 'unit', 'expected_range', 'source_type', 'enforce')} for d in ds]
        add(p.relative_to(REPO), 'all generic bands', yaml.safe_dump(selected, allow_unicode=True, sort_keys=False),
            'Drop all references, comments and notes containing population/project observations; preserve registered advisory bands for every taxon.')
    content = (''.join(chunks).rstrip() + '\n').encode('utf-8')
    # Same-source observations and identities must not survive this projection.
    forbidden = ['27,645', '12,637', '18,376', '19,156', '5,179', '5,384', '97.99', '6.333',
                 '97.9%', '76.7%', '98.1%', 'Siganus', 'NC_001133', 'arab_batch', 'celegans_batch',
                 'Nakaseomyces', '_archive_', '/home/', 'use-case-', '2026-']
    for token in forbidden:
        if token in content.decode():
            raise ValueError('context still contains a case observation/identity: ' + token)
    return content, json_bytes({'version': 'v1-draft', 'selection_policy': 'shared field whitelist + exact general excerpts; no case retrieval',
                               'package_sha256': digest(content), 'sources': records,
                               'excluded_categories': ['docs', 'STATE', 'run_registry', 'SOP settings', 'bench cases and sources']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, default=BENCH / 'context')
    args = parser.parse_args()
    if (BENCH / 'FROZEN.md').exists() and args.output.resolve() == (BENCH / 'context').resolve():
        raise SystemExit('Frozen context cannot be overwritten')
    args.output.mkdir(parents=True, exist_ok=True)
    content, record = build()
    (args.output / 'skill_context.md').write_bytes(content)
    (args.output / 'build_record.json').write_bytes(record)
    print('Shared context:', digest(content), 'bytes:', len(content))
