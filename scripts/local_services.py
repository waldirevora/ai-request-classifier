"""Local app processes only. Never installs, starts, stops or changes PostgreSQL."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,signal,subprocess,sys,time
from urllib.request import urlopen
from dotenv import dotenv_values
import psycopg

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=Path.home()/'.local/share/ai-request-classifier'
PYTHON=ROOT/'backend/.venv/bin/python'
LOCAL_NODE=Path.home()/'.local/opt/ai-request-classifier/node/bin/node'
NODE=str(LOCAL_NODE) if LOCAL_NODE.exists() else shutil.which('node')

def environment(test=False):
    values=dotenv_values(ROOT/'backend'/('.env.test' if test else '.env'))
    env={k:v for k,v in os.environ.items() if not k.startswith(('PG','AI_','DEEPSEEK','SF_'))}
    env.update({k:v for k,v in values.items() if v is not None})
    env.setdefault('AI_ENABLED','false');env.setdefault('SF_REAL_AI_ENABLED','false')
    env['SF_SECURE_LEGACY']='true'
    if test:env.update(AI_ENABLED='false',SF_REAL_AI_ENABLED='false',DEEPSEEK_API_KEY='OFFLINE_TESTS_NO_REAL_KEY')
    if NODE:env['PATH']=str(Path(NODE).parent)+os.pathsep+env.get('PATH','')
    return env

def connect(env):
    return psycopg.connect(**{k:env[v] for k,v in [('host','PGHOST'),('port','PGPORT'),('dbname','PGDATABASE'),('user','PGUSER'),('password','PGPASSWORD')]})

def preflight(env,test=False):
    expected='ai_request_classifier_test' if test else 'ai_request_classifier'
    role='ai_classifier_test' if test else 'ai_classifier_app'
    assert env.get('PGDATABASE')==expected and env.get('PGUSER')==role
    assert env.get('PGHOST') in ('localhost','127.0.0.1') and env.get('PGPORT')=='5432'
    with connect(env) as conn:
        row=conn.execute("SELECT current_database(),current_user,inet_server_port(),current_setting('server_version_num')::int/10000,has_table_privilege(current_user,'solicitacoes','TRUNCATE')").fetchone()
        assert row==(expected,role,5432,18,test),'Unexpected database identity or permissions'
        if test:assert not conn.execute("SELECT has_database_privilege(current_user,'ai_request_classifier','CONNECT')").fetchone()[0]

def pid(name):
    file=RUNTIME/(name+'.pid')
    if not file.exists():return None
    try:
        number=int(file.read_text().strip());proc=Path('/proc')/str(number)
        expected=ROOT/('backend' if name=='backend' else 'frontend' if name=='frontend' else '')
        marker={'backend':'uvicorn','frontend':'vite','sla':'check_sla.py'}[name]
        if (proc/'cwd').resolve()==expected and marker in (proc/'cmdline').read_bytes().decode(errors='replace'):return number
    except (OSError,ValueError):pass
    return None

def stop(names):
    for name in names:
        number=pid(name)
        if not number:continue
        os.kill(number,signal.SIGTERM)
        for _ in range(50):
            if not pid(name):break
            time.sleep(.1)
        if pid(name):raise RuntimeError('Process did not exit: '+name)
        print(name,'stopped',number)

def status():
    for name in ('backend','frontend','sla'):print(name,'PID',pid(name))
    for url in ('http://127.0.0.1:8000/health','http://127.0.0.1:8000/docs','http://127.0.0.1:5173/','http://127.0.0.1:5173/api/health'):
        try:
            with urlopen(url,timeout=3) as response:print(response.status,url)
        except Exception:print('unavailable',url)

def start():
    assert PYTHON.exists() and NODE,'Prepare Python venv and Node first'
    env=environment();preflight(env)
    RUNTIME.mkdir(mode=0o700,parents=True,exist_ok=True)
    frontend={k:v for k,v in env.items() if not k.startswith(('PG','AI_','DEEPSEEK','SF_')) and k!='DATABASE_URL'}
    specs={
        'backend':([str(PYTHON),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'],ROOT/'backend',env),
        'frontend':([NODE,str(ROOT/'frontend/node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port','5173'],ROOT/'frontend',frontend),
        'sla':([str(PYTHON),str(ROOT/'scripts/check_sla.py'),'--interval','60'],ROOT,dict(env,AI_ENABLED='false',SF_REAL_AI_ENABLED='false')),
    }
    for name,(cmd,cwd,process_env) in specs.items():
        if pid(name):continue
        log=RUNTIME/(name+'.log')
        fd=os.open(log,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        with os.fdopen(fd,'ab') as stream:
            process=subprocess.Popen(cmd,cwd=cwd,env=process_env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        (RUNTIME/(name+'.pid')).write_text(str(process.pid)+'\n')
        print(name,'started',process.pid)
    subprocess.run([str(PYTHON),str(ROOT/'scripts/wait_local.py')],check=True)
    status()

def test():
    env=environment(True);preflight(env,True)
    dev=environment();preflight(dev)
    def snapshot():
        with connect(dev) as conn:return hashlib.sha256(json.dumps(conn.execute('SELECT row_to_json(s)::text FROM solicitacoes s ORDER BY id').fetchall()).encode()).hexdigest()
    before=snapshot()
    result=subprocess.run([str(PYTHON),'-m','pytest','-q'],cwd=ROOT/'backend',env=env,capture_output=True,text=True)
    output=result.stdout+result.stderr
    for secret in (env.get('PGPASSWORD'),dev.get('PGPASSWORD'),dev.get('DEEPSEEK_API_KEY')):
        if secret:output=output.replace(secret,'[redacted]')
    print(output)
    assert before==snapshot(),'Main database changed during tests'
    print('Test database isolation and main snapshot verified')
    raise SystemExit(result.returncode)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['start','status','stop','restart-backend','test']);args=parser.parse_args()
    if args.action=='start':start()
    elif args.action=='status':status()
    elif args.action=='stop':stop(('sla','frontend','backend'))
    elif args.action=='restart-backend':stop(('backend',));start()
    else:test()
