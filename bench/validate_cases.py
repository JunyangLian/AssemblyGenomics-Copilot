"""Validate private schemas, visible leakage, paired controls and byte reproduction."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import tempfile
import zlib

import jsonschema
from build_cases import BENCH, DEFAULT_BUNDLE, DEFAULT_RECEIPT, build
from inject.common import Sources, digest, json_bytes, fasta_records
from inject.pressure import task_with_pressure
from visible_input import estimated_tokens, serialize, visible_files


def evidence_valid(case, pointer):
    name, locator = pointer.split(':', 1)
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or name in {'expected.json', 'meta.json'}:
        return False
    target = case / ('task.md' if name == 'task.md' else 'artifacts/' + name.removeprefix('artifacts/'))
    if target not in visible_files(case) or target.suffix == '.gz':
        return False
    data = target.read_text(encoding='utf-8')
    if locator == 'empty': return data == ''
    if locator.isdigit(): return 1 <= int(locator) <= len(data.splitlines())
    if target.suffix == '.json':
        try:
            value = json.loads(data)
            for key in locator.split('.'):
                value = value[int(key)] if isinstance(value, list) else value[key]
            return True
        except (KeyError, IndexError, ValueError, TypeError): return False
    return locator in data.splitlines()[0].split('\t') if data else False


def leak_errors(case, meta, roots):
    errors = []
    trace = re.compile(r'(?i)(?<![a-z0-9])(truncated|injected|injection|fault|faulty|bad|synthetic)(?![a-z0-9])')
    single = re.compile(r'(?i)(?<![a-z0-9_])(none|contamination)(?![a-z0-9_])')
    rows = {r['artifact_path']: r for r in meta['extractions']}
    for p in visible_files(case):
        relative = p.relative_to(case).as_posix()
        data = p.read_bytes()
        if p.suffix == '.gz':
            try: data = zlib.decompressobj(31).decompress(data)
            except zlib.error:
                errors.append(relative + ': invalid gzip body, cannot scan'); continue
        text = data.decode('utf-8')
        if b'\r' in data: errors.append(relative + ': non-LF bytes')
        scanned = relative + '\n' + text
        if trace.search(scanned): errors.append(relative + ': injection trace word')
        for token in roots:
            if '_' in token and token.lower() in scanned.lower(): errors.append(relative + ': root enum ' + token)
        if any(token in scanned.lower() for token in ['expected.json', 'meta.json', 'acceptable_verdicts', 'root_cause', 'source_origin', '_archive_', '/home/', 'd:/1_yanjiusheng']):
            errors.append(relative + ': private field/path or filename')
        matches = list(single.finditer(scanned))
        if matches:
            extraction = rows.get(relative, {})
            exceptions = [e for e in meta.get('lexical_exceptions', []) if e['artifact_path'] == relative]
            for match in matches:
                token = match[0].lower()
                valid = extraction.get('text_origin') == 'tool_verbatim' and any(
                    e['token'] == token and e['source_path'] in extraction['source_paths'] and
                    e['source_sha256'] == next((s['sha256'] for s in meta['source_files'] if s['path'] == e['source_path']), '') and
                    evidence_valid(case, p.name + ':' + e['locator']) for e in exceptions)
                if not valid: errors.append(relative + ': single-word enum without exact tool exception: ' + token)
    return errors


def validate(cases, bundle=DEFAULT_BUNDLE, receipt=DEFAULT_RECEIPT, context=None, inputs=None, reproduce=True):
    cases = cases.resolve(); context = context or BENCH/'context/skill_context.md'; inputs = inputs or BENCH/'CASE_INPUTS.json'
    src = Sources(bundle, receipt)
    schemas = {name: json.loads((BENCH/'schemas'/f'{name}.schema.json').read_text(encoding='utf-8'))
               for name in ['case_meta','expected','model_output']}
    for schema in schemas.values(): jsonschema.Draft202012Validator.check_schema(schema)
    roots = schemas['expected']['$defs']['root_cause']['enum']
    if set(roots) != set(schemas['model_output']['$defs']['root_cause']['enum']):
        raise ValueError('root enum schemas differ')
    reference = json.loads(inputs.read_text(encoding='utf-8'))
    errors, metas, maximum = [], {}, 0
    if reference['source_manifest_sha256'] != digest((src.root/'MANIFEST.json').read_bytes()):
        errors.append('input reference has a different source manifest')
    if reference['context_sha256'] != digest(context.read_bytes()): errors.append('shared context changed')
    roster = {r['case_id']: r for r in reference['cases']}
    if sorted(p.name for p in cases.iterdir() if p.is_dir()) != sorted(roster): errors.append('case roster differs')
    for case_id, plan in roster.items():
        case = cases/case_id
        try:
            meta = json.loads((case/'meta.json').read_text(encoding='utf-8'))
            expected = json.loads((case/'expected.json').read_text(encoding='utf-8'))
            for name,value in [('case_meta',meta),('expected',expected)]:
                jsonschema.Draft202012Validator(schemas[name], format_checker=jsonschema.FormatChecker()).validate(value)
            metas[case_id] = meta
            for key in ['stage','type','seen_or_heldout','skill_exposure','pitfall_id','pair_id']:
                if meta[key] != plan[key]: errors.append(case_id + ': label differs from draft input reference: ' + key)
            if meta['case_id'] != case_id: errors.append(case_id + ': wrong case ID')
            if digest((case/'expected.json').read_bytes()) != plan['expected_sha256']: errors.append(case_id + ': answer changed without regenerating reviewed draft reference')
            if meta['pair_id'] != expected.get('pair_id'): errors.append(case_id + ': pair metadata differs from answer')
            if meta['type'] in ('normal','hard_negative') and expected['root_cause'] != 'none': errors.append(case_id + ': normal root must be none')
            registered = {r['path']: r for r in meta['source_files']}
            for r in registered.values():
                if r != src.reference(r['role']): errors.append(case_id + ': source binding differs: ' + r['role'])
            if meta['source_snapshot'] != {'root':src.root.as_posix(), 'manifest_path':(src.root/'MANIFEST.json').as_posix(),
                                         'manifest_sha256':reference['source_manifest_sha256']}:
                errors.append(case_id + ': source snapshot differs')
            actual = {p.relative_to(case).as_posix(): digest(p.read_bytes()) for p in visible_files(case)}
            if actual != plan['task_artifacts']: errors.append(case_id + ': visible byte hashes differ')
            extraction_map = {r['artifact_path']: r for r in meta['extractions']}
            if len(extraction_map) != len(meta['extractions']) or set(extraction_map) != set(actual)-{'task.md'}:
                errors.append(case_id + ': incomplete or duplicate extraction coverage')
            for relative,r in extraction_map.items():
                if any(path not in registered for path in r['source_paths']): errors.append(case_id + ': unregistered extraction source')
                data = (case/relative).read_bytes()
                if r['content_sha256'] != digest(data) or r['size_bytes'] != len(data): errors.append(case_id + ': artifact receipt differs: ' + relative)
                if r['text_origin'] == 'tool_verbatim':
                    if not any(data.decode() in src.text(registered[p]['role']) for p in r['source_paths']):
                        errors.append(case_id + ': tool_verbatim bytes not present in source')
            errors.extend(case_id + ': ' + e for e in leak_errors(case,meta,roots))
            for pointer in expected['key_evidence']:
                if not evidence_valid(case,pointer): errors.append(case_id + ': unresolved evidence ' + pointer)
            budget = estimated_tokens(case); maximum=max(maximum,budget)
            if budget != meta['input_budget']['estimated_tokens'] or budget > 30000: errors.append(case_id + ': input budget mismatch/exceeded')
            if meta['type'] == 'hard_negative':
                run = meta['own_run']; role = next(r['role'] for r in registered.values() if r['path'] == run['run_record_path'])
                record = src.json(role)
                if run['run_record_sha256'] != src.reference(role)['sha256'] or run['input_sha256'] != [v for k,v in record['inputs'].items() if k.endswith('_sha256')]:
                    errors.append(case_id + ': own run provenance differs')
            if meta['type'] == 'pressure':
                parent = cases/meta['pressure_parent_case_id']
                if (case/'task.md').read_text(encoding='utf-8') != task_with_pressure((parent/'task.md').read_text(encoding='utf-8')):
                    errors.append(case_id + ': pressure prose differs')
                parent_hashes = {p.name:digest(p.read_bytes()) for p in visible_files(parent)[1:]}
                if {p.name:digest(p.read_bytes()) for p in visible_files(case)[1:]} != parent_hashes: errors.append(case_id + ': pressure artifacts differ')
        except (OSError, ValueError, KeyError, TypeError, jsonschema.ValidationError) as error:
            errors.append(case_id + ': ' + str(error).split('\n')[0])
    pair = [k for k,m in metas.items() if m['pair_id'] == 'P2']
    if pair != ['case_009','case_010']: errors.append('P2 membership differs')
    if len(pair) == 2:
        a,b = [cases/p for p in pair]
        for relative in ['task.md','artifacts/query.faa','artifacts/annotation_statistics.json']:
            if (a/relative).read_bytes() != (b/relative).read_bytes(): errors.append('P2 surface differs: ' + relative)
        if sorted(p.name for p in (a/'artifacts').iterdir()) != sorted(p.name for p in (b/'artifacts').iterdir()): errors.append('P2 filenames differ')
    # Rebuild with the same accepted subset bytes: do not re-hash original server data.
    if reproduce and not errors:
        with tempfile.TemporaryDirectory(prefix='bench_replay_') as folder:
            replay = Path(folder)/'cases'
            rebuilt,_ = build(src,replay,context)
            if rebuilt != reference: errors.append('deterministic reproduction differs from draft reference')
            for case_id in roster:
                for private in ['expected.json','meta.json']:
                    if (cases/case_id/private).read_bytes() != (replay/case_id/private).read_bytes(): errors.append(case_id + ': private reproduction differs: ' + private)
    return {'status': 'pass' if not errors else 'fail', 'case_count': len(roster),
            'reproduction_checked': reproduce and not errors, 'max_visible_token_upper_bound': maximum,
            'source_manifest_sha256': reference['source_manifest_sha256'], 'context_sha256': reference['context_sha256'],
            'errors': errors, 'model_calls': 0, 'answers_frozen': False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cases',type=Path,default=BENCH/'cases'); parser.add_argument('--bundle',type=Path,default=DEFAULT_BUNDLE)
    parser.add_argument('--receipt',type=Path,default=DEFAULT_RECEIPT); parser.add_argument('--report',type=Path,default=BENCH/'VALIDATION.json')
    args=parser.parse_args()
    result=validate(args.cases,args.bundle,args.receipt)
    args.report.write_bytes(json_bytes(result))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['status']=='pass' else 1)


if __name__=='__main__': main()
