"""SLA and transitions are deterministic. No model calls, wall-clock changes or email."""
from datetime import datetime,timezone,timedelta
from psycopg.types.json import Jsonb
from fastapi import HTTPException
from app.routing import event

LAB_POLICIES={'alta':(2,8,2,4),'media':(8,24,4,8),'baixa':(24,72,6,24)}

def ensure_policies(conn,workspace):
    for priority,values in LAB_POLICIES.items():
        conn.execute('''INSERT INTO sf_sla_policies(workspace_id,priority,first_response_hours,resolution_hours,risk_hours,escalation_hours)
            VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',(workspace,priority,*values))

def now_for(conn,workspace):
    row=conn.execute('SELECT clock_hours FROM sf_workspaces WHERE id=%s',(workspace,)).fetchone()
    return datetime.now(timezone.utc)+timedelta(hours=row['clock_hours'])

def apply_policy(conn,case):
    if case['state'] not in ('encaminhada','em_atendimento','aguardando_colaborador') or case.get('resolution_due'):return
    ensure_policies(conn,case['workspace_id'])
    policy=conn.execute('SELECT * FROM sf_sla_policies WHERE workspace_id=%s AND priority=%s',(case['workspace_id'],case['priority'])).fetchone()
    timestamp=now_for(conn,case['workspace_id'])
    snapshot={k:policy[k] for k in LAB_POLICIES_FIELDS}
    conn.execute('UPDATE sf_cases SET first_response_due=%s,resolution_due=%s,policy_snapshot=%s WHERE id=%s',
        (timestamp+timedelta(hours=policy['first_response_hours']),timestamp+timedelta(hours=policy['resolution_hours']),Jsonb(snapshot),case['id']))
    event(conn,case,'sla_definido',snapshot)

LAB_POLICIES_FIELDS=('first_response_hours','resolution_hours','risk_hours','escalation_hours')

def sla_state(case,now):
    if case['state']=='resolvida':
        return 'resolvido_em_atraso' if case.get('resolution_due') and case['resolved_at']>case['resolution_due'] else 'concluido'
    due=case.get('resolution_due')
    if not due:return 'sem_prazo'
    if now>=due:return 'violado'
    if now>=due-timedelta(hours=case['policy_snapshot']['risk_hours']):return 'em_risco'
    return 'normal'

def evaluate(conn,workspace):
    conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,1))',(str(workspace),))
    now=now_for(conn,workspace)
    rows=conn.execute("SELECT * FROM sf_cases WHERE workspace_id=%s AND state<>'resolvida' ORDER BY id FOR UPDATE",(workspace,)).fetchall()
    created=0
    for case in rows:
        # Reconcile a worker interrupted after the original INSERT; never call AI again.
        if case['state']=='analisando' and datetime.now(timezone.utc)-case['created_at']>timedelta(minutes=5):
            from app.routing import finalize
            finalize(conn,case['id'],None)
            continue
        apply_policy(conn,case)
        case=conn.execute('SELECT * FROM sf_cases WHERE id=%s',(case['id'],)).fetchone()
        if not case['resolution_due']:continue
        notifications=[]
        state=sla_state(case,now)
        if state=='em_risco':notifications.append(('risco_sla','Prazo de resolução próximo. Revise o atendimento.'))
        if state=='violado':notifications.append(('cobranca_sla','Prazo de resolução violado. Cobrança interna registrada.'))
        if not case['first_response_at'] and now>=case['first_response_due']:notifications.append(('primeira_resposta_atrasada','Primeira resposta pendente após o prazo.'))
        if now>=case['resolution_due']+timedelta(hours=case['policy_snapshot']['escalation_hours']):notifications.append(('escalonamento','Escalonamento para a central: atraso excede a política configurada.'))
        for kind,message in notifications:
            inserted=conn.execute('''INSERT INTO sf_notifications(workspace_id,case_id,kind,message,created_at) VALUES(%s,%s,%s,%s,%s)
                ON CONFLICT(case_id,kind) DO NOTHING RETURNING id''',(workspace,case['id'],kind,message,now)).fetchone()
            if inserted:
                event(conn,case,kind,{'message':message,'effective_at':now.isoformat()})
                created+=1
    return {'notifications_created':created,'effective_now':now}

def transition(conn,case,who,action,message):
    now=now_for(conn,case['workspace_id'])
    if action=='assumir':
        if case['state']!='encaminhada' or case['responsible_id']:raise HTTPException(409,'Solicitação já assumida ou estado incompatível')
        conn.execute("UPDATE sf_cases SET responsible_id=%s,state='em_atendimento' WHERE id=%s",(who['id'],case['id']))
    else:
        if case['responsible_id']!=who['id']:raise HTTPException(403,'Somente o responsável pode atualizar o atendimento')
        if action=='resolver':
            if case['state'] not in ('em_atendimento','aguardando_colaborador'):raise HTTPException(409,'Estado inválido para resolução')
            conn.execute("UPDATE sf_cases SET state='resolvida',resolution=%s,resolved_at=%s,first_response_at=coalesce(first_response_at,%s) WHERE id=%s",(message,now,now,case['id']))
        else:
            states={'andamento':('em_atendimento','em_atendimento'),'aguardar':('em_atendimento','aguardando_colaborador'),'retomar':('aguardando_colaborador','em_atendimento')}
            if action not in states or case['state']!=states[action][0]:raise HTTPException(409,'Transição não permitida')
            conn.execute('UPDATE sf_cases SET state=%s,first_response_at=coalesce(first_response_at,%s) WHERE id=%s',(states[action][1],now,case['id']))
    event(conn,case,action,{'message':message,'effective_at':now.isoformat()},who['id'])

def report(conn,workspace):
    now=now_for(conn,workspace)
    rows=conn.execute('''SELECT c.*,d.name AS department_name FROM sf_cases c LEFT JOIN sf_departments d ON d.id=c.department_id
        WHERE c.workspace_id=%s ORDER BY c.created_at''',(workspace,)).fetchall()
    result={}
    for case in rows:
        name=case['department_name'] or 'Sem destino'
        group=result.setdefault(name,{'department':name,'total':0,'resolved':0,'overdue':0,'at_risk':0,'first_response_hours':[],'resolution_hours':[]})
        group['total']+=1
        group['resolved']+=int(case['state']=='resolvida')
        state=sla_state(case,now)
        group['overdue']+=int(state in ('violado','resolvido_em_atraso'))
        group['at_risk']+=int(state=='em_risco')
        if case['first_response_at']:group['first_response_hours'].append(max(0,(case['first_response_at']-case['created_at']).total_seconds()/3600))
        if case['resolved_at']:group['resolution_hours'].append(max(0,(case['resolved_at']-case['created_at']).total_seconds()/3600))
    for group in result.values():
        for key in ('first_response_hours','resolution_hours'):
            values=group.pop(key);group['average_'+key]=round(sum(values)/len(values),2) if values else None
    return {'effective_now':now,'departments':list(result.values()),'total':len(rows),'exceptions':sum(c['state']=='excecao' for c in rows)}
