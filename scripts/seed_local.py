"""Create fictional local accounts once. Passwords go only to a private local file."""
import sys,json,secrets,os
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.identity import password_hash
from app.database import conectar

from app.bootstrap import seed

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
