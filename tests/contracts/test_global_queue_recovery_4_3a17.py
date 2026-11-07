import importlib.util
import json
import sqlite3
import tempfile
from pathlib import Path
import sys
src=Path(__file__).resolve().parents[2]
assert (src/'scripts/global_queue_recovery_4_3a17.py').exists()
spec=importlib.util.spec_from_file_location('runner',src/'scripts/global_queue_recovery_4_3a17.py')
r=importlib.util.module_from_spec(spec);sys.modules['runner']=r;spec.loader.exec_module(r)
with tempfile.TemporaryDirectory() as t:
 root=Path(t);g=root/'global.sqlite';l=root/'benchmark.sqlite'
 q=sqlite3.connect(g);q.executescript('''CREATE TABLE global_queue_jobs(id INTEGER,producer TEXT,external_id TEXT,kind TEXT,state TEXT,claim_generation INTEGER,created_at INTEGER);''')
 for id,lab in [(3,193),(9,204),(10,205)]:
  q.execute('INSERT INTO global_queue_jobs VALUES(?,?,?,?,?,?,?)',(id,'lab',f'analysis_job:{lab}','profile','queued',0,id))
 q.commit();q.close()
 d=sqlite3.connect(l);d.executescript('''CREATE TABLE analysis_jobs(id INTEGER,kind TEXT,status TEXT,dispatch_owner TEXT,scientific_run_id INTEGER);CREATE TABLE global_queue_admission_outbox(job_id INTEGER,state TEXT,global_job_id INTEGER);CREATE TABLE scientific_runs(id INTEGER,state TEXT);''')
 for gid,jid in [(9,204),(10,205)]:
  d.execute('INSERT INTO analysis_jobs VALUES(?,?,?,?,?)',(jid,'profile','queued','orchestrator',jid-25))
  d.execute('INSERT INTO global_queue_admission_outbox VALUES(?,?,?)',(jid,'admitted',gid))
  d.execute('INSERT INTO scientific_runs VALUES(?,?)',(jid-25,'queued'))
 d.commit();d.close();r.GLOBAL=g;r.LOCAL=l
 assert r.status()==[(9,204,'queued'),(10,205,'queued')]
 q=sqlite3.connect(g);q.execute("UPDATE global_queue_jobs SET state='completed' WHERE id=9");q.commit();q.close()
 d=sqlite3.connect(l);d.execute("UPDATE analysis_jobs SET status='completed' WHERE id=204");d.execute("UPDATE scientific_runs SET state='done' WHERE id=179");d.commit();d.close()
 assert r.status()==[(9,204,'completed'),(10,205,'queued')]
 q=sqlite3.connect(g);q.execute("UPDATE global_queue_jobs SET state='failed' WHERE id=10");q.commit();q.close()
 try:r.status()
 except r.Refusal as e:assert 'JOB_NOT_RECOVERABLE_10' in str(e)
 else:raise AssertionError('failed job must refuse')
print('RUNNER_SQLITE_SYNTHETIC_OK: strict FIFO, historic job untouched, completed, fail-closed')
handler=(src/'src/Module/Coordination/Messenger/GlobalQueueJobHandler.php').read_text(encoding='utf8')
assert 'LAB_GLOBAL_PROFILE_EXECUTION_FAILED' in handler
assert '$process->disableOutput()' not in handler
assert "env['EZS_QUEUE_RECOVERY_ONLY']='9,10'" in (src/'scripts/global_queue_recovery_4_3a17.py').read_text()
assert "getenv('EZS_QUEUE_RECOVERY_ONLY')" in (src/'src/Module/Coordination/Messenger/GlobalQueueReceiver.php').read_text()
print('PATCH_ASSERTIONS_OK')
