"""Scoped portal API. Every resource query is bound to an authenticated workspace."""
from datetime import datetime,timezone
import os,hashlib
from uuid import UUID,uuid4
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from pydantic import BaseModel,Field,ConfigDict
from app.database import conectar
from app.identity import actor,require,issue_session,password_matches,public_actor,rate_limit,visible_case,context
from app.routing import simulate,finalize,event
from app.ia import classificar_solicitacao,ErroClassificacao
from app.schemas import SolicitacaoEntrada
from app.classificacao import Categoria,Impacto,Urgencia,calcular_prioridade
from psycopg.types.json import Jsonb

router=APIRouter(prefix='/v2',tags=['SolicitaFlow'])

class Login(BaseModel):
    username:str=Field(min_length=1,max_length=80)
    password:str=Field(min_length=1,max_length=200)

@router.post('/login')
def login(data:Login,request:Request,response:Response):
    if context(request)!='local':raise HTTPException(400,'Use a entrada do laboratório')
    with conectar() as conn:
        allowed=rate_limit(conn,'login:'+request.client.host,20)
    if not allowed:raise HTTPException(429,'Muitas tentativas. Aguarde a próxima hora.')
    with conectar() as conn:
        who=conn.execute("SELECT a.*,w.kind FROM sf_accounts a JOIN sf_workspaces w ON w.id=a.workspace_id WHERE w.kind='local' AND a.username=%s",(data.username,)).fetchone()
        if not who or not password_matches(data.password,who['password_hash']): raise HTTPException(401,'Usuário ou senha inválidos')
        issue_session(conn,who,response,'local')
    return public_actor(who)

@router.get('/session')
def session(who=Depends(actor)):return public_actor(who)

@router.post('/logout',status_code=204)
def logout(request:Request,response:Response,who=Depends(actor)):
    kind=context(request)
    with conectar() as conn:conn.execute('DELETE FROM sf_sessions WHERE token_hash=%s',(hashlib.sha256(request.cookies['sf_'+kind].encode()).hexdigest(),))
    response.delete_cookie('sf_'+kind,path='/')

class CreateCase(SolicitacaoEntrada):
    client_key:UUID
    mode:str=Field(default='simulacao',pattern='^(simulacao|deepseek)$')

@router.post('/cases',status_code=201)
def create_case(data:CreateCase,who=Depends(actor)):
    require(who,'colaborador')
    if data.mode=='deepseek' and (who['kind']!='local' or os.getenv('SF_REAL_AI_ENABLED','false')!='true'):
        raise HTTPException(403,'IA real indisponível neste ambiente; utilize simulação')
    with conectar() as conn:
        # Same idempotency key serializes concurrent submissions, including the paid budget reservation.
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(str(who['workspace_id'])+str(data.client_key),))
        old=conn.execute('SELECT id,requester_id FROM sf_cases WHERE workspace_id=%s AND client_key=%s',(who['workspace_id'],data.client_key)).fetchone()
        if old:
            if old['requester_id']!=who['id']:raise HTTPException(409,'Identificador já utilizado')
            return detail(old['id'],who)
        if who['kind']=='lab' and conn.execute('SELECT count(*) n FROM sf_cases WHERE workspace_id=%s',(who['workspace_id'],)).fetchone()['n']>=20:raise HTTPException(429,'Limite de 20 solicitações por laboratório')
        if data.mode=='deepseek':
            budget=conn.execute('''INSERT INTO sf_ai_budgets(workspace_id,day,used) VALUES(%s,current_date,1)
                ON CONFLICT(workspace_id,day) DO UPDATE SET used=sf_ai_budgets.used+1 WHERE sf_ai_budgets.used<2 RETURNING used''',(who['workspace_id'],)).fetchone()
            if not budget:raise HTTPException(429,'Cota diária de duas classificações atingida')
        rid=conn.execute('INSERT INTO solicitacoes(titulo,descricao) VALUES(%s,%s) RETURNING id',(data.titulo,data.descricao)).fetchone()['id']
        case=conn.execute('''INSERT INTO sf_cases(id,workspace_id,request_id,client_key,source,requester_id)
            VALUES(%s,%s,%s,%s,%s,%s) RETURNING *''',(uuid4(),who['workspace_id'],rid,data.client_key,data.mode,who['id'])).fetchone()
        event(conn,case,'cadastrada',{'source':data.mode},who['id'])
    # The original request is committed before any external operation.
    try:result=simulate(data.titulo,data.descricao) if data.mode=='simulacao' else classificar_solicitacao(data.titulo,data.descricao)
    except ErroClassificacao:result=None
    with conectar() as conn:finalize(conn,case['id'],result)
    return detail(case['id'],who)

@router.get('/cases')
def cases(who=Depends(actor)):
    with conectar() as conn:
        clause=''
        params=[who['workspace_id']]
        if who['role']=='colaborador':clause=' AND c.requester_id=%s';params.append(who['id'])
        if who['role']=='departamento':clause=' AND c.department_id=%s';params.append(who['department_id'])
        return conn.execute('''SELECT c.*,s.titulo,s.descricao,d.name AS department_name FROM sf_cases c
            JOIN solicitacoes s ON s.id=c.request_id LEFT JOIN sf_departments d ON d.id=c.department_id
            WHERE c.workspace_id=%s'''+clause+' ORDER BY c.created_at DESC',params).fetchall()

@router.get('/cases/{case_id}')
def detail(case_id:UUID,who=Depends(actor)):
    with conectar() as conn:
        case=visible_case(conn,who,case_id)
        case['request']=conn.execute('SELECT * FROM solicitacoes WHERE id=%s',(case['request_id'],)).fetchone()
        case['events']=conn.execute('SELECT * FROM sf_events WHERE workspace_id=%s AND case_id=%s ORDER BY id',(who['workspace_id'],case_id)).fetchall()
        case['decisions']=conn.execute('SELECT * FROM sf_routing_decisions WHERE workspace_id=%s AND case_id=%s ORDER BY id',(who['workspace_id'],case_id)).fetchall()
        return case

@router.get('/departments')
def departments(who=Depends(actor)):
    with conectar() as conn:return conn.execute('SELECT id,name,active FROM sf_departments WHERE workspace_id=%s ORDER BY name',(who['workspace_id'],)).fetchall()

class Department(BaseModel):
    name:str=Field(min_length=3,max_length=100)

@router.post('/departments',status_code=201)
def add_department(data:Department,who=Depends(actor)):
    require(who,'central')
    with conectar() as conn:
        if conn.execute('SELECT 1 FROM sf_departments WHERE workspace_id=%s AND name=%s',(who['workspace_id'],data.name.strip())).fetchone():raise HTTPException(409,'Departamento já cadastrado')
        return conn.execute('INSERT INTO sf_departments(id,workspace_id,name) VALUES(%s,%s,%s) RETURNING *',(uuid4(),who['workspace_id'],data.name.strip())).fetchone()

@router.get('/routes')
def routes(who=Depends(actor)):
    require(who,'central')
    with conectar() as conn:return conn.execute('SELECT * FROM sf_routes WHERE workspace_id=%s ORDER BY category',(who['workspace_id'],)).fetchall()

class Route(BaseModel):
    category:Categoria
    department_id:UUID
    review_required:bool=False

@router.put('/routes')
def set_route(data:Route,who=Depends(actor)):
    require(who,'central')
    with conectar() as conn:
        if not conn.execute('SELECT 1 FROM sf_departments WHERE workspace_id=%s AND id=%s AND active',(who['workspace_id'],data.department_id)).fetchone():raise HTTPException(422,'Departamento não disponível')
        conn.execute('''INSERT INTO sf_routes(workspace_id,category,department_id,review_required) VALUES(%s,%s,%s,%s)
            ON CONFLICT(workspace_id,category) DO UPDATE SET department_id=EXCLUDED.department_id,review_required=EXCLUDED.review_required''',
            (who['workspace_id'],data.category.value,data.department_id,data.review_required))
    return {'ok':True}

class Review(Route):
    impact:Impacto
    urgency:Urgencia
    reason:str=Field(min_length=10,max_length=500)

@router.post('/cases/{case_id}/review')
def review(case_id:UUID,data:Review,who=Depends(actor)):
    require(who,'central')
    with conectar() as conn:
        case=visible_case(conn,who,case_id,True)
        if case['state']!='excecao':raise HTTPException(409,'Somente exceções podem ser revisadas')
        route=conn.execute('SELECT * FROM sf_routes r JOIN sf_departments d ON d.id=r.department_id WHERE r.workspace_id=%s AND r.category=%s AND d.active',(who['workspace_id'],data.category.value)).fetchone()
        if not route or route['department_id']!=data.department_id:raise HTTPException(422,'Destino não corresponde ao mapeamento validado')
        priority=calcular_prioridade(data.impact,data.urgency).value
        conn.execute('UPDATE sf_cases SET category=%s,impact=%s,urgency=%s,priority=%s,department_id=%s,state=%s WHERE id=%s',
            (data.category.value,data.impact.value,data.urgency.value,priority,data.department_id,'encaminhada',case_id))
        conn.execute('''UPDATE solicitacoes SET categoria_final=%s,impacto_final=%s,urgencia_final=%s,prioridade_final=%s,
            decisao_revisao='corrigir',observacao_revisao=%s,revisado_em=now(),status='revisada' WHERE id=%s''',
            (data.category.value,data.impact.value,data.urgency.value,priority,data.reason,case['request_id']))
        conn.execute("INSERT INTO sf_routing_decisions(workspace_id,case_id,step,outcome,reasons,department_id) VALUES(%s,%s,'review','manual',%s,%s)",(who['workspace_id'],case_id,Jsonb([data.reason]),data.department_id))
        event(conn,case,'revisao_humana',{'reason':data.reason,'priority':priority},who['id'])
    return detail(case_id,who)
