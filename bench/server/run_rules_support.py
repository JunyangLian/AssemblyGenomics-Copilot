"""Locate pinned original rules under bench without changing the frozen executor."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent


def safe_child(root, relative):
    rel=PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts or '\\' in relative or ':' in relative:
        raise ValueError('unsafe support path')
    target=root.joinpath(*rel.parts)
    if any(p.is_symlink() for p in [target,*target.parents]):
        raise ValueError('symlink support/output path forbidden')
    if root.resolve() not in target.resolve().parents:
        raise ValueError('support path escaped root')
    return target


def load_server(package):
    spec=importlib.util.spec_from_file_location('bench_original_server_rules',package/'server/run_rules.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def execute(base=BASE):
    bench=base.parent.resolve(strict=True)
    package=bench/'rules_package'
    sys.path.insert(0,str(package))
    from transfer import verify, manifest, write_json, files, sha256
    verify(base);verify(package)
    plan=json.loads((package/'SERVER_PLAN.json').read_text(encoding='utf-8'))
    sources=plan['rule_sources']
    source_root=base/'original_rules'
    if set(files(source_root))!=set(sources):
        raise ValueError('original rule source set differs from frozen server plan')
    for name,expected in sources.items():
        if hashlib.sha256(safe_child(source_root,name).read_bytes()).hexdigest()!=expected:
            raise ValueError('original rule source identity differs: '+name)
    # Runtime outputs stay outside the immutable support/input manifests.
    repo=safe_child(bench,'rules_support_work/original_rules')
    for name in sources:
        target=safe_child(repo,name);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source_root/name,target)
    runtime_files={n for n in files(repo) if n.startswith(('scripts/','knowledge/'))}
    if runtime_files!=set(sources):
        raise ValueError('unexpected original rules in runtime directory; leave them untouched')
    workspace=repo/'bench';workspace.mkdir(parents=True,exist_ok=True)
    status=load_server(package).execute(package=package,bench=workspace)
    relative=plan['output_root']
    if not relative.startswith('bench_transfer/'):
        raise ValueError('output must be inside bench_transfer')
    produced=safe_child(workspace,relative)
    verify(produced)
    output=safe_child(bench,relative);output.mkdir(parents=True,exist_ok=True)
    # Publish the unchanged executor's full result bundle at the documented path.
    for name,path in files(produced).items():
        target=safe_child(output,name);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
    write_json(output/'execution_layout.json',{
        'purpose':'Pinned original rule sources located under bench; no new QC rules or model calls',
        'rules_root':str(repo),'input_package':str(package),'output_root':str(output),
        'wrapper_sha256':sha256(base/'run.py'),'support_manifest_sha256':sha256(base/'MANIFEST.json'),
        'original_rule_sources':sources,'original_adapter_files':plan['adapter_files'],
        'api_calls':0,'verdict_mapping_changed':False})
    manifest(output)
    print(f'{status["status"].upper()}: {status["observations"]} A observations; 0 API calls')
    print('Final bundle: '+str(output))
    print('MANIFEST.json SHA-256: '+sha256(output/'MANIFEST.json'))
    return output,status


if __name__=='__main__': execute()
