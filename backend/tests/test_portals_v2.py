import sys
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import conectar
from app.identity import password_hash
from conftest import clean_test_database
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from seed_local import seed

@pytest.fixture
def portal(monkeypatch):
    monkeypatch.setenv('PGDATABASE','ai_request_classifier_test')
    monkeypatch.setenv('SF_SECURE_LEGACY','true')
    with conectar() as conn:
        clean_test_database(conn)
        workspace,accounts=seed(conn)
        # Deterministic test password is never used by local operational accounts.
        conn.execute('UPDATE sf_accounts SET password_hash=%s',(password_hash('test-password-only'),))
    return TestClient(app),workspace,accounts

def login(client,name):
    response=client.post('/v2/login',json={'username':name,'password':'test-password-only'})
    assert response.status_code==200,response.text
    return response.json()

def create(client,title='Servidor parado',description='A equipe está impedida de trabalhar porque o servidor está parado desde o início do expediente.',**extra):
    return client.post('/v2/cases',json={'titulo':title,'descricao':description,'client_key':str(uuid4()),**extra})

def test_authentication_and_idempotency(portal):
    client,_,_=portal
    assert client.get('/v2/cases').status_code==401
    assert client.get('/solicitacoes').status_code==401
    login(client,'colaborador')
    assert client.get('/solicitacoes').status_code==403
    key=str(uuid4())
    first=create(client,client_key=key);second=create(client,client_key=key)
    assert first.status_code==201,first.text
    assert first.json()['id']==second.json()['id']
    assert first.json()['state']=='encaminhada'
    assert len(client.get('/v2/cases').json())==1
    assert client.post('/v2/departments',json={'name':'Inválido'}).status_code==403
    assert create(client,mode='deepseek').status_code==403

def test_resource_authorization(portal):
    client,workspace,accounts=portal
    login(client,'colaborador');case=create(client).json()
    login(client,'financeiro')
    assert client.get('/v2/cases').json()==[]
    assert client.get('/v2/cases/'+case['id']).status_code==404
    login(client,'suporte_ti')
    assert len(client.get('/v2/cases').json())==1
    assert client.get('/v2/cases/'+case['id']).status_code==200
    login(client,'central')
    assert client.get('/solicitacoes/'+str(case['request_id'])).status_code==404
    assert client.get('/solicitacoes').json()==[]
    # A valid local token cannot be reused as a lab capability.
    assert client.get('/v2/cases',headers={'X-SolicitaFlow-Context':'lab'}).status_code==401

def test_exception_requires_human_and_preserves_suggestion(portal):
    client,_,_=portal
    login(client,'colaborador')
    case=create(client,description='A equipe relata problema no servidor e também uma fatura incorreta para pagamento.').json()
    assert case['state']=='excecao'
    login(client,'central')
    departments=client.get('/v2/departments').json();department=next(d['id'] for d in departments if d['name']=='Tecnologia')
    payload={'category':'suporte_ti','department_id':department,'impact':'equipe','urgency':'media','reason':'Após esclarecimento, trata-se do servidor da equipe.'}
    result=client.post('/v2/cases/'+case['id']+'/review',json=payload)
    assert result.status_code==200,result.text
    assert result.json()['request']['categoria_sugerida']=='outros'
    assert result.json()['request']['categoria_final']=='suporte_ti'
    assert client.post('/v2/cases/'+case['id']+'/review',json=payload).status_code==409

def test_origin_and_logout(portal):
    client,_,_=portal
    assert client.post('/v2/login',json={'username':'central','password':'test-password-only'},headers={'Origin':'https://example.com'}).status_code==403
    login(client,'central')
    assert client.post('/v2/logout').status_code==204
    assert client.get('/v2/session').status_code==401

def test_provider_failure_keeps_request_and_daily_budget(portal,monkeypatch):
    from app import portals
    from app.ia import ErroClassificacao
    client,_,_=portal
    monkeypatch.setenv('SF_REAL_AI_ENABLED','true')
    monkeypatch.setenv('AI_ENABLED','true')
    calls=[]
    def fail(*args):
        calls.append(args)
        raise ErroClassificacao('http_429')
    monkeypatch.setattr(portals,'classificar_solicitacao',fail)
    login(client,'colaborador')
    for _ in range(2):
        response=create(client,mode='deepseek')
        assert response.status_code==201,response.text
        assert response.json()['state']=='excecao'
        assert response.json()['request']['titulo']=='Servidor parado'
    assert create(client,mode='deepseek').status_code==429
    assert len(calls)==2
    assert len(client.get('/v2/cases').json())==2

def test_map_rejects_unknown_or_foreign_destination(portal):
    client,_,_=portal
    login(client,'central')
    assert client.put('/v2/routes',json={'category':'suporte_ti','department_id':str(uuid4())}).status_code==422
