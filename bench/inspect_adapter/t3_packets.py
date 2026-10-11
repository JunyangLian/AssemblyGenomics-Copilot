"""Deterministic T3 source-subset pairs; draft answers only, no model requests."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from urllib.parse import unquote

from jsonschema import Draft202012Validator
ROOT = Path(__file__).resolve().parent
DIRECTORY = ROOT / 't3_test'
RECEIPT = ROOT.parent / 'v3/SOURCE_RECEIPT.json'
V3 = ROOT.parent / 'v3'
ASSIGNMENT = [('fungi','protein'), ('nematoda','parent'), ('insecta','protein'),
              ('viridiplantae','parent'), ('mammalia','protein'), ('aves','coordinate'),
              ('actinopterygii','coordinate')]
POLICY = {'candidate_limit': 50, 'genes_selected': 2, 'max_feature_rows_per_gene': 40,
          'max_visible_bytes': 30000, 'require_multisegment_cds': True,
          'selection_order': 'source GFF order; first two individually closed, connected eligible coding blocks within byte limit',
          'same_source_pairs': True, 'api_calls': 0, 'answer_status': 'draft'}


def canonical(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',', ':'))+'\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(canonical(value))


def fasta_records(text):
    records={}
    header=None
    chunks=[]
    def save():
        if header is not None:
            name=header.split()[0]
            if name in records or not chunks:
                raise ValueError('duplicate or empty FAA record')
            records[name]=(header,''.join(chunks))
    for line in text.splitlines():
        if line.startswith('>'):
            save()
            header=line[1:]
            if not header.split():
                raise ValueError('empty FAA header')
            chunks=[]
        elif line.strip():
            if header is None or any(c.isspace() for c in line.strip()):
                raise ValueError('invalid FAA sequence layout')
            chunks.append(line.strip())
    save()
    if not records:
        raise ValueError('empty FAA')
    return records


def attributes(row):
    pairs = [item.split('=',1) for item in row[8].split(';') if item]
    if any(len(item)!=2 for item in pairs) or len({k for k,v in pairs}) != len(pairs):
        raise ValueError('invalid or duplicate GFF attribute')
    return {unquote(k): unquote(v) for k,v in pairs}


def parse_gff(text):
    rows = []
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        row = line.split('\t')
        if len(row)!=9 or not 1 <= int(row[3]) <= int(row[4]):
            raise ValueError('invalid GFF row/coordinates')
        attributes(row)
        rows.append(row)
    return rows


def relations(rows, proteins):
    """File-level reference oracle; not group A or an upstream causal inference."""
    index = {}
    for number,row in enumerate(rows,2):
        attrs=attributes(row)
        if 'ID' not in attrs:
            raise ValueError('selected feature lacks ID')
        index.setdefault(attrs['ID'],[]).append((number,row,attrs))
    unresolved, incompatible, missing = [], [], []
    for number,row in enumerate(rows,2):
        attrs=attributes(row)
        if row[2]=='gene':
            if attrs.get('Parent'):
                incompatible.append(number)
            continue
        parents=attrs.get('Parent','').split(',')
        for parent in parents:
            matches=index.get(parent,[])
            if not matches:
                unresolved.append(number)
                continue
            if len(matches)!=1:
                raise ValueError('selected Parent refers to a multipart feature')
            _,outer,_=matches[0]
            allowed_type = outer[2]=='gene' if row[2]=='mRNA' else outer[2]=='mRNA'
            if (not allowed_type or row[0]!=outer[0] or row[6]!=outer[6] or
                    not int(outer[3]) <= int(row[3]) <= int(row[4]) <= int(outer[4])):
                incompatible.append(number)
        if row[2]=='CDS' and attrs.get('protein_id') not in proteins:
            missing.append(number)
    for key,values in index.items():
        if len(values)>1 and (any(row[2]!='CDS' for _,row,a in values) or
                len({(row[0],row[6],a.get('Parent'),a.get('protein_id')) for _,row,a in values})!=1):
            raise ValueError('inconsistent repeated feature ID')
    cds_ids={attributes(r).get('protein_id') for r in rows if r[2]=='CDS'}
    return {'missing_sequence_lines':sorted(set(missing)), 'unresolved_parent_lines':sorted(set(unresolved)),
            'incompatible_parent_lines':sorted(set(incompatible)), 'extra_protein_ids':sorted(set(proteins)-cds_ids)}


def eligible_blocks(path):
    """Keep all original rows from gene to next gene; reject nonclosed candidates."""
    current=[]
    with gzip.open(path,'rt',encoding='utf-8') as handle:
        for line in handle:
            if not line.strip() or line.startswith('#'):
                continue
            row=line.rstrip('\r\n').split('\t')
            if len(row)!=9:
                raise ValueError('source GFF has non-nine-column row')
            if row[2]=='gene':
                if current:
                    yield current
                current=[row]
            elif current:
                current.append(row)
        if current:
            yield current


def candidate_blocks(path):
    result=[]
    for block in eligible_blocks(path):
        if (len(block)>POLICY['max_feature_rows_per_gene'] or
                attributes(block[0]).get('gene_biotype')!='protein_coding' or
                any(r[2] not in {'gene','mRNA','exon','CDS'} for r in block)):
            continue
        cds=[r for r in block if r[2]=='CDS']
        ids={attributes(r).get('protein_id') for r in cds}
        if not cds or None in ids:
            continue
        if max(Counter(attributes(r)['ID'] for r in cds).values())<2:
            continue
        try:
            facts=relations(block,{name: ('','') for name in ids})
        except ValueError:
            continue
        if any(facts.values()):
            continue
        result.append(block)
        if len(result)==POLICY['candidate_limit']:
            break
    return result


def protein_subset(path,wanted):
    result={}
    header=None
    seq=[]
    def save():
        if header and header.split()[0] in wanted:
            key=header.split()[0]
            if key in result or not seq:
                raise ValueError('duplicate or empty selected FAA record')
            result[key]=(header,''.join(seq))
    with gzip.open(path,'rt',encoding='utf-8') as handle:
        for line in handle:
            if line.startswith('>'):
                save()
                if set(result)==wanted:
                    break
                header=line[1:].rstrip('\r\n')
                seq=[]
            elif line.strip():
                if header is None:
                    raise ValueError('sequence before source FAA header')
                seq.append(line.strip())
        else:
            save()
    return result


def gff_bytes(rows):
    return ('##gff-version 3\n'+''.join('\t'.join(row)+'\n' for row in rows)).encode('utf-8')


def faa_bytes(records):
    return ''.join('>'+header+'\n'+''.join(seq[i:i+60]+'\n' for i in range(0,len(seq),60))
                   for header,seq in records.values()).encode('utf-8')


def surface(rows,proteins):
    counts=Counter(row[2] for row in rows)
    return {'gene_rows':counts['gene'],'mrna_rows':counts['mRNA'],'cds_rows':counts['CDS'],
            'exon_rows':counts['exon'],'unique_cds_ids':len({attributes(r)['ID'] for r in rows if r[2]=='CDS'}),
            'protein_records':len(proteins),'protein_residues':sum(len(seq) for h,seq in proteins.values())}


def task(species):
    return f'''# 下游输入审核

请审核{species.replace('_',' ')}的一组结构注释记录是否可以交给下游文件连接程序。输出统一规定的JSON。

本题审核输入文件，不是已完成的分析交付；没有提供可回退的旧版本。审核范围仅为给出的两套完整编码gene特征块及对应蛋白，不能外推全基因组注释质量。models.gff3是本次输入，proteins.faa是按ID查找序列的输入；record_counts.json仅列字面计数。

消费者读取GFF的Parent建立gene→mRNA→exon/CDS关系，并按每行CDS的protein_id精确查找FAA header第一个token。每个Parent必须在本题完整记录中存在且类型符合上述层级；子记录必须与父记录同seqid、同链，闭区间完全位于父记录内。FAA记录与不同protein_id对应的一组CDS一一相接。没有声明去版本号、改大小写、以Name或CDS ID代替protein_id等映射。

同一CDS的多片段可以重复ID，不能把CDS行数当蛋白条数。允许异构体和partial=true，不检查模型全长、翻译正确性或生物学功能；这些属性不豁免上述文件连接要求。除必要输入合同外，本题没有其它继续条件，也没有提供运行日志来解释上游过程。

请根据公开记录检查必要合同，并建议最小修复或补证。满足所有必要输入要求时可继续；必要连接或层级要求不能满足时，应先停止下游启动并修复。不要仅凭字面计数接近就认为可以继续。
'''


def replace_attribute(row,key,value):
    items=row[8].split(';')
    if sum(item.startswith(key+'=') for item in items)!=1:
        raise ValueError('cannot uniquely replace attribute')
    row[8]=';'.join(key+'='+value if item.startswith(key+'=') else item for item in items)


def change(rows,proteins,mode):
    altered=copy.deepcopy(rows)
    if mode=='protein':
        old=next(attributes(r)['protein_id'] for r in rows if r[2]=='CDS')
        prefix,number=old.rsplit('.',1)
        new=prefix+'.'+str(int(number)+100)
        if new in proteins:
            raise ValueError('replacement protein identifier already exists')
        for row in altered:
            if row[2]=='CDS' and attributes(row)['protein_id']==old:
                replace_attribute(row,'protein_id',new)
        detail={'attribute':'protein_id','before':old,'after':new,'policy':'all segments of one CDS; no other field changes'}
    elif mode=='parent':
        row=next(r for r in altered if r[2]=='mRNA')
        old=attributes(row)['Parent']
        new=old+'_1'
        if new in {attributes(r)['ID'] for r in rows}:
            raise ValueError('replacement Parent exists')
        replace_attribute(row,'Parent',new)
        detail={'attribute':'Parent','before':old,'after':new,'policy':'one mRNA edge; other rows unchanged'}
    else:
        row=next(r for r in altered if r[2]=='CDS')
        parent=next(r for r in rows if attributes(r)['ID']==attributes(row)['Parent'])
        old=row[3:5]
        start=int(parent[4])+1
        row[3:5]=[str(start),str(start+int(old[1])-int(old[0]))]
        detail={'attribute':'CDS coordinates','before':old,'after':row[3:5],
                'policy':'one segment moved just beyond its own mRNA end, same segment length'}
    return altered,detail


def source_groups():
    receipt=read_json(RECEIPT)
    bundle=Path(receipt['bundle_path'])
    groups={}
    for record in receipt['sources']:
        path=bundle/record['package_path']
        if not path.is_file() or path.stat().st_size!=record['copy_signature']['size_bytes']:
            raise ValueError('received source missing or size changed: '+record['package_path'])
        groups.setdefault(record['clade'],{})[record['kind']]=(record,path)
    if set(groups)!={clade for clade,mode in ASSIGNMENT}:
        raise ValueError('seven source groups unavailable')
    return groups


def extract():
    if (DIRECTORY/'FROZEN.json').exists():
        raise ValueError('test version frozen; cannot extract')
    groups=source_groups()
    selected={}
    for clade,mode in ASSIGNMENT:
        gff,gff_path=groups[clade]['gff']
        faa,faa_path=groups[clade]['faa']
        candidates=candidate_blocks(gff_path)
        wanted={attributes(r)['protein_id'] for block in candidates for r in block if r[2]=='CDS'}
        available=protein_subset(faa_path,wanted)
        kept=[]
        for block in candidates:
            names=list(dict.fromkeys(attributes(r)['protein_id'] for r in block if r[2]=='CDS'))
            if any(name not in available for name in names):
                continue
            tentative=kept+[block]
            all_rows=[r for b in tentative for r in b]
            all_names=list(dict.fromkeys(attributes(r)['protein_id'] for r in all_rows if r[2]=='CDS'))
            records={name:available[name] for name in all_names}
            size=len(gff_bytes(all_rows))+len(faa_bytes(records))+len(task(gff['species']).encode('utf-8'))+512
            if size>POLICY['max_visible_bytes'] or any(relations(all_rows,records).values()):
                continue
            kept=tentative
            if len(kept)==POLICY['genes_selected']:
                selected[clade]={'rows':all_rows,'proteins':records,'mode':mode,'sources':[gff,faa],
                    'gene_ids':[attributes(b[0])['ID'] for b in kept],'candidate_blocks_examined':len(candidates)}
                break
        if clade not in selected:
            raise ValueError('source cannot support two complete connected blocks: '+clade)
        print('EXTRACTED: '+clade+' '+gff['source_group']+'; '+str(len(all_rows))+' feature rows',flush=True)
    target=DIRECTORY/'selection/SOURCE_SUBSETS.json'
    if target.exists() and target.read_bytes()!=canonical(selected):
        raise ValueError('source selection differs; use another version')
    write_json(target,selected)
    return selected


def evidence(number,statement,pointers,method='record_connection'):
    return {'claim_id':f'E{number:02d}','statement':statement,'acceptable_pointers':pointers,
            'verification_method':method,'required_for_joint':True,'review_note':'Author AI draft; not independent human review; pending user approval.'}


def generate(selected):
    packets={}
    for index,(clade,mode) in enumerate(ASSIGNMENT,1):
        record=selected[clade]
        before=record['rows']
        proteins={k:tuple(v) for k,v in record['proteins'].items()}
        altered,detail=change(before,proteins,mode)
        pair=f'T3P{index}'
        for offset,rows in enumerate((before,altered)):
            cid=f't3_{2*index-1+offset:03d}'
            public={'task.md':task(record['sources'][0]['species']).encode('utf-8'),
                    'artifacts/models.gff3':gff_bytes(rows),'artifacts/proteins.faa':faa_bytes(proteins),
                    'artifacts/record_counts.json':canonical(surface(rows,proteins))}
            facts=relations(rows,proteins)
            if offset:
                key={'protein':'missing_sequence_lines','parent':'unresolved_parent_lines','coordinate':'incompatible_parent_lines'}[mode]
                observed={'protein':'gff_faa_link_missing','parent':'gff_reference_unresolved','coordinate':'gff_hierarchy_inconsistent'}[mode]
                cause='id_mismatch' if mode=='protein' else 'gff_hierarchy_error'
                line=facts[key][0]
                normal_line=2 if mode=='parent' else next(i for i,r in enumerate(before,2) if r[2]=='mRNA')
                statement={'protein':'CDS的protein_id在本题FAA首token集合中没有序列，不能用Name或其它标识替代。',
                           'parent':'本题完整特征块内，一个mRNA的Parent没有对应gene记录。',
                           'coordinate':'一个CDS片段的区间完全越过其mRNA父区间，不能建立题面要求的层级。'}[mode]
                pointers=list(dict.fromkeys([f'artifacts/models.gff3:{line}',
                    'artifacts/proteins.faa:1'] if mode=='protein' else [f'artifacts/models.gff3:{line}',f'artifacts/models.gff3:{normal_line}']))
                answer=evidence(1,statement,pointers)
                verdict='block'
            else:
                observed=cause='none'
                verdict='pass'
                cds_line=next(i for i,r in enumerate(rows,2) if r[2]=='CDS')
                answer=evidence(1,'所有不同CDS protein_id均与FAA首token精确相接；多片段CDS行数不作为蛋白数。',
                    [f'artifacts/models.gff3:{cds_line}','artifacts/proteins.faa:1','artifacts/record_counts.json:protein_records'])
            sources=[{'path':s['package_path'],'sha256':s['sha256'],'source_origin':s['source_path'],
                'source_group':s['source_group'],'selection':json.dumps({'gene_ids':record['gene_ids'],
                    'policy':POLICY,'source_receipt_sha256':digest(RECEIPT.read_bytes()),
                    'transform':detail if offset else 'original feature rows and original complete protein sequences'},ensure_ascii=False,sort_keys=True)} for s in record['sources']]
            contract={'review_target':'input','scope':'declared_subset','consumer_contract':'完整Parent层级、同seqid/链、闭区间包含及CDS protein_id与FAA首token精确一一相接；允许partial与多片段',
                'allowed_id_mapping':'仅精确匹配，不使用Name或CDS ID替代','artifact_roles':{
                    'delivery':['artifacts/models.gff3','artifacts/proteins.faa','artifacts/record_counts.json'],'reference':[]},'usable_previous_result':False}
            meta={'schema_version':'v3-spec-draft-1','case_id':cid,'source_group':record['sources'][0]['source_group'],
                'split':'sealed_test','stage':'structural_annotation','type':'fault' if offset else 'normal',
                'mechanism_family':{'protein':'protein_identifier_connection','parent':'parent_reference_closure','coordinate':'child_parent_interval'}[mode],
                'pitfall_exposure':'held_out','pitfall_ids':[], 'guidance_exposure':'unassigned','guidance_version_sha256':None,
                'source_files':sources,'injection_script':'bench/inspect_adapter/t3_packets.py','seed':0,
                'synthetic':True,'pair_id':pair,'pressure_parent':None,'visible_contract':contract,
                'verbatim_tool_exceptions':[],'excerpt_policy':'两个原始完整编码gene块、所有子记录及关联完整FAA；闭包/连接参考核算后选样。格式子集标synthetic，不声称重跑原注释。',
                'review_status':'draft'}
            expected={'schema_version':'v3-spec-draft-1','case_id':cid,'acceptable_decisions':[{
                'verdict':verdict,'observed_defect':observed,'root_cause':cause}],
                'root_identifiability':'confirmed' if offset else 'no_defect','key_evidence':[answer] if offset else [answer,
                    evidence(2,'两套完整gene块内每条Parent能接续，类型、同序列/链及闭区间包含成立。',
                        ['artifacts/models.gff3:2',f"artifacts/models.gff3:{next(i for i,r in enumerate(rows,2) if r[2]=='mRNA')}"])],
                'rationale':'仅确认本题文件级连接缺陷，不推测造成它的历史运行或生物学原因。' if offset else '在明确的输入子集合同内可继续，不声明全基因组注释正确。',
                'pair_id':pair,'independent_review_status':'pending','user_approved':False}
            packets[cid]={**public,'meta.json':canonical(meta),'expected.json':canonical(expected)}
    return packets


def validate(packets):
    validators={n:Draft202012Validator(read_json(DIRECTORY/'schemas'/f'{n}.schema.json')) for n in ('case_meta','expected')}
    schema=read_json(DIRECTORY/'schemas/model_output.schema.json')
    enums=set(schema['properties']['root_cause']['enum']+schema['properties']['observed_defect']['enum'])
    strict=[w for w in enums if '_' in w]
    words=[w for w in enums if '_' not in w]+['fault','bad','injected','injection','truncated']
    sources={(s['source_group'],s['package_path'],s['sha256'],s['source_path']) for s in read_json(RECEIPT)['sources']}
    actual={}
    if len(packets)!=14:
        raise ValueError('expected fourteen draft packets')
    for cid,files in packets.items():
        meta=json.loads(files['meta.json']);expected=json.loads(files['expected.json'])
        validators['case_meta'].validate(meta);validators['expected'].validate(expected)
        if meta['case_id']!=cid or expected['case_id']!=cid or expected['user_approved']:
            raise ValueError('identity or premature approval')
        for s in meta['source_files']:
            if (s['source_group'],s['path'],s['sha256'],s['source_origin']) not in sources or s['source_group']!=meta['source_group']:
                raise ValueError('source binding mismatch')
        public={n:b for n,b in files.items() if n=='task.md' or n.startswith('artifacts/')}
        for name,data in public.items():
            text=name+'\n'+data.decode('utf-8')
            if b'\r' in data or re.search(r'(?:expected|meta)\.json',text,re.I):
                raise ValueError('private filename or non-LF visible text')
            if any(w.casefold() in text.casefold() for w in strict) or any(re.search(r'(?<![A-Za-z0-9_])'+re.escape(w)+r'(?![A-Za-z0-9_])',text,re.I) for w in words):
                raise ValueError('visible label/injection trace: '+name)
        if sum(len(b) for b in public.values())>POLICY['max_visible_bytes']:
            raise ValueError('public packet byte ceiling exceeded')
        rows=parse_gff(public['artifacts/models.gff3'].decode())
        proteins=fasta_records(public['artifacts/proteins.faa'].decode())
        if json.loads(public['artifacts/record_counts.json'])!=surface(rows,proteins):
            raise ValueError('surface statistics differ from actual records')
        facts=relations(rows,proteins)
        decision=expected['acceptable_decisions'][0]
        defect=any(facts.values())
        if defect!=(decision['verdict']=='block'):
            raise ValueError('reference facts disagree with draft decision')
        family=meta['mechanism_family']
        expected_label={'protein_identifier_connection':('gff_faa_link_missing','id_mismatch'),
                        'parent_reference_closure':('gff_reference_unresolved','gff_hierarchy_error'),
                        'child_parent_interval':('gff_hierarchy_inconsistent','gff_hierarchy_error')}[family]
        observed,cause=expected_label if defect else ('none','none')
        if (decision['observed_defect'],decision['root_cause'])!=(observed,cause):
            raise ValueError('draft defect/cause labels disagree with mechanism')
        if defect:
            required={'protein_identifier_connection':'missing_sequence_lines',
                      'parent_reference_closure':'unresolved_parent_lines',
                      'child_parent_interval':'incompatible_parent_lines'}[family]
            if not facts[required] or any(facts[k] for k in facts if k not in {required,'extra_protein_ids'}):
                raise ValueError('fault introduces a different hierarchy mechanism')
            if family!='protein_identifier_connection' and facts['extra_protein_ids']:
                raise ValueError('unexpected protein set difference')
        for fact in expected['key_evidence']:
            for pointer in fact['acceptable_pointers']:
                name,loc=pointer.split(':',1)
                if name not in public:
                    raise ValueError('private evidence pointer')
                if loc.isdigit():
                    if not 1<=int(loc)<=len(public[name].decode().splitlines()):
                        raise ValueError('missing evidence line')
                elif not name.endswith('.json') or loc not in json.loads(public[name]):
                    raise ValueError('missing evidence field')
        actual[cid]={'source_group':meta['source_group'],'type':meta['type'],'visible_bytes':sum(len(b) for b in public.values()),
                    'reference_facts':facts,'draft_decision':decision,'answer_status':'pending user review'}
    for index in range(1,8):
        a,b=(packets[f't3_{2*index-1+o:03d}'] for o in (0,1))
        if any(a[n]!=b[n] for n in ('task.md','artifacts/record_counts.json','artifacts/proteins.faa')):
            raise ValueError('paired surface/task differs')
    return actual


def build():
    if (DIRECTORY/'FROZEN.json').exists():
        raise ValueError('test version frozen; cannot rebuild')
    selected=read_json(DIRECTORY/'selection/SOURCE_SUBSETS.json')
    packets=generate(selected)
    actual=validate(packets)
    for cid,files in packets.items():
        for name,data in files.items():
            path=DIRECTORY/'cases'/cid/name
            path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and path.read_bytes()!=data:
                raise ValueError('existing draft differs; version changes before overwrite')
            path.write_bytes(data)
    write_json(DIRECTORY/'VALIDATION.json',{'status':'pass','cases':actual,'api_calls':0,
        'unresolved_pre_freeze':['user review','shared prompt/guidance assignment','Windows/Linux reproduction'],
        'selection_sha256':digest((DIRECTORY/'selection/SOURCE_SUBSETS.json').read_bytes()),'builder_sha256':digest(Path(__file__).read_bytes())})
    write_json(DIRECTORY/'CASE_MANIFEST.json',{'files':{cid+'/'+name:digest(data) for cid,files in packets.items() for name,data in files.items()},
        'policy':POLICY,'source_receipt_sha256':digest(RECEIPT.read_bytes()),'answers':'draft, not frozen'})
    buffer=io.StringIO(newline='')
    writer=csv.writer(buffer,lineterminator='\n')
    writer.writerow(['case_id','source_group','type','pair_id','mechanism','candidate_verdict','observed_defect','root_cause','evidence','user_comments'])
    for cid,files in packets.items():
        m=json.loads(files['meta.json']);e=json.loads(files['expected.json']);d=e['acceptable_decisions'][0]
        writer.writerow([cid,m['source_group'],m['type'],m['pair_id'],m['mechanism_family'],d['verdict'],d['observed_defect'],d['root_cause'],e['key_evidence'][0]['statement'],''])
    (DIRECTORY/'REVIEW_SHEET.csv').write_bytes(buffer.getvalue().encode('utf-8'))
    print('PASS: fourteen reproducible draft packets, seven sources; no API, no frozen answers')
    return packets


def prepare():
    if (DIRECTORY/'FROZEN.json').exists():
        raise ValueError('test version frozen; cannot prepare')
    (DIRECTORY/'schemas').mkdir(parents=True,exist_ok=True)
    for name in ('case_meta','expected','model_output'):
        target=DIRECTORY/'schemas'/f'{name}.schema.json'
        data=(V3/'schemas'/f'{name}.schema.json').read_bytes()
        if target.exists() and target.read_bytes()!=data:
            raise ValueError('schema differs; use another version')
        target.write_bytes(data)
    extract()
    return build()


def reproduction_package():
    build()
    contents={'t3_packets.py':Path(__file__).read_bytes(),'source_receipt.json':RECEIPT.read_bytes(),
              'reproduce_cases.py':(DIRECTORY/'server/reproduce_cases.py').read_bytes(),
              't3_test/CASE_MANIFEST.json':(DIRECTORY/'CASE_MANIFEST.json').read_bytes(),
              't3_test/selection/SOURCE_SUBSETS.json':(DIRECTORY/'selection/SOURCE_SUBSETS.json').read_bytes()}
    contents.update({'t3_test/schemas/'+p.name:p.read_bytes() for p in sorted((DIRECTORY/'schemas').glob('*.json'))})
    target=DIRECTORY/'reproduction_package.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(contents.items()):
            info=zipfile.ZipInfo('t3_reproduction/'+name,date_time=(2026,10,11,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3
            info.external_attr=0o100644<<16
            archive.writestr(info,data)
    write_json(DIRECTORY/'PACKAGE_RECEIPT.json',{'archive_sha256':digest(target.read_bytes()),
        'files':{n:digest(b) for n,b in sorted(contents.items())},'api_calls':0,'answers':'draft',
        'includes_original_large_sources':False,'purpose':'Windows/Linux generation parity; not re-extraction from original sources'})
    print('PACKAGE: '+str(target))
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','build','package'))
    {'prepare':prepare,'build':build,'package':reproduction_package}[parser.parse_args().action]()
