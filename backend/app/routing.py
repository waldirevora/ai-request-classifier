"""Deterministic routing. A model confidence score never grants authority."""
import re
import unicodedata
from uuid import uuid4
from psycopg.types.json import Jsonb
from app.classificacao import calcular_prioridade, Impacto, Urgencia
from app.ia import ResultadoIA, RespostaLLM

KEYWORDS = {
 'suporte_ti': ('computador','servidor','sistema','impressora','rede'),
 'acessos_permissoes': ('senha','permissao','acesso','login'),
 'financeiro': ('nota fiscal','pagamento','reembolso','fatura'),
 'recursos_humanos': ('ferias','beneficio','contratacao','folha'),
}
def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))

def topics(text):
    value=normalized(text)
    return {cat for cat,words in KEYWORDS.items() if any(re.search(r'\b'+re.escape(word)+r'\b',value) for word in words)}

def simulate(title, description):
    """Explicit laboratory fixture, never represented as an actual AI response."""
    matches=topics(title+' '+description)
    category=next(iter(matches)) if len(matches)==1 else 'outros'
    text=normalized(description)
    impact='empresa' if 'empresa' in text else 'equipe' if 'equipe' in text else 'individual'
    urgency='alta' if 'impedida' in text or 'parado' in text else 'media' if 'prazo' in text else 'baixa'
    return ResultadoIA(category,impact,urgency,calcular_prioridade(Impacto(impact),Urgencia(urgency)).value,
                       'Simulação determinística por palavras e contexto explícitos; não utiliza API externa.',
                       'simulacao-local',0,0,0)

def routing_reasons(title, description, result, route):
    if result is None: return ['classificacao_indisponivel']
    # Validate enum/schema independently of any adapter or model.
    try: RespostaLLM(categoria=result.categoria,impacto=result.impacto,urgencia=result.urgencia,justificativa=result.justificativa)
    except ValueError: return ['resposta_invalida']
    text=normalized(title+' '+description)
    reasons=[]
    if len(description.strip())<40: reasons.append('informacao_insuficiente')
    if topics(text)!={result.categoria} or result.categoria=='outros': reasons.append('assunto_ambiguo_ou_nao_confirmado')
    if any(x in text for x in ('ignore instru','system prompt','responda apenas','ignore previous')): reasons.append('instrucao_suspeita')
    if result.impacto=='equipe' and 'equipe' not in text: reasons.append('impacto_sem_evidencia')
    if result.impacto=='empresa' and 'empresa' not in text: reasons.append('impacto_sem_evidencia')
    if result.urgencia=='alta' and not any(x in text for x in ('impedid','parado','interromp','bloquead')): reasons.append('urgencia_sem_evidencia')
    if not route or not route['active']: reasons.append('destino_indisponivel')
    elif route['review_required']: reasons.append('categoria_exige_revisao')
    return reasons

def event(conn, case, kind, payload=None, actor=None):
    payload=dict(payload or {})
    clock=conn.execute('SELECT now()+make_interval(hours=>clock_hours) AS effective_at FROM sf_workspaces WHERE id=%s',(case['workspace_id'],)).fetchone()
    payload.setdefault('effective_at',clock['effective_at'].isoformat())
    conn.execute('INSERT INTO sf_events(workspace_id,case_id,actor_id,type,payload) VALUES(%s,%s,%s,%s,%s)',
                 (case['workspace_id'],case['id'],actor,kind,Jsonb(payload or {})))

def finalize(conn, case_id, result):
    case=conn.execute('SELECT * FROM sf_cases WHERE id=%s FOR UPDATE',(case_id,)).fetchone()
    if not case or case['state']!='analisando': return case
    request=conn.execute('SELECT * FROM solicitacoes WHERE id=%s',(case['request_id'],)).fetchone()
    route=conn.execute('''SELECT r.*,d.active FROM sf_routes r JOIN sf_departments d
        ON (r.workspace_id,r.department_id)=(d.workspace_id,d.id)
        WHERE r.workspace_id=%s AND r.category=%s''',(case['workspace_id'],result.categoria if result else '')).fetchone()
    reasons=routing_reasons(request['titulo'],request['descricao'],result,route)
    if result:
        priority=calcular_prioridade(Impacto(result.impacto),Urgencia(result.urgencia)).value if 'resposta_invalida' not in reasons else None
        if priority:
            conn.execute('''UPDATE solicitacoes SET categoria_sugerida=%s,impacto_sugerido=%s,urgencia_sugerida=%s,
                prioridade_sugerida=%s,justificativa_ia=%s,modelo_ia=%s,tokens_entrada=%s,tokens_saida=%s,
                latencia_ia_ms=%s,classificado_em=now() WHERE id=%s''',
                (result.categoria,result.impacto,result.urgencia,priority,result.justificativa,result.modelo,
                 result.tokens_entrada,result.tokens_saida,result.latencia_ms,case['request_id']))
            conn.execute('UPDATE sf_cases SET category=%s,impact=%s,urgency=%s,priority=%s WHERE id=%s',
                         (result.categoria,result.impacto,result.urgencia,priority,case_id))
    outcome='excecao' if reasons else 'automatico'
    department=None if reasons else route['department_id']
    conn.execute('''INSERT INTO sf_routing_decisions(workspace_id,case_id,step,outcome,reasons,department_id)
        VALUES(%s,%s,'initial',%s,%s,%s)''',(case['workspace_id'],case_id,outcome,Jsonb(reasons),department))
    conn.execute('UPDATE solicitacoes SET status=%s WHERE id=%s',('aguardando_revisao' if reasons else 'classificada_automaticamente',case['request_id']))
    updated=conn.execute('UPDATE sf_cases SET state=%s,department_id=%s WHERE id=%s RETURNING *',
        ('excecao' if reasons else 'encaminhada',department,case_id)).fetchone()
    event(conn,case,'roteamento_'+outcome,{'reasons':reasons,'department_id':str(department) if department else None})
    from app.workflow import apply_policy
    apply_policy(conn,updated)
    return updated
