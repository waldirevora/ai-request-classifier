from fastapi.testclient import TestClient
from app.main import app
from app.database import conectar
from app.identity import password_hash
from uuid import uuid4
from test_portals_v2 import portal,login,create

def test_legacy_numeric_spellings_cannot_bypass_portal_authorization(portal):
    client,_,_=portal
    login(client,'colaborador');case=create(client).json()
    login(client,'central')
    for spelling in (str(case['request_id']), '+'+str(case['request_id']), str(case['request_id'])+'.0'):
        # Pydantic accepts these as the same integer. All must be protected alike.
        assert client.get('/solicitacoes/'+spelling).status_code==404
        assert client.put('/solicitacoes/'+spelling,json={'titulo':'Alteração indevida','descricao':'Não deve alterar uma solicitação gerida pelos portais.'}).status_code==404

def test_colleague_cannot_read_or_change_another_request(portal):
    client,workspace,_=portal
    login(client,'colaborador');case=create(client).json()
    with conectar() as conn:
        conn.execute("INSERT INTO sf_accounts(id,workspace_id,username,display_name,role,password_hash) VALUES(%s,%s,'colega','Colega fictício','colaborador',%s)",(uuid4(),workspace,password_hash('test-password-only')))
    login(client,'colega')
    assert client.get('/v2/cases').json()==[]
    assert client.get('/v2/cases/'+case['id']).status_code==404
    assert client.post('/v2/cases/'+case['id']+'/transition',json={'action':'resolver','message':'Tentativa indevida de resolução.'}).status_code==403

def test_both_flags_are_required_before_real_classification(portal,monkeypatch):
    from app import portals
    client,_,_=portal
    monkeypatch.setenv('SF_REAL_AI_ENABLED','true')
    monkeypatch.setenv('AI_ENABLED','false')
    def forbidden(*_):raise AssertionError('Provider must not be invoked')
    monkeypatch.setattr(portals,'classificar_solicitacao',forbidden)
    login(client,'colaborador')
    assert create(client,mode='deepseek').status_code==403
