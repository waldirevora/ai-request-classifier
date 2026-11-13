from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.database import conectar
from app import ia
from app.ai_control import Policy, reservation
from test_portals_v2 import portal,login,create
from test_lab_v2 import start


def test_global_budget_spans_visitors_and_preserves_blocked_request(portal,monkeypatch):
    monkeypatch.setenv('SF_AI_DAILY_CALLS','1')
    one,_=start();two,_=start()
    assert create(one).json()['analysis_status']=='succeeded'
    denied=create(two)
    assert denied.status_code==201
    assert denied.json()['analysis_code']=='cota_global'
    assert denied.json()['state']=='excecao'
    assert denied.json()['request']['categoria_sugerida'] is None
    assert one.get('/v2/cases/'+denied.json()['id']).status_code==404


def test_dollar_and_token_limits_fail_closed_before_transport(portal,monkeypatch):
    client,_=start()
    def forbidden(*args):raise AssertionError('Transport must not run')
    monkeypatch.setattr(ia,'classificar_solicitacao',forbidden)
    for key,value in [('SF_AI_DAILY_USD','0.000001'),('SF_AI_DAILY_TOKENS','1')]:
        monkeypatch.setenv(key,value)
        result=create(client).json()
        assert result['analysis_code']=='orcamento_esgotado'
        assert result['request']['titulo']=='Servidor parado'
    with conectar() as conn:assert conn.execute('SELECT count(*) n FROM sf_ai_attempts').fetchone()['n']==0


def test_no_simulation_endpoint_and_idempotency_rejects_payload_change(portal):
    client,_=start();key=str(uuid4())
    assert create(client,mode='simulacao').status_code==422
    first=create(client,client_key=key).json()
    duplicate=create(client,client_key=key).json()
    assert duplicate['id']==first['id']
    assert create(client,title='Outra solicitação fictícia',client_key=key).status_code==409
    with conectar() as conn:assert conn.execute('SELECT count(*) n FROM sf_ai_attempts').fetchone()['n']==1


def test_concurrency_limit_rejects_without_charging_and_without_losing_request(portal,monkeypatch):
    client,who=start()
    entered=Event();release=Event();original=ia.classificar_solicitacao
    def slow(*args):
        entered.set();assert release.wait(5)
        return original(*args)
    monkeypatch.setattr(ia,'classificar_solicitacao',slow)
    def first():
        independent=TestClient(app,headers={'X-SolicitaFlow-Context':'lab'},cookies=dict(client.cookies))
        return create(independent)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(first)
        assert entered.wait(5)
        try:
            denied=create(client).json()
            assert denied['analysis_code']=='capacidade_ocupada'
            assert denied['state']=='excecao'
        finally:release.set()
        assert future.result().json()['analysis_status']=='succeeded'
    with conectar() as conn:assert conn.execute('SELECT count(*) n FROM sf_ai_attempts').fetchone()['n']==1


def test_async_creation_returns_persisted_stage_and_then_finishes(portal):
    client,_=start()
    result=client.post('/v2/cases',headers={'Prefer':'respond-async'},json={'titulo':'Servidor parado','descricao':'A equipe está impedida de trabalhar porque o servidor está parado neste expediente.','client_key':str(uuid4())})
    assert result.status_code==202
    assert result.json()['analysis_status']=='queued'
    final=client.get('/v2/cases/'+result.json()['id']).json()
    assert final['analysis_status']=='succeeded'
    assert final['state']=='encaminhada'
    assert {'cadastrada','ia_analisando','ia_concluida','roteamento_automatico'} <= {e['type'] for e in final['events']}


def test_failed_calls_keep_full_reservations_and_never_fabricate_suggestions(portal,monkeypatch):
    client,_=start()
    def unavailable(*args):raise ia.ErroClassificacao('http_429')
    monkeypatch.setattr(ia,'classificar_solicitacao',unavailable)
    result=create(client).json()
    assert result['analysis_status']=='failed' and result['analysis_code']=='http_429'
    assert result['request']['categoria_sugerida'] is None
    with conectar() as conn:
        attempt=conn.execute('SELECT * FROM sf_ai_attempts').fetchone()
        assert attempt['reserved_usd']>0 and attempt['reserved_tokens']>0
        assert attempt['status']=='failed'


def test_technical_legacy_form_uses_same_budget_and_idempotency(portal,monkeypatch):
    client,_,_=portal
    monkeypatch.setenv('SF_AI_DAILY_CALLS','1')
    login(client,'central')
    body={'titulo':'Servidor parado','descricao':'A equipe está impedida porque o servidor está parado desde o expediente.'}
    key=str(uuid4())
    one=client.post('/solicitacoes',json=body,headers={'Idempotency-Key':key})
    assert one.status_code==201,one.text
    same=client.post('/solicitacoes',json=body,headers={'Idempotency-Key':key})
    assert same.json()['id']==one.json()['id']
    assert client.delete('/solicitacoes/'+str(one.json()['id'])).status_code==409
    visitor,_=start()
    assert create(visitor).json()['analysis_code']=='cota_global'
    with conectar() as conn:assert conn.execute('SELECT count(*) n FROM sf_ai_attempts').fetchone()['n']==1


def test_invalid_policy_never_calls_provider(portal,monkeypatch):
    client,_=start()
    monkeypatch.setenv('SF_AI_DAILY_USD','NaN')
    assert create(client).json()['analysis_code']=='politica_invalida'


def test_provider_error_text_is_never_exposed(portal,monkeypatch):
    client,_=start()
    def unsafe(*args):raise ia.ErroClassificacao('PRIVATE_PROVIDER_TEXT')
    monkeypatch.setattr(ia,'classificar_solicitacao',unsafe)
    response=create(client)
    assert response.json()['analysis_code']=='falha_integracao'
    assert 'PRIVATE_PROVIDER_TEXT' not in response.text


def test_contact_only_comes_from_safe_explicit_configuration(portal,monkeypatch):
    client,_,_=portal
    for value in ('javascript:alert(1)','https://user:password@example.com','https://example.com/?token=private','mailto:a@example.com\nBcc:x@example.com','https://['):
        monkeypatch.setenv('SF_CONTACT_URL',value)
        assert client.get('/v2/presentation').json()['contact_url'] is None
    monkeypatch.setenv('SF_CONTACT_URL','https://example.com/contact')
    assert client.get('/v2/presentation').json()['contact_url']=='https://example.com/contact'
