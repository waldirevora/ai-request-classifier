"""Provision an EMPTY ephemeral GitHub Actions PostgreSQL service. Never run locally."""
from pathlib import Path
import os,secrets,hashlib,json
import psycopg
from psycopg import sql
from migrate_v2 import migrate

def main():
    assert os.getenv('GITHUB_ACTIONS')=='true', 'CI-only command'
    assert os.getenv('PGDATABASE')=='postgres' and os.getenv('PGUSER')=='postgres'
    assert os.getenv('PGHOST')=='127.0.0.1'
    root=Path(__file__).resolve().parents[1]
    passwords={role:secrets.token_urlsafe(32) for role in ('ai_classifier_app','ai_classifier_test')}
    with psycopg.connect(autocommit=True) as conn:
        assert conn.execute("SELECT count(*) FROM pg_database WHERE datname IN ('ai_request_classifier','ai_request_classifier_test')").fetchone()[0]==0
        assert conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'ai_classifier_%'").fetchone()[0]==0
        conn.execute('CREATE ROLE ai_classifier_owner NOLOGIN')
        for role,password in passwords.items():
            conn.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role),sql.Literal(password)))
        for name,owner,login in [('ai_request_classifier','ai_classifier_owner','ai_classifier_app'),('ai_request_classifier_test','ai_classifier_test','ai_classifier_test')]:
            conn.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(name),sql.Identifier(owner)))
            conn.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(name)))
            conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(name),sql.Identifier(login)))
    for database,owner in [('ai_request_classifier','ai_classifier_owner'),('ai_request_classifier_test','ai_classifier_test')]:
        with psycopg.connect(dbname=database,autocommit=True) as conn:
            conn.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(owner)))
            for filename in ['001_create_solicitacoes.sql','002_add_classificacao_ia.sql','003_add_revisao_humana.sql']:
                conn.execute((root/'backend/sql'/filename).read_text())
            conn.execute("INSERT INTO solicitacoes(titulo,descricao) VALUES('CI legado fictício','Registro fictício criado antes das migrações aditivas.')")
            before=conn.execute('SELECT row_to_json(s)::text FROM solicitacoes s ORDER BY id').fetchall()
            migrate(conn,owner)
            migrate(conn,owner) # Verify idempotency and applied checksums.
            assert before==conn.execute('SELECT row_to_json(s)::text FROM solicitacoes s ORDER BY id').fetchall()
            conn.execute('RESET ROLE')
            if database=='ai_request_classifier':
                conn.execute('GRANT USAGE ON SCHEMA public TO ai_classifier_app')
                tables=conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename<>'sf_schema_versions'").fetchall()
                for (table,) in tables:
                    grants='SELECT,INSERT' if table=='sf_events' else 'SELECT,INSERT,UPDATE,DELETE'
                    conn.execute(sql.SQL('GRANT '+grants+' ON {} TO ai_classifier_app').format(sql.Identifier(table)))
                conn.execute('GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_classifier_app')
    for value in passwords.values():print('::add-mask::'+value,flush=True)
    with Path(os.environ['GITHUB_ENV']).open('a') as file:
        file.write('PGUSER=ai_classifier_test\nPGDATABASE=ai_request_classifier_test\n')
        file.write('PGPASSWORD='+passwords['ai_classifier_test']+'\n')
        file.write('SF_APP_PASSWORD='+passwords['ai_classifier_app']+'\n')
    print('Ephemeral databases ready; legacy rows preserved; migration rerun verified. Credentials not logged.')

if __name__=='__main__':main()
