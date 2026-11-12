from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.database import conectar
from test_portals_v2 import portal,login,create

def start():
    client=TestClient(app,headers={'X-SolicitaFlow-Context':'lab'})
    response=client.post('/v2/lab/start')
    assert response.status_code==201,response.text
    return client,response.json()

def switch(client,name):
    response=client.post('/v2/lab/switch',json={'username':name})
    assert response.status_code==200,response.text
    return response.json()

def test_lab_complete_journey_and_visitor_isolation(portal):
    client,who=start();other,other_who=start()
    case=create(client).json();path='/v2/cases/'+case['id']
    assert case['state']=='encaminhada'
    assert other.get(path).status_code==404
    assert other.get('/v2/cases').json()==[]
    assert client.get('/solicitacoes').status_code==403
    assert create(client,mode='deepseek').status_code==403
    switch(client,'suporte_ti')
    assert client.post(path+'/transition',json={'action':'assumir','message':'Equipe fictícia iniciou a investigação.'}).status_code==200
    assert client.post('/v2/lab/advance',json={'hours':6}).status_code==200
    assert 'risco_sla' in {n['kind'] for n in client.get('/v2/notifications').json()}
    assert client.post('/v2/lab/advance',json={'hours':8}).status_code==200
    assert {'cobranca_sla','escalonamento'} <= {n['kind'] for n in client.get('/v2/notifications').json()}
    assert client.post(path+'/transition',json={'action':'resolver','message':'Servidor fictício restabelecido. Operação normalizada.'}).status_code==200
    switch(client,'colaborador')
    assert client.get(path).json()['resolution'].startswith('Servidor fictício')
    switch(client,'central')
    assert client.get('/v2/reports').json()['departments'][0]['resolved']==1
    assert client.get('/v2/reports').json()['departments'][0]['overdue']==1
    assert client.post('/v2/sla/evaluate').json()['notifications_created']==0

def test_switch_is_never_available_for_local_accounts(portal):
    client,workspace,_=portal
    login(client,'central')
    assert client.post('/v2/lab/switch',json={'username':'colaborador'}).status_code==403
    assert client.post('/v2/lab/advance',json={'hours':8}).status_code==403
    with conectar() as conn:assert conn.execute('SELECT clock_hours FROM sf_workspaces WHERE id=%s',(workspace,)).fetchone()['clock_hours']==0

def test_lab_cookie_cannot_authenticate_local_and_exceptions_preserve_source(portal):
    client,who=start()
    assert client.get('/v2/cases',headers={'X-SolicitaFlow-Context':'local'}).status_code==401
    case=create(client,description='A equipe relata falha no servidor e também problema com pagamento da fatura.').json()
    assert case['state']=='excecao'
    switch(client,'central')
    route=next(r for r in client.get('/v2/routes').json() if r['category']=='suporte_ti')
    result=client.post('/v2/cases/'+case['id']+'/review',json={'category':'suporte_ti','department_id':route['department_id'],'impact':'equipe','urgency':'media','reason':'O visitante esclareceu que o problema é no servidor.'})
    assert result.status_code==200,result.text
    assert result.json()['request']['categoria_sugerida']=='outros'
    assert result.json()['request']['categoria_final']=='suporte_ti'

def test_laboratory_limits_requests_and_time(portal):
    client,_=start()
    assert client.post('/v2/lab/advance',json={'hours':721}).status_code==422
    for _ in range(20):assert create(client).status_code==201
    assert create(client).status_code==429

def test_role_switch_rotates_capability_and_cannot_select_other_visitors(portal):
    client,who=start()
    token=client.cookies.get('sf_lab')
    switch(client,'central')
    stale=TestClient(app,headers={'X-SolicitaFlow-Context':'lab'},cookies={'sf_lab':token})
    assert stale.get('/v2/session').status_code==401
    assert client.post('/v2/lab/switch',json={'username':str(uuid4())}).status_code==404

def test_concurrent_submission_creates_one_request_and_one_route(portal,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from app import portals
    from app.routing import simulate
    client,who=start()
    calls=[]
    def classify(*args):
        calls.append(1)
        return simulate(*args)
    monkeypatch.setattr(portals,'simulate',classify)
    key=str(uuid4())
    def submit(_):
        isolated=TestClient(app,headers={'X-SolicitaFlow-Context':'lab'},cookies=dict(client.cookies))
        return create(isolated,client_key=key)
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(submit,range(2)))
    assert [r.status_code for r in responses]==[201,201]
    assert responses[0].json()['id']==responses[1].json()['id']
    assert len(calls)==1
    with conectar() as conn:
        assert conn.execute('SELECT count(*) n FROM sf_cases WHERE workspace_id=%s',(who['workspace_id'],)).fetchone()['n']==1
        assert conn.execute('SELECT count(*) n FROM sf_routing_decisions WHERE workspace_id=%s',(who['workspace_id'],)).fetchone()['n']==1


def test_new_request_after_time_advance_uses_virtual_creation_time(portal):
    from datetime import datetime
    client,_=start()
    assert client.post('/v2/lab/advance',json={'hours':14}).status_code==200
    case=create(client).json()
    clock=client.get('/v2/lab/clock').json()['effective_now']
    assert abs((datetime.fromisoformat(clock)-datetime.fromisoformat(case['created_at'])).total_seconds())<5
    assert datetime.fromisoformat(case['request']['criado_em'])==datetime.fromisoformat(case['created_at'])
    switch(client,'suporte_ti')
    for action in ('assumir','resolver'):
        assert client.post('/v2/cases/'+case['id']+'/transition',json={'action':action,'message':'Servidor fictício verificado e restabelecido.'}).status_code==200
    switch(client,'central')
    report=client.get('/v2/reports').json()['departments'][0]
    assert report['average_first_response_hours']<0.01
    assert report['average_resolution_hours']<0.01
