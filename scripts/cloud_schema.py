"""Fresh dedicated cloud DB only. Uses unchanged official SQL001–007 and checksums."""
from pathlib import Path
import hashlib,re
import psycopg
from psycopg import sql

ROOT=Path(__file__).resolve().parents[1]
DATABASES=('solicitaflow_demo','solicitaflow_cloud_test','solicitaflow_restore_test')

def apply(conn,owner):
    if conn.info.dbname not in DATABASES:raise ValueError('Dedicated cloud database required')
    if conn.execute("SELECT current_setting('server_version_num')::int/10000").fetchone()[0]!=18:raise ValueError('PostgreSQL18 required')
    conn.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(owner)))
    conn.execute('SELECT pg_advisory_lock(821422)')
    try:
        tables={x[0] for x in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()}
        if tables and 'sf_schema_versions' not in tables:raise ValueError('Unexpected pre-existing objects; no migration applied')
        conn.execute('CREATE TABLE IF NOT EXISTS sf_schema_versions(version text PRIMARY KEY,sha256 text NOT NULL,applied_at timestamptz NOT NULL DEFAULT now())')
        old=dict(conn.execute('SELECT version,sha256 FROM sf_schema_versions').fetchall())
        files=sorted((ROOT/'backend/sql').glob('00[1-7]_*.sql'))
        if len(files)!=7:raise ValueError('Seven official migration files required')
        if old and any(f.name not in old for f in files[:len(old)]):raise ValueError('Non-contiguous migration ledger')
        if 'solicitacoes' in tables and files[0].name not in old:raise ValueError('Untracked existing schema; refusing adoption')
        for file in files:
            digest=hashlib.sha256(file.read_bytes()).hexdigest()
            if file.name in old:
                if old[file.name]!=digest:raise ValueError('Applied migration checksum changed')
                continue
            body=file.read_text()
            if re.search(r'(?im)^BEGIN\s*;',body):
                prefix,tail=body.rsplit('COMMIT;',1);conn.execute(prefix)
            else:
                conn.execute('BEGIN');conn.execute(body);tail=''
            try:
                n=conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='solicitacoes'").fetchone()[0]
                expected=5 if file.name.startswith('001') else 15 if file.name.startswith('002') else 22
                if n!=expected:raise ValueError('Unexpected original column count')
                conn.execute('INSERT INTO sf_schema_versions(version,sha256) VALUES(%s,%s)',(file.name,digest))
                conn.execute('COMMIT;'+tail)
            except Exception:
                conn.execute('ROLLBACK');raise
        owners=conn.execute("SELECT DISTINCT tableowner FROM pg_tables WHERE schemaname='public'").fetchall()
        if owners!=[(owner,)]:raise ValueError('Unexpected object ownership')
        if conn.execute("SELECT pg_get_serial_sequence('solicitacoes','id')").fetchone()[0]!='public.solicitacoes_id_seq':raise ValueError('Missing identity sequence')
        return {'migrations':7,'original_columns':22,'owner':owner}
    finally:
        conn.execute('SELECT pg_advisory_unlock(821422)');conn.execute('RESET ROLE')


def privileges(conn,owner,app='ai_classifier_app',cleaner='ai_classifier_cleanup'):
    conn.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(owner)))
    try:
        conn.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
        conn.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {},{}').format(sql.Identifier(app),sql.Identifier(cleaner)))
        tables=[x[0] for x in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()]
        for table in tables:
            perms='SELECT' if table=='sf_schema_versions' else 'SELECT,INSERT' if table=='sf_events' else 'SELECT,INSERT,UPDATE' if table in ('sf_ai_attempts','sf_legacy_submissions') else 'SELECT,INSERT,UPDATE,DELETE'
            conn.execute(sql.SQL('GRANT '+perms+' ON {} TO {}').format(sql.Identifier(table),sql.Identifier(app)))
            if table!='sf_schema_versions':conn.execute(sql.SQL('GRANT SELECT,DELETE ON {} TO {}').format(sql.Identifier(table),sql.Identifier(cleaner)))
        conn.execute(sql.SQL('GRANT UPDATE ON solicitacoes,sf_cases TO {}').format(sql.Identifier(cleaner)))
        conn.execute(sql.SQL('GRANT INSERT ON sf_rate_windows TO {}').format(sql.Identifier(cleaner)))
        conn.execute(sql.SQL('GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO {}').format(sql.Identifier(app)))
        conn.execute(sql.SQL('REVOKE DELETE,TRUNCATE ON sf_ai_attempts,sf_legacy_submissions FROM {}').format(sql.Identifier(app)))
        conn.execute(sql.SQL('REVOKE UPDATE,DELETE,TRUNCATE ON sf_events FROM {}').format(sql.Identifier(app)))
    finally:conn.execute('RESET ROLE')
