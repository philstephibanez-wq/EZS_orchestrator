#!/usr/bin/env python3
"""EZS: controlled FIFO recovery for already-admitted LAB #204 and #205.

No new queue admission, scientific worker, DB mutation or scheduling logic.
Only Symfony Messenger (global_queue) and the preexisting LAB bridge can claim.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import datetime
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from urllib.parse import quote

ORCH=Path('H:/EZS_orchestrator')
LAB=Path('H:/EZStudio_lab')
GLOBAL=ORCH/'data/queue/global.sqlite'
LOCAL=LAB/'data/benchmark.sqlite'
BATCH=((9,204),(10,205))
TOKEN=re.compile(r'^[A-Za-z0-9._~+/=\-]{32,256}$')

class Refusal(RuntimeError): pass

def require(ok, reason):
    if not ok: raise Refusal(reason)

def setting(root,name):
    """Explicit allowlist caller; never print or persist the values."""
    v=os.environ.get(name)
    if v: return v
    path=root/'.env.local'
    if not path.is_file() or path.is_symlink(): return ''
    matches=[]
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        m=re.fullmatch(r'\s*'+re.escape(name)+r'\s*=\s*(.*?)\s*',line)
        if m:
            v=m.group(1).strip()
            if len(v)>=2 and v[0] in '\"\'' and v[-1]==v[0]:v=v[1:-1]
            matches.append(v)
    return matches[0] if len(matches)==1 else ''

def open_ro(path):
    require(path.is_file() and not path.is_symlink(),'SQLITE_NOT_A_FILE')
    db=sqlite3.connect('file:'+quote(path.as_posix(),safe='/:')+'?mode=ro',uri=True,timeout=3)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db

def status():
    with closing(open_ro(GLOBAL)) as q, closing(open_ro(LOCAL)) as l:
        require(q.execute('PRAGMA quick_check').fetchone()[0]=='ok','QUEUE_DB_CHECK_FAILED')
        require(l.execute('PRAGMA quick_check').fetchone()[0]=='ok','LAB_DB_CHECK_FAILED')
        busy=q.execute("SELECT id FROM global_queue_jobs WHERE state='running' LIMIT 1").fetchone()
        require(busy is None,'GLOBAL_JOB_ALREADY_RUNNING')
        busy=l.execute("SELECT id FROM analysis_jobs WHERE status IN ('running','cancelling') LIMIT 1").fetchone()
        require(busy is None,'LAB_JOB_ALREADY_RUNNING')
        result=[]
        for global_id,lab_id in BATCH:
            g=q.execute('SELECT id,producer,external_id,kind,state,claim_generation FROM global_queue_jobs WHERE id=?',(global_id,)).fetchone()
            j=l.execute("""SELECT j.id,j.kind,j.status,j.dispatch_owner,j.scientific_run_id,o.state AS admission_state,
                                  o.global_job_id,r.state AS scientific_state
                          FROM analysis_jobs j
                          JOIN global_queue_admission_outbox o ON o.job_id=j.id
                          JOIN scientific_runs r ON r.id=j.scientific_run_id
                          WHERE j.id=?""",(lab_id,)).fetchone()
            require(g is not None and j is not None,'JOB_NOT_FOUND_'+str(global_id))
            require((g['producer'],g['external_id'],g['kind'])==('lab','analysis_job:'+str(lab_id),'profile'),'GLOBAL_IDENTITY_MISMATCH_'+str(global_id))
            require(j['dispatch_owner']=='orchestrator' and j['kind']=='profile' and j['admission_state']=='admitted' and int(j['global_job_id'])==global_id,'LAB_IDENTITY_MISMATCH_'+str(global_id))
            require(g['state'] in ('queued','completed') and j['status'] in ('queued','completed'),'JOB_NOT_RECOVERABLE_'+str(global_id))
            require((g['state']=='queued' and j['status']=='queued' and j['scientific_state']=='queued') or
                    (g['state']=='completed' and j['status']=='completed' and j['scientific_state']=='done'),
                    'GLOBAL_LAB_STATE_DIVERGENCE_'+str(global_id))
            result.append((global_id,lab_id,g['state']))
        head=q.execute("SELECT id FROM global_queue_jobs WHERE state='queued' AND id >= 9 ORDER BY created_at,id LIMIT 1").fetchone()
        pending=next((item[0] for item in result if item[2]=='queued'),None)
        if pending is not None:
            require(head is not None and head['id']==pending,'ACTIVE_FIFO_HEAD_MISMATCH')
        return result

def check_processes():
    # Refuse ambiguity; no killing/adoption/claim of an existing process.
    require(os.name=='nt','WINDOWS_MAIN_ONLY')
    ps=r"""$ErrorActionPreference='Stop'
Get-CimInstance Win32_Process | Where-Object {
 $_.Name -in @('php.exe','python.exe','pythonw.exe') -and $_.CommandLine -and
 ($_.CommandLine -match 'messenger:consume\s+global_queue' -or
  $_.CommandLine -match 'lab:queue:execute-profile' -or
  $_.CommandLine -match 'queue_profile_jobobject_launcher')
} | ForEach-Object { $_.ProcessId }"""
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],capture_output=True,text=True,timeout=25)
    require(r.returncode==0,'WINDOWS_PROCESS_INVENTORY_FAILED')
    require(not r.stdout.strip(),'ANOTHER_CONSUMER_OR_EXECUTOR_EXISTS')

def configuration():
    require((ORCH/'VERSION').read_text(encoding='utf8').strip()=='4.3a17','ORCHESTRATOR_VERSION_MISMATCH')
    require((LAB/'VERSION').read_text(encoding='utf8').strip()=='1.6a20','LAB_VERSION_MISMATCH')
    require(setting(ORCH,'EZS_QUEUE_ACTIVE_FROM_ID')=='9','CUTOVER_MUST_BE_9')
    require(setting(ORCH,'EZS_QUEUE_EXECUTOR_API')=='1','ORCH_EXECUTOR_API_DISABLED')
    require(setting(LAB,'EZSTUDIO_GLOBAL_QUEUE_EXECUTOR')=='1','LAB_EXECUTOR_DISABLED')
    require(setting(LAB,'EZSTUDIO_GLOBAL_QUEUE_ADMISSION')=='1','LAB_ADMISSION_DISABLED')
    for key in ('EZS_QUEUE_EXECUTOR_TOKEN','EZS_QUEUE_LAB_RESULT_ATTESTATION_KEY','EZS_QUEUE_LAB_TOKEN'):
        a=setting(ORCH,key);b=setting(LAB,key)
        require(bool(TOKEN.fullmatch(a)) and a==b,'MISMATCHED_'+key+'_REDACTED')
    require((ORCH/'bin/console').is_file() and (LAB/'bin/console').is_file(),'SYMFONY_CONSOLE_MISSING')
    require((ORCH/'config/packages/messenger.yaml').is_file(),'MESSENGER_TRANSPORT_MISSING')
    require('global_queue:' in (ORCH/'config/packages/messenger.yaml').read_text(encoding='utf8'),'MESSENGER_TRANSPORT_DISABLED')
    p=setting(LAB,'EZSTUDIO_PROFILE_PYTHON') or 'H:/Python/pythoncore-3.14-64/python.exe'
    require(Path(p).is_file(),'PROFILE_PYTHON_MISSING')
    return p

def environment(profile_python):
    # Supply the same preexisting LAB scientific context as the historical one-shot launcher.
    env=os.environ.copy()
    for key in ('EZSTUDIO_GLOBAL_QUEUE_EXECUTOR','EZSTUDIO_GLOBAL_QUEUE_ADMISSION',
                'EZS_QUEUE_EXECUTOR_TOKEN','EZS_QUEUE_LAB_RESULT_ATTESTATION_KEY','EZS_QUEUE_LAB_TOKEN'):
        env[key]=setting(LAB,key)
    env['EZS_QUEUE_ACTIVE_FROM_ID']='9'
    env['EZS_QUEUE_RECOVERY_ONLY']='9,10'
    env['EZSTUDIO_PROFILE_PYTHON']=profile_python
    env['APP_ENV']='dev';env['APP_DEBUG']='1'
    env['EZSTUDIO_PYTHON']=profile_python
    env['AI_MODELS_ROOT']='H:/AIModels'
    env['BS_ROFORMER_MODELS_PATH']='H:/AIModels/audio/separation/bs-roformer'
    env['MELBAND_ROFORMER_MODELS_PATH']='H:/AIModels/audio/separation/melband-roformer'
    env['EZSTUDIO_PROFILE_MODELS']='H:/AIModels/audio/profile'
    env['EZSTUDIO_BEAT_THIS_CHECKPOINT']='H:/AIModels/audio/rhythm/beat-this/beat_this-final0.ckpt'
    storage=LAB/'var/storage';runtime=LAB/'var/runtime';temporary=LAB/'var/tmp';logs=LAB/'var/logs'
    mapping={
      'EZSTUDIO_STORAGE_ROOT':storage,'EZSTUDIO_TMP_ROOT':temporary,'EZSTUDIO_LOG_ROOT':logs,
      'EZSTUDIO_RUNTIME_ROOT':storage,'EZSTUDIO_DEP_ROOT':runtime/'deps',
      'EZSTUDIO_PROFILE_DEP_ROOT':runtime/'deps/profile-r3b12',
      'EZSTUDIO_PROFILE_R3B13_DEP_ROOT':runtime/'deps/profile-r3b13',
      'EZSTUDIO_PROFILE_R3B10_DEP_ROOT':runtime/'deps/profile-r3b10',
      'EZSTUDIO_PASST_PYTHON':runtime/'venvs/passt-r3b12/Scripts/python.exe',
      'EZSTUDIO_PASST_TORCH_HOME':runtime/'cache/passt-torch-home',
      'PANNS_LABELS_CSV':runtime/'deps/panns-data/class_labels_indices.csv',
      'EZSTUDIO_TORCH_HOME':runtime/'cache/torch-home',
      'EZSTUDIO_STEMS_CACHE_ROOT':storage/'stems',
      'EZSTUDIO_OBSERVABILITY_ROOT':logs/'observability',
      'EZSTUDIO_EXPORT_ROOT':storage/'exports','EZSTUDIO_JOB_ROOT':temporary/'jobs',
    }
    for k,v in mapping.items():env[k]=str(v)
    env['KEEP_UPLOADS']='1'
    return env

def preflight():
    require((Path('H:/temp')).is_dir(),'H_TEMP_MISSING')
    profile_python=configuration()
    check_processes()
    rows=status()
    for gid,lid,state in rows: print(f'JOB_GLOBAL_{gid}_LAB_{lid}={state}')
    print('EZS_RECOVERY_4_3A17_PREFLIGHT_OK NO_DB_WRITE NO_JOB_CREATED NO_WORKER_STARTED')
    return profile_python

def tests():
    preflight()
    for root in (ORCH,LAB):
        steps=[['php','bin/console','lint:container'],['php','bin/console','lint:twig','templates'],
               ['php','vendor/bin/phpunit','--no-progress']]
        for args in steps:
            print('TEST_START',root.name,args[1],flush=True)
            r=subprocess.run(args,cwd=root)
            require(r.returncode==0,'TEST_FAILED_'+root.name+'_'+args[1])
    print('EZS_RECOVERY_4_3A17_TESTS_OK')

def run():
    # If any job fails, stop. NO retry / no other job executed / no separate scientific scheduler.
    tests()
    profile_python=preflight()
    env=environment(profile_python)
    for global_id,lab_id,state in status():
        if state=='completed':
            print('ALREADY_COMPLETED',global_id,flush=True)
            continue
        preflight()  # Re-check concurrency and active head immediately before claim.
        print('MESSENGER_START_GLOBAL',global_id,'LAB',lab_id,flush=True)
        r=subprocess.run(['php','bin/console','messenger:consume','global_queue','--limit=1','--no-interaction','-vv'],
                         cwd=ORCH,env=env)
        require(r.returncode==0,'MESSENGER_ERROR_RC_'+str(r.returncode))
        new=status() # Both global and LAB must confirm completion.
        state_after=next(x[2] for x in new if x[0]==global_id)
        require(state_after=='completed','JOB_NOT_COMPLETED_'+str(global_id)+'_DO_NOT_RETRY')
        print('GLOBAL_AND_LAB_COMPLETED',global_id,lab_id,flush=True)
    print('EZS_EXISTING_JOBS_204_205_COMPLETED_OK')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['preflight','tests','run'])
    args=p.parse_args()
    try:
        {'preflight':preflight,'tests':tests,'run':run}[args.action]()
    except (Refusal,OSError,sqlite3.Error,subprocess.TimeoutExpired) as e:
        reason=str(e) if isinstance(e,Refusal) else type(e).__name__
        print('EZS_RECOVERY_4_3A17_REFUSED:'+reason,file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':sys.exit(main())
