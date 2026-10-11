"""Select new model-development sources from recorded T3 locations, without raw IO."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = Path(__file__).resolve().parent
T1_SPECIES = {'Arabidopsis_thaliana', 'Caenorhabditis_elegans', 'Saccharomyces_cerevisiae'}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def exposed_accessions(paths):
    used = set()
    for path in paths:
        meta = json.loads(path.read_bytes())
        # Never infer exposure from aggregate reports listing every T3 species.
        source_fields = [meta.get('source_group', ''), meta.get('source_files', [])]
        used.update(re.findall(r'GCF_\d+\.\d+', json.dumps(source_fields)))
    return used


def select(rows, used, count=6):
    eligible = {}
    for row in rows:
        if (row['accession'] in used or row['species'] in T1_SPECIES or
                row['recorded_complete_pair'].lower() != 'true'):
            continue
        if not row['server_gff_paths'] or not row['server_faa_paths']:
            continue
        eligible.setdefault(row['clade'], []).append(row)
    # Fixed metadata-only selection. Do not use baseline verdict or model results.
    chosen = [min(group, key=lambda r: (int(r['recorded_pair_bytes']), r['accession']))
              for _, group in sorted(eligible.items())]
    if len(chosen) < count:
        raise ValueError(f'only {len(chosen)} eligible clades; need {count}; no automatic substitution')
    return chosen[:count]


def prepare(root=ROOT, directory=DIRECTORY):
    tracked = subprocess.check_output(
        ['git', 'ls-files', '--', ':(glob)bench/**/meta.json'], cwd=root).decode().splitlines()
    metadata = [root / name for name in tracked]
    used = exposed_accessions(metadata)
    inventory = root / 'bench/v3/T3_CANDIDATES.csv'
    with inventory.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    chosen = select(rows, used)
    locations_path = root / 'bench/v1_prepare_t1t3_r3/bundle/t3_locations.json'
    locations = json.loads(locations_path.read_bytes())
    indexed = {(r['accession'], r['kind'], r['path']): r for r in locations['candidate_files']}
    files = []
    for row in chosen:
        for kind, column in (('gff', 'server_gff_paths'), ('faa', 'server_faa_paths')):
            paths = row[column].split(';')
            if len(paths) != 1:
                raise ValueError('ambiguous recorded path: ' + row['accession'] + '/' + kind)
            origin = paths[0]
            record = indexed[(row['accession'], kind, origin)]
            files.append({'source_group': row['accession'], 'species': row['species'],
                          'clade': row['clade'], 'kind': kind, 'filename': Path(origin).name,
                          'recorded_origin': origin, 'recorded_size_bytes': record['size_bytes']})
    source_roots = {str(Path(item['recorded_origin']).parent).replace('\\', '/') for item in files}
    if len(source_roots) != 1:
        raise ValueError('selected source paths require multiple roots; resolve explicitly')
    directory.mkdir(parents=True, exist_ok=True)
    server = directory / 'server'; server.mkdir(exist_ok=True)
    receipt = {
        'version': 'newsource-validation-preparation-1', 'status': 'awaiting_server_sources',
        'api_call_authorized': False, 'answers_frozen': False, 'api_calls': 0,
        'selection_policy': 'six clades; smallest recorded complete pair per clade; metadata only; no verdict filter',
        'excluded_case_accessions': sorted(used), 'excluded_T1_species': sorted(T1_SPECIES),
        'selected': chosen, 'source_groups': 6, 'target_cases': 12, 'proposed_observations': 72,
        'selected_recorded_bytes': sum(int(row['recorded_pair_bytes']) for row in chosen),
        'source_hash_rescans': 0, 'baseline_report_previously_seen': True,
        'claim': 'new to project model/prompt/tool development; not unexposed to historical T3 rule checks',
        'pretraining_exposure': 'unknown', 'paths_are_currently_verified_on_server': False,
        'metadata_identity': {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [inventory, locations_path, *metadata]},
    }
    (directory / 'SOURCE_AUDIT.json').write_bytes(encoded(receipt))
    config = {'spec_version': 'v3-source-prepare-1', 'source_scope': 'T3',
              'source_root': next(iter(source_roots)),
              'output_root': 'bench_transfer/newsource_validation_sources_r1',
              'historical_report_notice': receipt['claim'],
              'approved_selection': '2026-10-11 user agreed to 5-6 new sources and 10-12 QC cases; no API approval',
              'files': files}
    (server / 'prepare_config.json').write_bytes(encoded(config))
    original = root / 'bench/v3/server/prepare_sources.py'
    (server / 'prepare_sources.py').write_bytes(original.read_bytes())
    print(f'PREPARED: {len(chosen)} groups; {len(files)} source files; '
          f'{receipt["selected_recorded_bytes"]:,} recorded bytes; 0 raw rescans; 0 API calls')
    for row in chosen:
        print(row['accession'], row['species'], row['clade'])
    return receipt


if __name__ == '__main__':
    prepare()
