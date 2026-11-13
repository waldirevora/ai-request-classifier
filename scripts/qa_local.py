"""Local QA only: resets the isolated test DB; never uses real provider credentials."""
from pathlib import Path
import os,sys,json,subprocess,time,urllib.request
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'scripts'))
from local_services import environment
out=Path.home()/'.local/share/ai-request-classifier/solicitaflow-v2-6';out.mkdir(mode=0o700,exist_ok=True)
env=environment(True)
env.update(AI_ENABLED='true',SF_REAL_AI_ENABLED='true',SF_QA_MODE='true',SF_QA_PORT='18000',AI_MODEL='deepseek-flash',SF_AI_DAILY_CALLS='1000',SF_AI_WORKSPACE_CALLS='2',SF_AI_HOURLY_IP_CALLS='1000',SF_AI_DAILY_TOKENS='10000000',SF_AI_DAILY_USD='10')
if len(sys.argv)>1 and sys.argv[1]=='stop':
    import signal
    for name,marker,cwd in [('qa-backend','browser_backend.py',r),('qa-frontend','vite',r/'frontend')]:
        file=out/(name+'.pid')
        if not file.exists():continue
        pid=int(file.read_text());proc=Path('/proc')/str(pid)
        if proc.exists() and (proc/'cwd').resolve()==cwd and marker in (proc/'cmdline').read_bytes().decode():
            os.kill(pid,signal.SIGTERM);print(name,'stopped',pid)
    time.sleep(.3)
elif len(sys.argv)>1 and sys.argv[1]=='start':
    for name in ('qa-backend','qa-frontend'):
        pidfile=out/(name+'.pid')
        if pidfile.exists() and (Path('/proc')/pidfile.read_text().strip()).exists():
            raise SystemExit('QA já está ativo; execute stop antes de iniciar outra regressão.')
    # Only the isolated test DB can be reset for the local browser regression.
    code="""import sys,json,os
from pathlib import Path
sys.path.insert(0,'backend');sys.path.insert(0,'backend/tests')
from conftest import clean_test_database
from app.database import conectar
from app.bootstrap import seed
with conectar() as conn:
 clean_test_database(conn);w,accounts=seed(conn)
 file=Path.home()/'.local/share/ai-request-classifier/solicitaflow-v2-6/qa-accounts.json'
 fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600);os.fchmod(fd,0o600)
 with os.fdopen(fd,'w') as stream:json.dump({'accounts':accounts},stream)
"""
    subprocess.run([str(r/'backend/.venv/bin/python'),'-c',code],cwd=r,env=env,check=True)
    front={k:v for k,v in env.items() if not k.startswith(('PG','DEEPSEEK','AI_','SF_'))}
    front['SF_BACKEND_TARGET']='http://127.0.0.1:18000'
    for name,args,cwd,process_env in [('qa-backend',[str(r/'backend/.venv/bin/python'),str(r/'scripts/browser_backend.py')],r,env),('qa-frontend',[str(Path.home()/'.local/opt/ai-request-classifier/node/bin/node'),str(r/'frontend/node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port','5174','--strictPort'],r/'frontend',front)]:
        with (out/(name+'.log')).open('ab') as stream:p=subprocess.Popen(args,cwd=cwd,env=process_env,stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        (out/(name+'.pid')).write_text(str(p.pid));print(name,p.pid)
    for _ in range(30):
        try:
            with urllib.request.urlopen('http://127.0.0.1:5174/api/health') as response:assert response.status==200
            break
        except Exception:time.sleep(.3)
    else:raise SystemExit('QA não ficou disponível; consulte qa-backend.log e qa-frontend.log.')
elif len(sys.argv)>1 and sys.argv[1]=='browser':
    env['SF_BROWSER_BASE_URL']='http://127.0.0.1:5174'
    subprocess.run([str(Path.home()/'.local/share/ai-request-classifier/browser-venv/bin/python'),str(r/'scripts/browser_lab.py'),'--output',str(out/'qa-captures'),'--axe',str(Path.home()/'.local/share/ai-request-classifier/ux-redesign/tools/node_modules/axe-core/axe.min.js'),'--accounts',str(out/'qa-accounts.json')],cwd=r,env=env,check=True)
