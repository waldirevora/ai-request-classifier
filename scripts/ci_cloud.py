"""CI-only fresh schema + encrypted backup/restore. Never opens a local or provider DB."""
from pathlib import Path
import os,subprocess,sys,tempfile
import psycopg
from psycopg import sql
from cloud_schema import apply,privileges
from cloud_ops import backup,restore
assert os.getenv('GITHUB_ACTIONS')=='true'
assert os.getenv('PGDATABASE')=='postgres' and os.getenv('PGUSER')=='postgres' and os.getenv('PGHOST')=='127.0.0.1'
with psycopg.connect(autocommit=True) as conn:
    conn.execute('CREATE ROLE ai_classifier_cleanup LOGIN')
    for db in ('solicitaflow_cloud_test','solicitaflow_restore_test'):
        assert not conn.execute('SELECT 1 FROM pg_database WHERE datname=%s',(db,)).fetchone()
        conn.execute(sql.SQL('CREATE DATABASE {} OWNER ai_classifier_owner').format(sql.Identifier(db)))
        conn.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(db)))
os.environ['PGDATABASE']='solicitaflow_cloud_test'
with psycopg.connect(autocommit=True) as conn:
    print(apply(conn,'ai_classifier_owner'));print(apply(conn,'ai_classifier_owner'));privileges(conn,'ai_classifier_owner')
    conn.execute('SET ROLE ai_classifier_owner')
    conn.execute("INSERT INTO solicitacoes(titulo,descricao) VALUES('Backup fictício','Registro fictício para validar recuperação de dados.')")
    conn.execute('RESET ROLE')
    assert not conn.execute("SELECT has_table_privilege('ai_classifier_app','solicitacoes','TRUNCATE')").fetchone()[0]
    assert not conn.execute("SELECT has_table_privilege('ai_classifier_app','sf_ai_attempts','DELETE')").fetchone()[0]
    assert not conn.execute("SELECT has_table_privilege('ai_classifier_app','sf_events','UPDATE')").fetchone()[0]
# Exercise the actual limited cleanup role; a fully privileged test role would hide missing row-lock rights.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.retention import cleanup
from psycopg.rows import dict_row
with psycopg.connect(autocommit=False,row_factory=dict_row) as conn:
    conn.execute('SET ROLE ai_classifier_cleanup')
    assert cleanup(conn)=={'redacted':0,'purged':0}
with tempfile.TemporaryDirectory() as temp:
    stem=backup(temp)
    os.environ['PGDATABASE']='solicitaflow_restore_test'
    print('Encrypted restore:',restore(stem))
print('Cloud migrations001–007, rerun, ownership, minimum privileges and encrypted restore verified.')
