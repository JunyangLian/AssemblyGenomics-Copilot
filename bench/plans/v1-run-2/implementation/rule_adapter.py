"""Bindings to existing rules. No benchmark-specific biological checks."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

RULE_MAP = {
    'PIT-004': {'verdict': 'block', 'root_cause': 'protein_internal_ambiguity'},
    'PIT-005': {'verdict': 'rollback', 'root_cause': 'noncoding_residue'},
    'PIT-006': {'verdict': 'rollback', 'root_cause': 'masking_mode_error'},
}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def bindings(case):
    """Only public task and artifact types/fields, never case IDs or metadata."""
    task = (case / 'task.md').read_text(encoding='utf-8')
    artifacts = case / 'artifacts'
    candidates = sorted(p for p in artifacts.iterdir() if p.is_file())
    pit = []
    for path in candidates:
        if path.suffix in ('.faa',):
            pit.append(('PIT-004', {'PIT_PROT_FA': str(path.resolve())}, path.name, '未检出内部 . / *'))
        if path.suffix == '.gff3':
            pit.append(('PIT-005', {'PIT_GFF3': str(path.resolve())}, path.name, 'gene_total='))
        if path.suffix in ('.fa', '.fasta') and '软屏蔽' in task and '重复注释' in task:
            pit.append(('PIT-006', {'PIT_SM_FA': str(path.resolve())}, path.name, 'total='))
    taxon = None
    for text, group in [('拟南芥', 'viridiplantae'), ('线虫', 'nematoda'), ('酵母', 'fungi')]:
        if text in task:
            taxon = group
            break
    metrics, evidence = {}, []
    # Current delivery only; do not compare historical reference or invent thresholds.
    for path in candidates:
        if path.name not in {'delivery_metrics.json', 'annotation_metrics.json', 'mask_metrics.json'}:
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        for key, metric in [('gene_count', 'protein_coding_gene_count'), ('coding_genes', 'protein_coding_gene_count'),
                            ('lowercase_pct', 'repeat_masked_pct'), ('median_protein_length_aa', 'median_protein_length')]:
            if key in data and isinstance(data[key], (int, float)) and not isinstance(data[key], bool):
                metrics[metric] = data[key]
                evidence.append('artifacts/' + path.name + ':' + key)
        if isinstance(data.get('busco'), dict) and 'complete_pct' in data['busco']:
            metrics['annotation_busco_complete_pct'] = data['busco']['complete_pct']
            evidence.append('artifacts/' + path.name + ':busco.complete_pct')
    return pit, taxon, metrics, evidence


def evaluate_case(case, repo, mock=False):
    pit_bindings, taxon, metrics, evidence = bindings(case)
    if mock:
        # Transport test only: no invented successes, failures or shell output.
        return {'status': 'execution_error', 'parsed': None, 'checks': [],
                'error': 'mock A transport; real server rules pending', 'simulated': True}
    pitfalls = module(repo / 'scripts/run_pitfall_checks.py', 'bench_existing_pitfalls')
    baselines = module(repo / 'scripts/check_baselines.py', 'bench_existing_baselines')
    entries = {e['id']:e for e in pitfalls._load_entries(repo / 'knowledge/pitfalls')}
    checks, problems, results = [], [], []
    for pid, env, filename, marker in pit_bindings:
        if not shutil.which('bash') or not shutil.which('awk'):
            problems.append('bash/awk unavailable')
            continue
        entry = entries[pid]
        errors = pitfalls._validate(entry)
        if errors:
            problems.append('existing pitfall registry invalid')
            continue
        output, gap, engine = pitfalls._run_check(entry, env)
        checks.append({'id': pid, 'output': output, 'gap': gap, 'engine': engine,
                       'input_file': 'artifacts/' + filename})
        # Success markers validate execution only; diagnosis comes exclusively from existing gap.
        if engine != 'bash' or (marker not in output and gap is None):
            problems.append('rule execution did not return its known completion marker: ' + pid)
            continue
        verdict = RULE_MAP[pid]['verdict'] if gap else 'pass'
        root = RULE_MAP[pid]['root_cause'] if gap else 'none'
        results.append((verdict, root, 'artifacts/' + filename + ':1'))
    if taxon and metrics:
        registry = baselines.load_registry(repo / 'knowledge/baselines')
        if baselines.validate_registry(registry):
            problems.append('existing baseline registry invalid')
        else:
            output = baselines.evaluate(metrics, registry, taxon)
            checks.append({'id': 'check_baselines', 'output': output})
            covered = [r for r in output if r['status'] != 'unknown_metric']
            if covered:
                # Existing ranges are advisory; they cannot establish a specific cause.
                results.append(('warn' if any(r['status']=='out_of_range' for r in covered) else 'pass',
                                'none', evidence[0]))
    if problems:
        return {'status': 'execution_error', 'parsed': None, 'checks': checks, 'error': '; '.join(problems)}
    if not results:
        return {'status': 'not_covered', 'parsed': None, 'checks': checks, 'error': None}
    ranks = {'pass':0, 'warn':1, 'rollback':2, 'block':3}
    verdict, root, pointer = max(results, key=lambda r:ranks[r[0]])
    return {'status': 'ok', 'checks': checks, 'error': None, 'parsed': {
        'verdict': verdict, 'root_cause': root, 'evidence': [pointer],
        'action': '按已有规则输出复核交付；存在缺口时完成修复和检查后再继续。' if verdict != 'pass' else '已有可执行检查未报告缺口；仅覆盖日志列出的检查范围。',
        'proposes_threshold_relaxation': False, 'proposes_skipping_check': False}}
