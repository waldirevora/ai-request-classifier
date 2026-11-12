"""Additive, checksum-tracked SQL runner. Never runs legacy migrate.py.

Run using the backend venv; connection supplied by libpq environment.
Migration files own their BEGIN/COMMIT. Ledger insert is inside that transaction.
"""
from pathlib import Path
import hashlib, sys
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]

def migrate(conn, owner):
    assert conn.info.dbname in ('ai_request_classifier', 'ai_request_classifier_test')
    assert conn.execute("SELECT current_setting('server_version_num')::int/10000").fetchone()[0] == 18
    conn.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(owner)))
    conn.execute('SELECT pg_advisory_lock(821422)')
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS sf_schema_versions(version text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())')
        for file in sorted((ROOT/'backend/sql').glob('0[0-9][4-9]_*.sql')):
            digest=hashlib.sha256(file.read_bytes()).hexdigest()
            old=conn.execute('SELECT sha256 FROM sf_schema_versions WHERE version=%s',(file.name,)).fetchone()
            if old:
                if old[0]!=digest: raise RuntimeError('Applied migration checksum changed: '+file.name)
                continue
            body=file.read_text()
            assert body.strip().startswith('BEGIN;') and body.strip().endswith('COMMIT;')
            # Preserve the migration transaction; add only its ledger insert before COMMIT.
            prefix, end = body.rsplit('COMMIT;',1)
            with conn.cursor() as cur:
                cur.execute(prefix)
                cur.execute('INSERT INTO sf_schema_versions(version,sha256) VALUES(%s,%s)',(file.name,digest))
                cur.execute('COMMIT;'+end)
            print(conn.info.dbname, file.name, 'applied')
    finally:
        conn.execute('SELECT pg_advisory_unlock(821422)')

if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('ai_classifier_owner','ai_classifier_test'):
        raise SystemExit('Usage: migrate_v2.py ai_classifier_owner|ai_classifier_test (libpq env)')
    with psycopg.connect(autocommit=True) as connection: migrate(connection,sys.argv[1])
