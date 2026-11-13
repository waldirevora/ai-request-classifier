"""Activity-driven cleanup of expired fictitious labs; never targets the local main DB."""
import hashlib,os
from app.database import conectar


def cleanup(conn):
    if not conn.execute('SELECT pg_try_advisory_xact_lock(826176013) AS ok').fetchone()['ok']:return {'skipped':True}
    rows=conn.execute("SELECT id,(expires_at<now()-interval '32 days' AND NOT EXISTS(SELECT 1 FROM sf_ai_attempts a WHERE a.workspace_id=sf_workspaces.id AND (a.day>=(now() AT TIME ZONE 'UTC')::date-32 OR a.status='reserved'))) AS purge FROM sf_workspaces WHERE kind='lab' AND expires_at<=now() FOR UPDATE").fetchall()
    expired=[r['id'] for r in rows];old=[r['id'] for r in rows if r['purge']]
    if expired:
        conn.execute("UPDATE sf_cases SET state='excecao',analysis_status='failed',analysis_code='laboratorio_expirado',analysis_finished_at=now() WHERE workspace_id=ANY(%s) AND state='analisando'",(expired,))
        conn.execute("UPDATE solicitacoes SET titulo='Solicitação expirada',descricao='Dados fictícios removidos após expiração do laboratório.',justificativa_ia=NULL,observacao_revisao=NULL WHERE id IN (SELECT request_id FROM sf_cases WHERE workspace_id=ANY(%s))",(expired,))
        conn.execute('UPDATE sf_cases SET resolution=NULL WHERE workspace_id=ANY(%s)',(expired,))
        for table in ('sf_notifications','sf_events','sf_routing_decisions'):
            conn.execute('DELETE FROM '+table+' WHERE workspace_id=ANY(%s)',(expired,))
    if old:
        ids=[r['request_id'] for r in conn.execute('SELECT request_id FROM sf_cases WHERE workspace_id=ANY(%s) UNION SELECT request_id FROM sf_legacy_submissions WHERE workspace_id=ANY(%s)',(old,old)).fetchall()]
        for table in ('sf_ai_attempts','sf_legacy_submissions','sf_cases','sf_sessions','sf_accounts','sf_routes','sf_sla_policies','sf_departments','sf_ai_budgets'):
            conn.execute('DELETE FROM '+table+' WHERE workspace_id=ANY(%s)',(old,))
        conn.execute("DELETE FROM sf_workspaces WHERE id=ANY(%s) AND kind='lab' AND expires_at<now()-interval '32 days'",(old,))
        if ids:conn.execute('DELETE FROM solicitacoes WHERE id=ANY(%s)',(ids,))
    conn.execute('DELETE FROM sf_sessions WHERE expires_at<=now()')
    conn.execute("DELETE FROM sf_rate_windows WHERE bucket<floor(extract(epoch FROM now())/3600)::bigint-48")
    return {'redacted':len(expired),'purged':len(old)}


def activity():
    if os.getenv('SF_ENV')!='production':return
    if os.getenv('PGDATABASE') not in ('solicitaflow_demo','ai_request_classifier_test'):raise RuntimeError('Cleanup database forbidden')
    with conectar(user=os.environ['SF_CLEANUP_USER'],password=os.environ['SF_CLEANUP_PASSWORD']) as conn:
        marker=hashlib.sha256(b'cleanup.v1').hexdigest()
        row=conn.execute("INSERT INTO sf_rate_windows(key,bucket) VALUES(%s,floor(extract(epoch FROM now())/3600)::bigint) ON CONFLICT DO NOTHING RETURNING count",(marker,)).fetchone()
        if row:cleanup(conn)


def admit_lab(conn):
    if os.getenv('SF_ENV')!='production':return
    conn.execute('SELECT pg_advisory_xact_lock(826176014)')
    maximum=int(os.getenv('SF_LAB_DAILY_MAX','30'));active=int(os.getenv('SF_LAB_ACTIVE_MAX','30'))
    if not 1<=maximum<=100 or not 1<=active<=50:raise ValueError('Invalid public laboratory limits')
    from fastapi import HTTPException
    count=conn.execute("SELECT count(*) AS n FROM sf_workspaces WHERE kind='lab' AND expires_at>now()").fetchone()['n']
    marker=hashlib.sha256(b'public-lab-daily').hexdigest()
    row=conn.execute("INSERT INTO sf_rate_windows(key,bucket) VALUES(%s,floor(extract(epoch FROM now())/86400)::bigint*24) ON CONFLICT(key,bucket) DO UPDATE SET count=sf_rate_windows.count+1 RETURNING count",(marker,)).fetchone()
    if count>=active or row['count']>maximum:raise HTTPException(429,'A capacidade de demonstrações foi atingida. Uma sessão válida ainda pode ser retomada.',headers={'Retry-After':'3600'})
