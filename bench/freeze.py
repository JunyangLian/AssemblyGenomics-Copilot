"""Freeze already approved v1 materials; verify their bytes without model calls."""
from __future__ import annotations
import argparse
import json
from pathlib import Path, PurePosixPath

from inject.common import digest, json_bytes

BENCH=Path(__file__).resolve().parent


def render(lock):
    lines=['# bench v1 冻结清单', '',
           f"批准日期：{lock['approval_date']}；审核人：本对话用户。", '',
           '16题答案已逐题范围确认；当前 C 包、两轴与预注册门槛已明确采用。模型调用为0。',
           '模型清单、参数、提示、A适配及评分合同在阶段3另锁定 RUN_PLAN.json；真实API仍需单独批准。', '',
           f"机器清单：FROZEN.json；SHA-256 `{digest(json_bytes(lock))}`。", '',
           '## 已确认标准答案', '', '| case_id | expected.json SHA-256 |', '|---|---|']
    for row in lock['cases']:
        lines.append(f"| {row['case_id']} | `{row['expected_sha256']}` |")
    h=lock['preregistration']
    lines += ['', '## 固定分析规格', '',
              'H1主集合：not_exposed + related_guidance，type=fault；' + '、'.join(h['h1_case_ids']) + '（N=6）。',
              'H1：C−B检出题数至少1，至少两个预先指定模型方向一致。H2：危险施压题数最多0/2。',
              'H3：C成功配对至少1/1，且C−B成功配对数至少1。主分析按题，判定/根因各取三次多数。', '',
              '## 保护文件', '',
              '以下均为相对 bench/ 的路径；源清单为已验收包的原字节副本，不含原始大产物。', '',
              '| 文件 | 字节数 | SHA-256 |', '|---|---:|---|']
    for row in lock['files']:
        lines.append(f"| {row['path']} | {row['size_bytes']} | `{row['sha256']}` |")
    lines += ['', '任何冻结内容变更须另起版本并记录 CHANGELOG；保留本版清单及结果。', '']
    return '\n'.join(lines).encode('utf-8')


def verify(root=BENCH):
    root=root.resolve(strict=True)
    p=root/'FROZEN.json'; md=root/'FROZEN.md'
    if p.is_symlink() or md.is_symlink(): raise ValueError('frozen controls cannot be symlinks')
    lock=json.loads(p.read_text(encoding='utf-8'))
    if p.read_bytes()!=json_bytes(lock) or md.read_bytes()!=render(lock):
        raise ValueError('frozen manifest/Markdown bytes differ from their canonical representation')
    seen=set()
    for row in lock['files']:
        name=row['path']; relative=PurePosixPath(name)
        if not name or relative.is_absolute() or '..' in relative.parts or ':' in name or '\\' in name or name in seen or relative.as_posix()!=name:
            raise ValueError('invalid frozen file path')
        seen.add(name); path=root/name
        if any(p.is_symlink() for p in [path,*path.parents]): raise ValueError('frozen symlink forbidden')
        if not path.is_file() or path.stat().st_size!=row['size_bytes'] or digest(path.read_bytes())!=row['sha256']:
            raise ValueError('frozen byte mismatch: '+name)
    current_cases={p.relative_to(root).as_posix() for p in (root/'cases').rglob('*') if p.is_file()}
    if current_cases!={p for p in seen if p.startswith('cases/')}:
        raise ValueError('case file roster changed')
    by_path={row['path']:row for row in lock['files']}
    ids=[row['case_id'] for row in lock['cases']]
    if len(ids)!=16 or set(ids)!={f'case_{i:03d}' for i in range(1,17)}:
        raise ValueError('approved 16-case roster differs')
    for row in lock['cases']:
        if by_path[f"cases/{row['case_id']}/expected.json"]['sha256']!=row['expected_sha256']:
            raise ValueError('answer table differs from protected bytes')
    if json.loads((root/'preregistration.json').read_text(encoding='utf-8'))!=lock['preregistration']:
        raise ValueError('registered threshold snapshot differs')
    if by_path['context/skill_context.md']['sha256']!=lock['context_sha256'] or by_path['SOURCE_MANIFEST.json']['sha256']!=lock['source_manifest_sha256']:
        raise ValueError('source/context snapshot differs')
    return {'status':'pass','protected_files':len(seen),'case_count':len(lock['cases']),
            'frozen_md_sha256':digest(md.read_bytes()),'model_calls':0}


def create(root=BENCH):
    root=root.resolve(strict=True)
    if (root/'FROZEN.md').exists() or (root/'FROZEN.json').exists():
        raise ValueError('freeze already exists; verify it, never overwrite it')
    answer_approval=json.loads((root/'REVIEW_APPROVAL.json').read_text(encoding='utf-8'))
    approval=json.loads((root/'SPEC_APPROVAL.json').read_text(encoding='utf-8'))
    spec=json.loads((root/'preregistration.json').read_text(encoding='utf-8'))
    validation=json.loads((root/'VALIDATION.json').read_text(encoding='utf-8'))
    repro=json.loads((root/'REPRODUCTION_VERIFIED.json').read_text(encoding='utf-8'))
    if approval.get('real_api_authorized') is not False or approval.get('model_calls')!=0:
        raise ValueError('this phase cannot authorize or follow model calls')
    if approval['user_reply']!='采用' or approval['adopted_spec']!=spec:
        raise ValueError('no matching explicit specification approval')
    if validation['status']!='pass' or repro['status']!='pass' or validation['model_calls'] or repro['model_calls']:
        raise ValueError('validation/reproduction not passed before model calls')
    cases=answer_approval['approved_cases']
    if len(cases)!=16: raise ValueError('expected 16 approved answers')
    for row in cases:
        if digest((root/'cases'/row['case_id']/'expected.json').read_bytes())!=row['expected_sha256']:
            raise ValueError('answer changed since human approval: '+row['case_id'])
    context_sha=digest((root/'context/skill_context.md').read_bytes())
    if approval['context_sha256']!=context_sha or repro['context_sha256']!=context_sha:
        raise ValueError('C context differs from approval/reproduction')
    metas={row['case_id']:json.loads((root/'cases'/row['case_id']/'meta.json').read_text(encoding='utf-8')) for row in cases}
    h1=sorted(k for k,m in metas.items() if m['type']=='fault' and m['skill_exposure'] in spec['h1_exposures'])
    if h1!=spec['h1_case_ids'] or len(h1)!=spec['h1_n']: raise ValueError('H1 population differs')
    if approval['case_meta_sha256']!={k:digest((root/'cases'/k/'meta.json').read_bytes()) for k in metas}:
        raise ValueError('labels/metadata differ from adopted snapshot')
    if digest((root/'SOURCE_MANIFEST.json').read_bytes())!=repro['source_manifest_sha256']:
        raise ValueError('source manifest differs from accepted receipt')
    names=['PREREGISTRATION.md','preregistration.json','REVIEW_SHEET.csv','REVIEW_APPROVAL.json',
           'SPEC_APPROVAL.json','CASE_INPUTS.json','SOURCE_MANIFEST.json','REPRODUCTION_VERIFIED.json',
           'context/skill_context.md','context/build_record.json','visible_input.py','build_cases.py','build_context.py','freeze.py','validate_cases.py']
    names += [p.relative_to(root).as_posix() for folder in ['cases','schemas','inject'] for p in (root/folder).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
    entries=[]
    for name in sorted(set(names)):
        path=root/name
        if path.is_symlink(): raise ValueError('frozen symlink forbidden')
        entries.append({'path':name,'size_bytes':path.stat().st_size,'sha256':digest(path.read_bytes())})
    lock={'benchmark_version':'v1','spec_version':'1.2','approval_date':approval['date'],
          'cases':cases,'preregistration':spec,'files':entries,
          'source_manifest_sha256':repro['source_manifest_sha256'],'context_sha256':context_sha}
    (root/'FROZEN.json').write_bytes(json_bytes(lock))
    (root/'FROZEN.md').write_bytes(render(lock))
    return verify(root)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--create',action='store_true'); args=parser.parse_args()
    print(json.dumps(create() if args.create else verify(),ensure_ascii=False,indent=2))
