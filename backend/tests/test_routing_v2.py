from uuid import uuid4
import pytest
from app.routing import simulate,routing_reasons,finalize
from app.database import conectar

TITLE='Servidor indisponível'
DESC='A equipe está impedida de trabalhar porque o servidor está parado desde o início do expediente.'

def test_rules_do_not_trust_confidence():
    result=simulate(TITLE,DESC)
    assert result.prioridade=='alta'
    assert routing_reasons(TITLE,DESC,result,{'active':True,'review_required':False})==[]
    assert 'destino_indisponivel' in routing_reasons(TITLE,DESC,result,None)
    ambiguous=simulate(TITLE,DESC+' Também há reembolso pendente.')
    assert 'assunto_ambiguo_ou_nao_confirmado' in routing_reasons(TITLE,DESC+' Também há reembolso pendente.',ambiguous,None)
    assert routing_reasons(TITLE,DESC,None,None)==['classificacao_indisponivel']

def test_routing_is_persisted_once(monkeypatch):
    monkeypatch.setenv('PGDATABASE','ai_request_classifier_test')
    from conftest import clean_test_database
    with conectar() as c:
        clean_test_database(c)
        w,d,case=uuid4(),uuid4(),uuid4()
        c.execute("INSERT INTO sf_workspaces(id,name,kind) VALUES(%s,'Teste','lab')",(w,))
        c.execute("INSERT INTO sf_departments(id,workspace_id,name) VALUES(%s,%s,'Tecnologia')",(d,w))
        c.execute("INSERT INTO sf_routes(workspace_id,category,department_id) VALUES(%s,'suporte_ti',%s)",(w,d))
        rid=c.execute('INSERT INTO solicitacoes(titulo,descricao) VALUES(%s,%s) RETURNING id',(TITLE,DESC)).fetchone()['id']
        c.execute("INSERT INTO sf_cases(id,workspace_id,request_id,client_key,source) VALUES(%s,%s,%s,%s,'simulacao')",(case,w,rid,uuid4()))
        result=simulate(TITLE,DESC)
        assert finalize(c,case,result)['state']=='encaminhada'
        assert finalize(c,case,result)['state']=='encaminhada'
        assert c.execute('SELECT count(*) n FROM sf_routing_decisions').fetchone()['n']==1
        assert c.execute("SELECT count(*) n FROM sf_events WHERE type='roteamento_automatico'").fetchone()['n']==1
        assert c.execute("SELECT count(*) n FROM sf_events WHERE type='sla_definido'").fetchone()['n']==1
