from datetime import timedelta
import pytest
from app.database import conectar
from app.workflow import evaluate,now_for,sla_state
from test_portals_v2 import portal,login,create

def test_department_lifecycle_and_report(portal):
    client,workspace,_=portal
    login(client,'colaborador');case=create(client).json();path='/v2/cases/'+case['id']
    assert case['resolution_due']
    assert client.post(path+'/transition',json={'action':'assumir','message':'Atendimento iniciado pela equipe.'}).status_code==403
    login(client,'financeiro')
    assert client.post(path+'/transition',json={'action':'assumir','message':'Atendimento iniciado pela equipe.'}).status_code==404
    login(client,'suporte_ti')
    assert client.post(path+'/transition',json={'action':'resolver','message':'O servidor voltou a funcionar.'}).status_code==403
    for action,state in [('assumir','em_atendimento'),('andamento','em_atendimento'),('aguardar','aguardando_colaborador'),('retomar','em_atendimento'),('resolver','resolvida')]:
        response=client.post(path+'/transition',json={'action':action,'message':'O servidor foi verificado pela equipe fictícia.'})
        assert response.status_code==200,response.text
        assert response.json()['state']==state
    assert client.post(path+'/transition',json={'action':'resolver','message':'Resolver novamente não é permitido.'}).status_code==409
    login(client,'colaborador');response=client.get(path).json()
    assert response['resolved_at'] and response['first_response_at'] and response['resolution']
    login(client,'central');report=client.get('/v2/reports').json()
    assert report['departments'][0]['resolved']==1

def test_sla_risk_violation_and_escalation_are_idempotent(portal):
    client,workspace,_=portal
    login(client,'colaborador');case=create(client).json()
    with conectar() as conn:
        # Move only the test case deadlines, never the operating system clock.
        now=now_for(conn,workspace)
        conn.execute('UPDATE sf_cases SET resolution_due=%s,first_response_due=%s WHERE id=%s',(now+timedelta(hours=1),now-timedelta(hours=1),case['id']))
        first=evaluate(conn,workspace)
        assert first['notifications_created']==2
        assert evaluate(conn,workspace)['notifications_created']==0
        conn.execute('UPDATE sf_cases SET resolution_due=%s WHERE id=%s',(now-timedelta(hours=5),case['id']))
        assert evaluate(conn,workspace)['notifications_created']==2
        assert evaluate(conn,workspace)['notifications_created']==0
    login(client,'central');alerts=client.get('/v2/notifications').json()
    assert {x['kind'] for x in alerts}=={'risco_sla','primeira_resposta_atrasada','cobranca_sla','escalonamento'}
    assert client.get('/v2/reports').json()['departments'][0]['overdue']==1

def test_policy_validation_and_snapshot(portal):
    client,workspace,_=portal
    login(client,'colaborador');case=create(client).json()
    login(client,'central')
    body={'priority':'alta','first_response_hours':2,'resolution_hours':16,'risk_hours':2,'escalation_hours':6}
    assert client.put('/v2/sla/policies',json=body).status_code==200
    assert client.get('/v2/cases/'+case['id']).json()['resolution_due']==case['resolution_due']
    assert client.put('/v2/sla/policies',json={**body,'first_response_hours':20}).status_code==422
