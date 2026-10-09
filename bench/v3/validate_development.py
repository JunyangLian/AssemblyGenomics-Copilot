"""Validate draft T1 development packets; reference calculations do not extend A rules."""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

V3 = Path(__file__).resolve().parent
sys.path.insert(0, str(V3/'inject'))
import build_development as builder


def pointers(files, value):
    name, location = value.split(':', 1)
    if name not in files or not (name == 'task.md' or name.startswith('artifacts/')):
        raise ValueError('evidence points outside visible packet: ' + value)
    text = files[name].decode('utf-8')
    if location.isdigit():
        if not 1 <= int(location) <= len(text.splitlines()):
            raise ValueError('evidence line does not exist: ' + value)
    elif name.endswith('.json'):
        if location not in json.loads(text):
            raise ValueError('evidence field does not exist: ' + value)
    elif name.endswith('.faa') or name.endswith('.fa'):
        if location not in {header.split()[0] for header, _ in builder.fasta_records(text)}:
            raise ValueError('evidence FASTA record does not exist: ' + value)
    elif name.endswith('.tsv'):
        if location not in text.splitlines()[0].split('\t'):
            raise ValueError('evidence TSV field does not exist: ' + value)
    else:
        raise ValueError('unsupported evidence locator: ' + value)


def validate_packets(packets):
    validators = {name: Draft202012Validator(json.loads((V3/'schemas'/ (name + '.schema.json')).read_text(encoding='utf-8')))
                  for name in ('expected', 'case_meta')}
    schema = json.loads((V3/'schemas/model_output.schema.json').read_text(encoding='utf-8'))
    labels = set(schema['properties']['root_cause']['enum'] + schema['properties']['observed_defect']['enum'])
    strict = [label for label in labels if '_' in label]
    words = [label for label in labels if '_' not in label] + ['fault', 'bad', 'injected', 'injection', 'truncated']
    source_records = json.loads((V3/'development/SOURCE_RECORDS.json').read_text(encoding='utf-8'))['sources']
    bindings = {(record['path'], record['source_origin'], record['sha256']) for record in source_records.values()}
    details = {}
    if set(packets) != {'dev_001','dev_002','dev_003','dev_004'}:
        raise ValueError('expected exactly four authorized development cases')
    for case, files in packets.items():
        expected = json.loads(files['expected.json'])
        meta = json.loads(files['meta.json'])
        validators['expected'].validate(expected)
        validators['case_meta'].validate(meta)
        if expected['case_id'] != case or meta['case_id'] != case:
            raise ValueError('case identity mismatch')
        if meta['split'] != 'development' or meta['source_group'] != 'T1_arabidopsis':
            raise ValueError('development source separation violated')
        for source in meta['source_files']:
            if source['source_group'] != meta['source_group'] or (source['path'],source['source_origin'],source['sha256']) not in bindings:
                raise ValueError('source receipt binding mismatch')
        if not any(fact['required_for_joint'] for fact in expected['key_evidence']):
            raise ValueError('no required key evidence')
        for fact in expected['key_evidence']:
            for pointer in fact['acceptable_pointers']:
                pointers(files, pointer)
        roles = meta['visible_contract']['artifact_roles']
        if any(name not in files for name in roles['delivery'] + roles['reference']):
            raise ValueError('declared artifact role unavailable')
        visible = {name: data for name, data in files.items() if name == 'task.md' or name.startswith('artifacts/')}
        for name, data in visible.items():
            text = name + '\n' + data.decode('utf-8')
            if b'\r' in data:
                raise ValueError('non-LF visible file')
            if any(label.casefold() in text.casefold() for label in strict):
                raise ValueError('enum leak in visible material: ' + name)
            if any(re.search(r'(?<![A-Za-z0-9_])' + re.escape(word) + r'(?![A-Za-z0-9_])', text, re.I) for word in words):
                raise ValueError('word leak in visible material: ' + name)
            if re.search(r'(?:expected|meta)\.json', text, re.I):
                raise ValueError('private filename in visible material')
        count = sum(len(data) for data in visible.values())
        if count > 30000:
            raise ValueError('development visible byte ceiling exceeded; no provider token count claimed')
        details[case] = {'visible_utf8_bytes': count, 'visible_files': sorted(visible), 'answer_status': 'draft'}

    files = packets['dev_001']
    rows = list(csv.DictReader(io.StringIO(files['artifacts/annotation.tsv'].decode()), delimiter='\t'))
    proteins = builder.fasta_records(files['artifacts/query.faa'].decode())
    query_ids = [row['query'] for row in rows]
    protein_ids = [header.split()[0] for header, _ in proteins]
    flags = [name for name in rows[0] if name.endswith('-Annotated')]
    annotated = sum(any(row[flag] == '1' for flag in flags) for row in rows)
    metrics = json.loads(files['artifacts/annotation_metrics.json'])
    actual = {'query_records': len(protein_ids), 'annotation_rows': len(rows), 'matched_ids': len(set(query_ids)&set(protein_ids)),
              'annotated_records': annotated, 'coverage_percent': 100*annotated/len(protein_ids)}
    if metrics != actual or len(set(query_ids)) != 32 or set(query_ids) != set(protein_ids):
        raise ValueError('functional statistics/ID relation inconsistent')
    files = packets['dev_002']
    if files['artifacts/hints.gff'] != b'' or json.loads(files['artifacts/input_metrics.json']) != {'hints_bytes':0,'feature_rows':0,'intron_rows':0}:
        raise ValueError('hints statistics inconsistent')
    a, b = packets['dev_003'], packets['dev_004']
    for name in ('task.md','artifacts/regions.tsv','artifacts/sequence_metrics.json'):
        if a[name] != b[name]:
            raise ValueError('masking pair task/surface statistic mismatch')
    if a['artifacts/sequence.fa'] != b['artifacts/reference.fa'] or a['artifacts/reference.fa'] != b['artifacts/sequence.fa']:
        raise ValueError('masking role exchange mismatch')
    for case, valid_mode in (('dev_003',True),('dev_004',False)):
        files = packets[case]
        header, seq = builder.fasta_records(files['artifacts/sequence.fa'].decode())[0]
        ref_header, ref_seq = builder.fasta_records(files['artifacts/reference.fa'].decode())[0]
        metrics = json.loads(files['artifacts/sequence_metrics.json'])
        if header != ref_header or len(seq) != len(ref_seq) or metrics != {'records':1,'delivery_length':len(seq),'reference_length':len(ref_seq),'ids_equal':True}:
            raise ValueError('sequence summary inconsistent')
        for interval in csv.DictReader(io.StringIO(files['artifacts/regions.tsv'].decode()),delimiter='\t'):
            start,end = int(interval['start']),int(interval['end'])
            if not 1 <= start <= end <= len(seq):
                raise ValueError('interval outside declared window')
            observed = seq[start-1:end]
            if interval['seqid'] != header or (valid_mode and any(base not in 'acgt' for base in observed)) or (not valid_mode and set(observed) != {'N'}):
                raise ValueError('sequence does not match construction reference calculation')
    return details


def load_packets(root):
    packets = {}
    for case in sorted(Path(root).iterdir()):
        if case.is_dir():
            packets[case.name] = {path.relative_to(case).as_posix(): path.read_bytes() for path in case.rglob('*') if path.is_file()}
    return packets


def validate(root, reproduce=False, sources_root=builder.DEFAULT_SOURCES):
    packets = load_packets(root)
    details = validate_packets(packets)
    if reproduce:
        regenerated = builder.generate(sources_root)
        if builder.hashes(packets) != builder.hashes(regenerated):
            raise ValueError('deterministic regeneration differs from stored packet bytes')
    return {'status':'pass', 'mode':'draft_development_only_not_freeze_ready', 'cases':len(packets),
            'local_byte_reproduction': 'passed' if reproduce else 'not_requested',
            'linux_reproduction':'pending', 'api_calls':0, 'original_source_hash_rescans':0, 'details':details}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases-root',type=Path,default=V3/'development/cases')
    parser.add_argument('--sources-root',type=Path,default=builder.DEFAULT_SOURCES)
    parser.add_argument('--reproduce',action='store_true')
    parser.add_argument('--report',type=Path)
    args = parser.parse_args()
    report = validate(args.cases_root,args.reproduce,args.sources_root)
    if args.report:
        target=args.report.resolve()
        if not target.is_relative_to(V3):
            raise ValueError('report must stay in bench/v3')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(builder.json_bytes(report))
    print('PASS: {} draft development cases; local reproduction {}; Linux pending; 0 API calls.'.format(report['cases'],report['local_byte_reproduction']))
