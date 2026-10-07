"""Finish an already running API queue: receipt, usage, tests and local backup only."""
from datetime import datetime, timezone
import subprocess
import sys
import time
from zipfile import ZipFile, ZIP_DEFLATED

from harness_common import BENCH, digest, read_json, write_json
from run_plan import verify
from seal_api import seal
from summarize_api import summarize


def finish(root=BENCH):
    locked=verify(root);lock=root/'runs/API_ACTIVE.lock'
    if not lock.exists(): raise ValueError('no active approved queue to follow')
    owner=lock.read_bytes();deadline=time.monotonic()+6*3600
    status={'status':'waiting_for_existing_queue','plan_sha256':locked['plan_sha256'],
        'implementation_sha256':digest((root/'finish_api.py').read_bytes()),
        'started_utc':datetime.now(timezone.utc).isoformat(),'api_calls_by_this_helper':0,
        'scope':'Seal stage-3 protocol/usage only. Never call models, retry requests, score answers or start stage 4.'}
    write_json(root/'API_COMPLETION.json',status)
    print('Following existing approved queue; no additional API calls',flush=True)
    try:
        while lock.exists():
            if lock.read_bytes()!=owner: raise ValueError('active queue identity changed')
            if time.monotonic()>deadline: raise TimeoutError('queue still active after six hours; left untouched')
            time.sleep(10)
        if verify(root)['plan_sha256']!=locked['plan_sha256']: raise ValueError('run plan changed')
        receipt=seal(root);usage=summarize(root)
        test=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=root.parent,capture_output=True,
                            text=True,encoding='utf-8',errors='replace')
        (root/'runs/API_final_pytest.log').write_bytes((test.stdout+'\n'+test.stderr).replace('\r\n','\n').encode('utf-8'))
        verify(root)
        names=set(receipt['records'])
        for path in (root/'runs').glob('api_ledger_*.json'): names.add(path.relative_to(root).as_posix())
        names.update(['API_RECEIPT.json','API_RUNS.json','API_STATUS.json','API_STATUS.md',
                      'RUN_PLAN.json','RUN_PLAN.sha256','FROZEN.md','TRANSPORT_RUN1.json','runs/API_final_pytest.log'])
        prior=read_json(root/'TRANSPORT_RUN1.json')
        for name in prior['runs']: names.add(name+'/records.jsonl')
        hashes={n:digest((root/n).read_bytes()) for n in sorted(names)}
        write_json(root/'runs/API_backup_manifest.json',{'files':hashes,'contains_credentials':False,'contains_expected_answers':False})
        with ZipFile(root/'api_logs.zip','w',ZIP_DEFLATED) as z:
            for name in sorted(names): z.write(root/name,name)
            z.write(root/'runs/API_backup_manifest.json','API_backup_manifest.json')
        status.update({'status':'complete' if receipt['complete'] and test.returncode==0 else 'needs_attention',
            'finished_utc':datetime.now(timezone.utc).isoformat(),'observations':receipt['observations'],
            'planned_observations':receipt['planned_observations'],'missing_slots':receipt['missing_slots'],
            'pytest_exit_code':test.returncode,'pytest_output':'runs/API_final_pytest.log',
            'global_reserved_calls':receipt['global_reserved_calls'],'reserved_cny_not_billing':receipt['global_reserved_cny_not_billing'],
            'known_usage_cost_estimate_cny':sum(g['uncached_peak_cost_estimate_cny'] or 0 for g in receipt['groups']),
            'actual_account_deduction_cny':None,'backup':'api_logs.zip',
            'backup_sha256':digest((root/'api_logs.zip').read_bytes()),
            'A_server_results':'received' if (root/'A_RECEIPT.json').exists() else 'pending',
            'stage4_started':False})
        write_json(root/'API_COMPLETION.json',status)
        print(f'{status["status"]}: {receipt["observations"]}/288; pytest exit {test.returncode}',flush=True)
        return status
    except Exception as exc:
        status.update({'status':'needs_attention','error':str(exc),'stage4_started':False})
        write_json(root/'API_COMPLETION.json',status)
        raise


if __name__=='__main__': finish()
