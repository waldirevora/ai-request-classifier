"""Create fictional local accounts once. Passwords go only to a private local file."""
import sys,json,secrets,os
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.identity import password_hash
from app.database import conectar

DEPARTMENTS={'suporte_ti':'Tecnologia','acessos_permissoes':'Identidades e acessos','financeiro':'Financeiro','recursos_humanos':'Pessoas'}

def seed(conn,kind='local',name='Ambiente local',expires=None):
    workspace=uuid4()
    conn.execute('INSERT INTO sf_workspaces(id,name,kind,expires_at) VALUES(%s,%s,%s,%s)',(workspace,name,kind,expires))
    departments={}
    for cat,label in DEPARTMENTS.items():
        did=uuid4();departments[cat]=did
        conn.execute('INSERT INTO sf_departments(id,workspace_id,name) VALUES(%s,%s,%s)',(did,workspace,label))
        conn.execute('INSERT INTO sf_routes(workspace_id,category,department_id) VALUES(%s,%s,%s)',(workspace,cat,did))
    accounts=[]
    for username,role,did,label in [('colaborador','colaborador',None,'Ana · Colaboradora fictícia'),('central','central',None,'Marina · Central fictícia')]+[(cat,'departamento',did,DEPARTMENTS[cat]+' · Equipe fictícia') for cat,did in departments.items()]:
        password=secrets.token_urlsafe(20) if kind=='local' else None
        aid=uuid4()
        conn.execute('INSERT INTO sf_accounts(id,workspace_id,username,display_name,role,department_id,password_hash) VALUES(%s,%s,%s,%s,%s,%s,%s)',
            (aid,workspace,username,label,role,did,password_hash(password) if password else None))
        accounts.append({'id':str(aid),'username':username,'password':password,'role':role})
    return workspace,accounts

if __name__=='__main__':
    destination=Path.home()/'.local/share/ai-request-classifier/solicitaflow-v2/local-accounts.json'
    destination.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    with conectar() as conn:
        if conn.execute("SELECT 1 FROM sf_workspaces WHERE kind='local'").fetchone():raise SystemExit('Local workspace already exists; no credentials changed')
        if destination.exists():raise SystemExit('Credentials file exists; refusing to overwrite')
        workspace,accounts=seed(conn)
        fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:json.dump({'workspace':str(workspace),'accounts':accounts},stream,indent=2)
    print('Fictional accounts created; credentials stored privately at',destination)
