from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field,field_validator
from app.database import conectar
from app.identity import actor,require,visible_case
from app.portals import detail
from app.workflow import transition,evaluate,report,ensure_policies,LAB_POLICIES_FIELDS

router=APIRouter(prefix='/v2',tags=['Operações e SLA'])

class Update(BaseModel):
    action:str=Field(pattern='^(assumir|andamento|aguardar|retomar|resolver)$')
    message:str=Field(min_length=10,max_length=1000)
    @field_validator('message',mode='before')
    @classmethod
    def trim(cls,value):return value.strip() if isinstance(value,str) else value

@router.post('/cases/{case_id}/transition')
def update(case_id:UUID,data:Update,who=Depends(actor)):
    require(who,'departamento')
    with conectar() as conn:
        case=visible_case(conn,who,case_id,True)
        transition(conn,case,who,data.action,data.message)
    return detail(case_id,who)

@router.get('/reports')
def reports(who=Depends(actor)):
    require(who,'central')
    with conectar() as conn:return report(conn,who['workspace_id'])

@router.get('/notifications')
def notifications(who=Depends(actor)):
    with conectar() as conn:
        clause='';params=[who['workspace_id']]
        if who['role']=='colaborador':clause=' AND c.requester_id=%s';params.append(who['id'])
        if who['role']=='departamento':clause=' AND c.department_id=%s';params.append(who['department_id'])
        return conn.execute('''SELECT n.* FROM sf_notifications n JOIN sf_cases c ON c.id=n.case_id
            WHERE n.workspace_id=%s'''+clause+' ORDER BY n.id DESC',params).fetchall()

@router.post('/sla/evaluate')
def check(who=Depends(actor)):
    require(who,'central')
    with conectar() as conn:return evaluate(conn,who['workspace_id'])

@router.get('/sla/policies')
def policies(who=Depends(actor)):
    require(who,'central')
    with conectar() as conn:
        ensure_policies(conn,who['workspace_id'])
        return conn.execute('SELECT * FROM sf_sla_policies WHERE workspace_id=%s ORDER BY priority',(who['workspace_id'],)).fetchall()

class Policy(BaseModel):
    priority:str=Field(pattern='^(baixa|media|alta)$')
    first_response_hours:int=Field(ge=1,le=720)
    resolution_hours:int=Field(ge=1,le=720)
    risk_hours:int=Field(ge=1,le=48)
    escalation_hours:int=Field(ge=1,le=720)

@router.put('/sla/policies')
def policy(data:Policy,who=Depends(actor)):
    require(who,'central')
    if data.first_response_hours>data.resolution_hours or data.risk_hours>data.resolution_hours:raise HTTPException(422,'Prazos inconsistentes')
    with conectar() as conn:
        conn.execute('''INSERT INTO sf_sla_policies(workspace_id,priority,first_response_hours,resolution_hours,risk_hours,escalation_hours)
            VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(workspace_id,priority) DO UPDATE SET first_response_hours=EXCLUDED.first_response_hours,
            resolution_hours=EXCLUDED.resolution_hours,risk_hours=EXCLUDED.risk_hours,escalation_hours=EXCLUDED.escalation_hours''',
            (who['workspace_id'],data.priority,*[getattr(data,k) for k in LAB_POLICIES_FIELDS]))
    return {'ok':True,'note':'Aplica-se somente a novos encaminhamentos; prazos existentes preservam o snapshot.'}
