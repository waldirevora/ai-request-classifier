"""Opaque, hashed sessions. Laboratory capabilities cannot authenticate locally."""
import hashlib, hmac, os, secrets
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from fastapi import HTTPException, Request, Response
from app.database import conectar

def password_hash(password):
    salt=secrets.token_hex(16)
    return salt+':'+hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()

def password_matches(password, encoded):
    if not encoded: return False
    salt,digest=encoded.split(':',1)
    actual=hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()
    return hmac.compare_digest(actual,digest)

def context(request):
    value=request.headers.get('X-SolicitaFlow-Context','local')
    if value not in ('local','lab'): raise HTTPException(400,'Contexto inválido')
    return value

def rate_limit(conn,key,limit=30):
    digest=hashlib.sha256(key.encode()).hexdigest()
    bucket=int(datetime.now(timezone.utc).timestamp())//3600
    count=conn.execute('''INSERT INTO sf_rate_windows(key,bucket) VALUES(%s,%s)
        ON CONFLICT(key,bucket) DO UPDATE SET count=sf_rate_windows.count+1 RETURNING count''',(digest,bucket)).fetchone()['count']
    # Commit failed-attempt counters too; callers use a separate transaction for authentication.
    if count>limit: return False
    return True

def issue_session(conn,account,response,kind):
    token=secrets.token_urlsafe(32)
    conn.execute('INSERT INTO sf_sessions(token_hash,workspace_id,account_id,expires_at) VALUES(%s,%s,%s,%s)',
        (hashlib.sha256(token.encode()).hexdigest(),account['workspace_id'],account['id'],datetime.now(timezone.utc)+timedelta(hours=2 if kind=='lab' else 8)))
    response.set_cookie('sf_'+kind,token,httponly=True,samesite='strict',secure=False,max_age=7200 if kind=='lab' else 28800,path='/')

def actor(request: Request):
    kind=context(request)
    token=request.cookies.get('sf_'+kind,'')
    if len(token)<30 or len(token)>100: raise HTTPException(401,'Entre para continuar')
    with conectar() as conn:
        who=conn.execute('''SELECT a.*,w.kind,w.expires_at AS workspace_expires FROM sf_sessions s
            JOIN sf_accounts a ON (a.workspace_id,a.id)=(s.workspace_id,s.account_id)
            JOIN sf_workspaces w ON w.id=a.workspace_id
            WHERE s.token_hash=%s AND s.expires_at>now() AND w.kind=%s AND (w.expires_at IS NULL OR w.expires_at>now())''',
            (hashlib.sha256(token.encode()).hexdigest(),kind)).fetchone()
    if not who: raise HTTPException(401,'Sessão expirada. Entre novamente.')
    return who

def require(who,*roles):
    if who['role'] not in roles: raise HTTPException(403,'Seu perfil não autoriza esta operação')

def visible_case(conn,who,case_id,lock=False):
    case=conn.execute('SELECT * FROM sf_cases WHERE id=%s AND workspace_id=%s'+(' FOR UPDATE' if lock else ''),
                     (case_id,who['workspace_id'])).fetchone()
    if not case or (who['role']=='colaborador' and case['requester_id']!=who['id']) or (who['role']=='departamento' and case['department_id']!=who['department_id']):
        raise HTTPException(404,'Solicitação não encontrada')
    return case

def public_actor(who):
    return {k:who[k] for k in ('id','workspace_id','username','display_name','role','department_id','kind')}

def legacy_guard(request: Request):
    if os.getenv('SF_SECURE_LEGACY','true').lower()=='false': return
    who=actor(request)
    require(who,'central')
    if who['kind']!='local': raise HTTPException(403,'A triagem clássica exige uma conta local')
    tail=request.url.path.rsplit('/',1)[-1]
    if tail.isdigit():
        with conectar() as conn:
            if conn.execute('SELECT 1 FROM sf_cases WHERE request_id=%s',(int(tail),)).fetchone():
                raise HTTPException(404,'Use os portais para consultar esta solicitação')

def classic_filter():
    return " AND id NOT IN (SELECT request_id FROM sf_cases)" if os.getenv('SF_SECURE_LEGACY','true').lower()!='false' else ''
