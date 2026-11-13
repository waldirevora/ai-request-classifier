import os,hashlib,json
from pathlib import Path
from uuid import uuid4
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from fastapi.testclient import TestClient
from app.cloud import create_public_app
from app.deployment import PublicSettings,client_network
from app.database import conectar
from app.bootstrap import seed
from app.retention import cleanup
from app import ia
from test_portals_v2 import portal,create
from test_lab_v2 import start

ORIGIN='https://solicitaflow-test.onrender.com'

@pytest.fixture
def public(portal,monkeypatch,tmp_path):
    monkeypatch.setenv('SF_ENV','production')
    monkeypatch.setenv('SF_CLEANUP_USER',os.environ['PGUSER'])
    monkeypatch.setenv('SF_CLEANUP_PASSWORD',os.environ['PGPASSWORD'])
    (tmp_path/'index.html').write_text('<html lang="pt-BR"><h1>SolicitaFlow</h1></html>')
    (tmp_path/'theme-init.js').write_text('//fixture')
    settings=PublicSettings(ORIGIN,False,'M'*40,tmp_path,require_tls=False)
    client=TestClient(create_public_app(settings),base_url=ORIGIN,headers={'Origin':ORIGIN,'X-SolicitaFlow-Context':'lab','Content-Type':'application/json'},client=('203.0.113.9',1234))
    return client,settings


def test_https_session_cookie_and_role_switch(public):
    client,_=public
    response=client.post('/api/v2/lab/start');assert response.status_code==201,response.text
    cookie=response.headers['set-cookie']
    assert cookie.startswith('__Host-sf_lab=') and 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=strict' in cookie and 'Path=/' in cookie and 'Domain=' not in cookie
    assert client.get('/api/v2/session').json()['kind']=='lab'
    switched=client.post('/api/v2/lab/switch',json={'username':'central'})
    assert switched.status_code==200 and switched.json()['role']=='central'
    assert client.post('/api/v2/logout').status_code==204
    assert client.get('/api/v2/session').status_code==401


def test_public_admin_docs_and_cross_site_requests_are_blocked(public):
    client,_=public
    for path in ('/docs','/openapi.json','/api/docs','/api/openapi.json','/api/v2/login','/api/solicitacoes'):
        assert client.get(path).status_code==404,path
    for origin in ('','https://evil.example','null',ORIGIN+'.evil'):
        assert client.post('/api/v2/lab/start',headers={'Origin':origin}).status_code==403
    assert client.post('/api/v2/lab/start',headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
    assert client.post('/api/v2/lab/start',headers={'X-SolicitaFlow-Context':'local'}).status_code==403
    assert client.get('/api/v2/presentation',headers={'Host':'evil.example'}).status_code==400
    assert client.get('/api/v2/presentation').json()['public_demo'] is True


def test_production_frontend_and_headers(public):
    client,_=public
    response=client.get('/')
    assert response.status_code==200 and 'data-public-demo="true"' in response.text
    assert response.headers['strict-transport-security']=='max-age=31536000'
    assert response.headers['x-frame-options']=='DENY'
    assert "script-src 'self'" in response.headers['content-security-policy']
    assert 'unsafe-eval' not in response.headers['content-security-policy']
    assert client.get('/.env').status_code==404
    assert client.get('/theme-init.js').status_code==200
    assert client.post('/api/v2/lab/start',content=b'x'*32769).status_code==413
    assert client.post('/api/v2/lab/start',headers={'Content-Type':'text/plain'}).status_code==415


def test_maintenance_is_closed_and_operator_does_not_gain_admin_access(public):
    _,settings=public
    from dataclasses import replace
    settings=replace(settings,maintenance=True)
    client=TestClient(create_public_app(settings),base_url=ORIGIN,headers={'Origin':ORIGIN,'Content-Type':'application/json','X-SolicitaFlow-Context':'lab'})
    assert client.get('/').status_code==503
    assert client.post('/api/v2/lab/start').status_code==503
    assert client.get('/health').status_code==200
    assert client.get('/',headers={'Authorization':'Bearer '+'M'*40}).status_code==200
    assert client.get('/api/v2/login',headers={'Authorization':'Bearer '+'M'*40}).status_code==404
    assert client.get('/',headers={'Authorization':'Bearer invalid'}).status_code==503


def test_liveness_does_not_wake_database_and_readiness_hides_failures(public,monkeypatch):
    client,_=public
    def down(**kwargs):raise RuntimeError('PRIVATE_CONNECTION_DETAILS')
    monkeypatch.setattr('app.database.conectar',down)
    assert client.get('/health').status_code==200
    assert client.get('/ready').status_code==404
    response=client.get('/ready',headers={'Authorization':'Bearer '+'M'*40});assert response.status_code==503 and 'PRIVATE' not in response.text
    response=client.get('/api/v2/cases');assert response.status_code==503 and 'PRIVATE' not in response.text


def test_network_headers_require_explicit_transport_trust():
    from ipaddress import ip_network
    scope={'client':('203.0.113.10',4000),'headers':[(b'x-forwarded-for',b'1.1.1.1'),(b'cf-connecting-ip',b'8.8.8.8')]}
    settings=PublicSettings(ORIGIN)
    assert client_network(scope,settings)=='203.0.113.0/24'
    from dataclasses import replace
    trusted=replace(settings,proxy_networks=(ip_network('10.0.0.0/8'),))
    assert client_network(scope,trusted)=='203.0.113.0/24'
    scope['client']=('10.0.0.2',9000)
    assert client_network(scope,trusted)=='8.8.8.0/24'
    scope['headers']=[(b'cf-connecting-ip',b'8.8.8.8,1.1.1.1')]
    assert client_network(scope,trusted)=='10.0.0.0/24'


def test_global_creation_cap_is_not_ip_identity(public,monkeypatch):
    client,_=public;monkeypatch.setenv('SF_LAB_DAILY_MAX','1')
    assert client.post('/api/v2/lab/start').status_code==201
    # Valid sessions still resume without consuming creation quotas.
    assert client.post('/api/v2/lab/start').status_code==200
    client.cookies.clear()
    denied=client.post('/api/v2/lab/start',headers={'X-Forwarded-For':'8.8.8.8'})
    assert denied.status_code==429 and denied.headers['Retry-After']


def add_case(conn,workspace):
    requester=conn.execute("SELECT id FROM sf_accounts WHERE workspace_id=%s AND role='colaborador'",(workspace,)).fetchone()['id']
    rid=conn.execute("INSERT INTO solicitacoes(titulo,descricao,justificativa_ia,observacao_revisao) VALUES('Pedido fictício de teste','Texto inventado que deve ser eliminado após expiração.','Justificativa fictícia removível','Observação removível') RETURNING id").fetchone()['id']
    case=uuid4();conn.execute("INSERT INTO sf_cases(id,workspace_id,request_id,client_key,source,requester_id,state,analysis_status,resolution) VALUES(%s,%s,%s,%s,'deepseek',%s,'excecao','failed','Texto removível')",(case,workspace,rid,uuid4(),requester))
    conn.execute("INSERT INTO sf_events(workspace_id,case_id,type,payload) VALUES(%s,%s,'andamento',%s)",(workspace,case,json.dumps({'message':'Texto removível'})))
    return case,rid


def test_retention_redacts_expired_and_only_purges_old_fictitious_workspace(portal):
    _,local,_=portal
    with conectar() as conn:
        active,_=seed(conn,'lab','Ativo fictício',datetime.now(timezone.utc)+timedelta(hours=24))
        expired,_=seed(conn,'lab','Expirado fictício',datetime.now(timezone.utc)-timedelta(hours=1))
        old,_=seed(conn,'lab','Antigo fictício',datetime.now(timezone.utc)-timedelta(days=34))
        active_case,active_id=add_case(conn,active);_,expired_id=add_case(conn,expired);_,old_id=add_case(conn,old)
        result=cleanup(conn)
        assert result=={'redacted':2,'purged':1}
        assert conn.execute('SELECT titulo FROM solicitacoes WHERE id=%s',(expired_id,)).fetchone()['titulo']=='Solicitação expirada'
        assert conn.execute('SELECT 1 FROM solicitacoes WHERE id=%s',(old_id,)).fetchone() is None
        assert conn.execute('SELECT titulo FROM solicitacoes WHERE id=%s',(active_id,)).fetchone()['titulo']=='Pedido fictício de teste'
        assert conn.execute('SELECT count(*) n FROM sf_workspaces WHERE id=ANY(%s)',([local,active,expired],)).fetchone()['n']==3
        assert conn.execute('SELECT count(*) n FROM sf_events WHERE workspace_id=%s',(expired,)).fetchone()['n']==0


def test_loss_of_session_lock_does_not_allow_a_second_paid_attempt(portal,monkeypatch):
    client,_=start();entered=Event();release=Event();original=ia.classificar_solicitacao;calls=[]
    def slow(*args):
        calls.append(1);entered.set();assert release.wait(10)
        return original(*args)
    monkeypatch.setattr(ia,'classificar_solicitacao',slow)
    def first():
        independent=TestClient(__import__('app.main',fromlist=['app']).app,headers={'X-SolicitaFlow-Context':'lab'},cookies=dict(client.cookies))
        return create(independent)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(first);assert entered.wait(5)
        try:
            with conectar() as conn:
                locks=conn.execute("SELECT a.pid FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid WHERE l.locktype='advisory' AND l.classid=826160 AND l.objsubid=2 AND a.datname=current_database() AND a.usename=current_user").fetchall()
                assert len(locks)==1
                assert conn.execute('SELECT pg_terminate_backend(%s) AS ok',(locks[0]['pid'],)).fetchone()['ok']
            denied=create(client).json()
            assert denied['analysis_code']=='capacidade_ocupada' and len(calls)==1
        finally:release.set()
        assert future.result().json()['analysis_status']=='succeeded'


def test_worker_interruption_is_reconciled_without_retry(portal,monkeypatch):
    client,who=start();key=str(uuid4())
    with conectar() as conn:
        case,rid=add_case(conn,who['workspace_id']);record={'id':str(case),'workspace_id':who['workspace_id']}
        conn.execute("UPDATE sf_cases SET state='analisando',analysis_status='running',client_key=%s WHERE id=%s",(key,case))
        conn.execute("INSERT INTO sf_ai_attempts(request_id,workspace_id,case_id,day,status,reserved_tokens,reserved_usd) VALUES(%s,%s,%s,(now() AT TIME ZONE 'UTC')::date,'reserved',1000,0.001)",(rid,who['workspace_id'],case))
        conn.execute("UPDATE sf_events SET created_at=now()-interval '6 minutes' WHERE case_id=%s",(record['id'],))
        conn.execute("UPDATE sf_ai_attempts SET status='reserved',created_at=now()-interval '6 minutes' WHERE case_id=%s",(record['id'],))
        from app.workflow import evaluate
        evaluate(conn,record['workspace_id'])
    def forbidden(*args):raise AssertionError('No retry allowed')
    monkeypatch.setattr(ia,'classificar_solicitacao',forbidden)
    result=client.get('/v2/cases/'+record['id']).json()
    assert result['analysis_code']=='processamento_interrompido'
    assert create(client).json()['analysis_code']=='consumo_pendente'
    with conectar() as conn:assert conn.execute('SELECT count(*) n FROM sf_ai_attempts').fetchone()['n']==1


def test_public_configuration_fails_closed(monkeypatch):
    from decimal import Decimal
    from app.ai_control import Policy
    monkeypatch.setenv('SF_ENV','production');monkeypatch.setenv('RENDER_EXTERNAL_URL',ORIGIN)
    for key,value in {'SF_MAINTENANCE_TOKEN':'M'*40,'PGHOST':'ep-test.us-east-1.aws.neon.tech','PGDATABASE':'solicitaflow_demo','PGUSER':'ai_classifier_app','PGSSLMODE':'verify-full','PGSSLROOTCERT':'system','SF_SECURE_LEGACY':'true','SF_QA_MODE':'false','SF_CLEANUP_USER':'ai_classifier_cleanup','SF_CLEANUP_PASSWORD':'test-only','SF_AI_WORKSPACE_CALLS':'2','SF_AI_DAILY_CALLS':'10','SF_AI_DAILY_USD':'0.05','SF_AI_CONCURRENT':'1'}.items():monkeypatch.setenv(key,value)
    assert PublicSettings.from_env().maintenance
    for key,bad in [('PGHOST','ep-test-pooler.us-east-1.aws.neon.tech'),('PGUSER','postgres'),('PGSSLMODE','require'),('SF_QA_MODE','true'),('SF_TRUSTED_PROXY_CIDRS','0.0.0.0/0'),('SF_AI_CONCURRENT','2'),('SF_AI_DAILY_USD','0.06')]:
        with monkeypatch.context() as m:
            m.setenv(key,bad)
            with pytest.raises(ValueError):PublicSettings.from_env()


def test_cleanup_keeps_current_budget_and_unknown_consumption(portal):
    with conectar() as conn:
        old,_=seed(conn,'lab','Antigo protegido',datetime.now(timezone.utc)-timedelta(days=35))
        case,rid=add_case(conn,old)
        conn.execute("INSERT INTO sf_ai_attempts(request_id,workspace_id,case_id,day,status,reserved_tokens,reserved_usd,created_at) VALUES(%s,%s,%s,(now() AT TIME ZONE 'UTC')::date-35,'reserved',1000,0.001,now()-interval '35 days')",(rid,old,case))
        marker=hashlib.sha256(b'public-lab-daily').hexdigest()
        conn.execute("INSERT INTO sf_rate_windows(key,bucket,count) VALUES(%s,floor(extract(epoch FROM now())/86400)::bigint*24,25)",(marker,))
        assert cleanup(conn)['purged']==0
        assert conn.execute('SELECT count(*) n FROM sf_ai_attempts WHERE workspace_id=%s',(old,)).fetchone()['n']==1
        assert conn.execute('SELECT count FROM sf_rate_windows WHERE key=%s',(marker,)).fetchone()['count']==25


def test_readiness_uses_client_tls_at_neon_proxy_boundary(monkeypatch):
    from types import SimpleNamespace
    from app.cloud import readiness
    root=Path(__file__).resolve().parents[1]
    checks=[{'version':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in (root/'sql').glob('00[1-7]_*.sql')]
    class Connection:
        pgconn=SimpleNamespace(ssl_in_use=True)
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def execute(self,query):
            if 'current_user AS role' in query:return SimpleNamespace(fetchone=lambda:{'role':'ai_classifier_app','version':18})
            if 'FROM sf_schema_versions' in query:return SimpleNamespace(fetchall=lambda:checks)
            if 'information_schema.columns' in query:return SimpleNamespace(fetchone=lambda:{'n':22})
            if 'has_table_privilege' in query:return SimpleNamespace(fetchone=lambda:{'bad':False})
            raise AssertionError('Unexpected SQL')
    conn=Connection();monkeypatch.setattr('app.database.conectar',lambda:conn)
    assert readiness(PublicSettings(ORIGIN)).status_code==200
    conn.pgconn.ssl_in_use=False
    assert readiness(PublicSettings(ORIGIN)).status_code==503


def test_endpoint_failure_returns_safe_json_and_no_implementation_details(public,monkeypatch):
    client,_=public
    def down(*args,**kwargs):raise RuntimeError('PRIVATE_ERROR_DETAILS')
    monkeypatch.setattr('app.laboratory.seed',down)
    response=client.post('/api/v2/lab/start',json={})
    assert response.status_code==503 and response.headers['content-type']=='application/json'
    assert 'PRIVATE' not in response.text and 'reenviar' in response.json()['detail']
