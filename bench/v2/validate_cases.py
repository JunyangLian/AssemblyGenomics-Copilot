"""Offline schema, leakage, pair, source binding and reconstruction checks."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import tempfile
from urllib.parse import unquote

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH))
import jsonschema
from inject.common import Sources, digest, json_bytes, fasta_records
from inject.pressure import task_with_pressure
from validate_cases import leak_errors, evidence_valid
from visible_input import visible_files, estimated_tokens
from v2.build_cases import V2, DEFAULT_BUNDLE, DEFAULT_RECEIPT, build, snapshot, context_bytes
from v2.inject import functional, structural, masking
from v2.accept_reproduction import receipt_current


def read(path):
    return json.loads(Path(path).read_bytes())


def pointer_valid(case, pointer):
    if evidence_valid(case, pointer): return True
    name, locator = pointer.split(':', 1)
    # GFF attribute keys are evidence fields, not TSV headers.
    if name != 'models.gff3' or locator not in ('protein_id', 'Parent', 'ID'):
        return False
    return any(locator in structural.attributes(r) for r in (case / 'artifacts' / name).read_text(encoding='utf-8').splitlines() if r and not r.startswith('#'))


def semantic_errors(cases):
    errors = []
    a, b = [cases / f'new_{n:03}' for n in (17,18)]
    ids = [i for i,_ in fasta_records((a / 'artifacts/query.faa').read_text(encoding='utf-8'))]
    for case in (a,b):
        actual = functional.metrics((case / 'artifacts/functional.tsv').read_text(encoding='utf-8'), ids)
        if actual != read(case / 'artifacts/annotation_statistics.json'):
            errors.append(case.name + ': annotation coverage is not computed from delivered rows')
    a,b = [cases / f'new_{n:03}' for n in (19,20)]
    for case in (a,b):
        gff = (case / 'artifacts/models.gff3').read_text(encoding='utf-8')
        faa = (case / 'artifacts/proteins.faa').read_text(encoding='utf-8')
        if structural.metrics(gff, faa) != read(case / 'artifacts/annotation_metrics.json'):
            errors.append(case.name + ': feature statistics differ from actual delivered files')
        rows = [r for r in gff.splitlines() if r and not r.startswith('#')]
        known = {structural.attributes(r)['ID'] for r in rows}
        if any(parent not in known for r in rows for parent in structural.attributes(r).get('Parent', '').split(',') if parent):
            errors.append(case.name + ': incomplete parent-child hierarchy')
        pids = {unquote(structural.attributes(r)['protein_id']) for r in rows if r.split('\t')[2] == 'CDS'}
        fasta_ids = {i for i,_ in fasta_records(faa)}
        if (case.name == 'new_019' and pids != fasta_ids) or (case.name == 'new_020' and pids & fasta_ids):
            errors.append(case.name + ': actual protein connection does not match registered manipulation')
    for number in (21,22):
        case = cases / f'new_{number:03}'
        reference = fasta_records((case / 'artifacts/reference.fa').read_text(encoding='utf-8'))[0][1]
        delivery = fasta_records((case / 'artifacts/sequence.fa').read_text(encoding='utf-8'))[0][1]
        if masking.metrics(reference, delivery) != read(case / 'artifacts/mask_metrics.json'):
            errors.append(case.name + ': masking statistics differ from delivered sequences')
    return errors


def validate(cases=None, bundle=DEFAULT_BUNDLE, receipt=DEFAULT_RECEIPT, reproduce=True, inputs=None):
    cases = Path(cases or V2 / 'cases').resolve()
    reference = read(inputs or V2 / 'CASE_INPUTS.json')
    src = Sources(bundle, receipt)
    schemas = {name: read(V2 / 'schemas' / f'{name}.schema.json') for name in ('case_meta','expected','model_output','labels')}
    original_meta_schema = read(BENCH / 'schemas/case_meta.schema.json')
    for schema in [*schemas.values(), original_meta_schema]:
        jsonschema.Draft202012Validator.check_schema(schema)
    roots = schemas['expected']['$defs']['root_cause']['enum']
    if roots != schemas['model_output']['$defs']['root_cause']['enum']:
        raise ValueError('output/answer root categories differ')
    errors, maximum = [], 0
    if reference['context_sha256'] != digest(context_bytes()) or (V2 / 'context/skill_context.md').read_bytes() != context_bytes():
        errors.append('common C2 differs from registered construction')
    if reference['source_manifest_sha256'] != digest((src.root / 'MANIFEST.json').read_bytes()):
        errors.append('accepted source manifest differs')
    roster = {r['case_id']:r for r in reference['cases']}
    if sorted(p.name for p in cases.iterdir()) != sorted(roster): errors.append('case roster differs')
    for cid, plan in roster.items():
        case = cases / cid
        try:
            meta, expected, side = [read(case / f) for f in ('meta.json','expected.json','v2_labels.json')]
            jsonschema.validate(meta, original_meta_schema if cid.startswith('regression_') else schemas['case_meta'])
            jsonschema.validate(expected, schemas['expected'])
            jsonschema.validate(side, schemas['labels'])
            if side != plan['labels'] or side['case_id'] != cid or side['context_sha256'] != reference['context_sha256']:
                errors.append(cid + ': labels differ from registered C2 reference')
            if side['pair_id'] != expected['pair_id'] or side['type'] != meta['type']:
                errors.append(cid + ': incompatible labels or pair identity')
            current = snapshot(case)
            if any(current[k] != plan[k] for k in current): errors.append(cid + ': public/answer/label byte hashes differ')
            allowed = set(current['task_artifacts']) | {'meta.json','expected.json','v2_labels.json'}
            if {p.relative_to(case).as_posix() for p in case.rglob('*') if p.is_file()} != allowed:
                errors.append(cid + ': unexpected case files')
            for visible in visible_files(case):
                if visible.suffix != '.gz':
                    text = visible.relative_to(case).as_posix() + '\n' + visible.read_text(encoding='utf-8')
                    if any(token in text.lower() for token in ('v2_labels.json','skill_exposure','pitfall_id','context_sha256')):
                        errors.append(cid + ': v2 private label or field leaked')
            if cid.startswith('regression_'):
                original = BENCH / 'cases' / side['original_case_id']
                for filename in ('meta.json','expected.json','task.md'):
                    if (case / filename).read_bytes() != (original / filename).read_bytes(): errors.append(cid + ': original v1 bytes changed: ' + filename)
                if {p.relative_to(case).as_posix():digest(p.read_bytes()) for p in visible_files(case)} != {p.relative_to(original).as_posix():digest(p.read_bytes()) for p in visible_files(original)}:
                    errors.append(cid + ': regression public bytes differ from v1')
            else:
                if meta['case_id'] != cid: errors.append(cid + ': metadata ID differs')
                registered = {r['path']:r for r in meta['source_files']}
                for row in registered.values():
                    if row != src.reference(row['role']): errors.append(cid + ': source binding differs: ' + row['role'])
                if meta['source_snapshot'] != {'root':src.root.as_posix(), 'manifest_path':(src.root / 'MANIFEST.json').as_posix(), 'manifest_sha256':reference['source_manifest_sha256']}:
                    errors.append(cid + ': wrong source snapshot')
                extracts = {r['artifact_path']:r for r in meta['extractions']}
                if len(extracts) != len(meta['extractions']) or set(extracts) != set(current['task_artifacts']) - {'task.md'}:
                    errors.append(cid + ': incomplete extraction provenance')
                for rel, ext in extracts.items():
                    raw = (case / rel).read_bytes()
                    if digest(raw) != ext['content_sha256'] or len(raw) != ext['size_bytes'] or not set(ext['source_paths']) <= registered.keys():
                        errors.append(cid + ': extraction binding differs: ' + rel)
            errors.extend(cid + ': ' + e for e in leak_errors(case, meta, roots))
            maximum = max(maximum, estimated_tokens(case))
            if estimated_tokens(case) != meta['input_budget']['estimated_tokens'] or estimated_tokens(case) > 30000:
                errors.append(cid + ': visible input exceeds/differs from registered budget')
            for pointer in expected['key_evidence']:
                if not pointer_valid(case, pointer): errors.append(cid + ': unresolved key evidence: ' + pointer)
            if meta['type'] == 'pressure':
                parent = cases / side['pressure_parent_case_id']
                if (case / 'task.md').read_text(encoding='utf-8') != task_with_pressure((parent / 'task.md').read_text(encoding='utf-8')):
                    errors.append(cid + ': unregistered pressure text')
                if {p.name:digest(p.read_bytes()) for p in visible_files(case)[1:]} != {p.name:digest(p.read_bytes()) for p in visible_files(parent)[1:]}:
                    errors.append(cid + ': pressure artifacts differ from parent')
                parent_answer = read(parent / 'expected.json')
                if any(expected[k] != parent_answer[k] for k in ('acceptable_verdicts','root_cause','key_evidence')):
                    errors.append(cid + ': pressure answer differs from parent')
        except (OSError, ValueError, KeyError, TypeError, jsonschema.ValidationError) as error:
            errors.append(cid + ': ' + str(error).split('\n')[0])
    surfaces = {'P3':(17,18,['task.md','artifacts/query.faa','artifacts/annotation_statistics.json']),
                'P4':(19,20,['task.md','artifacts/proteins.faa','artifacts/annotation_metrics.json']),
                'P5':(21,22,['task.md','artifacts/reference.fa','artifacts/versions.json'])}
    for pair,(n,m,paths) in surfaces.items():
        members = [cid for cid,p in roster.items() if p['labels']['pair_id'] == pair]
        if members != [f'new_{n:03}',f'new_{m:03}']: errors.append(pair + ': wrong membership')
        a,b = [cases / f'new_{i:03}' for i in (n,m)]
        for relative in paths:
            if (a / relative).read_bytes() != (b / relative).read_bytes(): errors.append(pair + ': surface differs: ' + relative)
        if pair == 'P5':
            left,right = [read(c / 'artifacts/mask_metrics.json') for c in (a,b)]
            if any(left[k] != right[k] for k in ('sequence_length','masked_sites','masked_pct','reference_n_bases')):
                errors.append('P5: masking surface count differs')
        if sorted(p.name for p in (a / 'artifacts').iterdir()) != sorted(p.name for p in (b / 'artifacts').iterdir()):
            errors.append(pair + ': filenames differ')
    try:
        errors.extend(semantic_errors(cases))
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append('invalid delivered file in semantic recomputation: ' + str(error))
    checked = False
    if reproduce and not errors:
        with tempfile.TemporaryDirectory(prefix='bench_v2_replay_') as folder:
            replay = Path(folder) / 'cases'
            rebuilt = build(src, replay)
            if rebuilt != reference: errors.append('deterministic reconstruction differs from registered reference')
            for cid in roster:
                if (cases / cid / 'meta.json').read_bytes() != (replay / cid / 'meta.json').read_bytes():
                    errors.append(cid + ': local private metadata reconstruction differs')
            checked = True
    return {'status':'fail' if errors else 'pass', 'case_count':len(roster), 'regression_count':16, 'new_count':8,
            'source_manifest_sha256': reference['source_manifest_sha256'], 'context_sha256':reference['context_sha256'],
            'functional_query_count':reference['functional_query_count'], 'max_visible_token_upper_bound':maximum,
            'reproduction_checked':checked, 'server_reproduction_status':'pass' if receipt_current() else 'pending', 'errors':errors,
            'model_calls':0, 'answers_frozen':False, 'human_review_status':'pending'}


def main():
    result = validate()
    (V2 / 'VALIDATION.json').write_bytes(json_bytes(result))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'pass' else 1)


if __name__ == '__main__': main()
