"""Operator-only migrations and encrypted backups. No secret arguments or public endpoints."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
import psycopg
from psycopg import sql
from cloud_schema import apply,privileges,DATABASES


def snapshot(conn):
    result={}
    for (table,) in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"):
        rows=conn.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} t ORDER BY row_to_json(t)::text').format(sql.Identifier(table))).fetchall()
        result[table]={'rows':len(rows),'sha256':hashlib.sha256(json.dumps(rows).encode()).hexdigest()}
    return result


def binary(directory,name):
    path=str(Path(directory)/name) if directory else name
    version=subprocess.run([path,'--version'],capture_output=True,text=True,check=True).stdout
    if ' 18.' not in version:raise ValueError('PostgreSQL18 client required')
    return path


def backup(directory,pg_bin=''):
    from cryptography.fernet import Fernet
    with psycopg.connect(autocommit=True) as conn:
        if conn.info.dbname not in DATABASES:raise ValueError('Dedicated demonstration database required')
        before=snapshot(conn)
    # stdout is held in memory, never written unencrypted or printed.
    data=subprocess.run([binary(pg_bin,'pg_dump'),'--format=custom','--no-owner','--no-privileges'],capture_output=True,check=True).stdout
    directory=Path(directory).expanduser();directory.mkdir(parents=True,mode=0o700,exist_ok=True);directory.chmod(0o700)
    stem=directory/('solicitaflow-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+os.urandom(3).hex())
    key=Fernet.generate_key()
    for suffix,value in (('.key',key),('.backup.fernet',Fernet(key).encrypt(data)),('.manifest.private',json.dumps(before,indent=2).encode())):
        fd=os.open(str(stem)+suffix,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(value)
    return stem


def restore(stem,pg_bin='',owner='ai_classifier_owner'):
    from cryptography.fernet import Fernet
    with psycopg.connect(autocommit=True) as conn:
        if conn.info.dbname!='solicitaflow_restore_test':raise ValueError('Restore is restricted to the dedicated empty verification database')
        if conn.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public'").fetchone()[0]:raise ValueError('Restore target must be empty; never overwrite')
    data=Fernet(Path(str(stem)+'.key').read_bytes()).decrypt(Path(str(stem)+'.backup.fernet').read_bytes())
    subprocess.run([binary(pg_bin,'pg_restore'),'--dbname='+os.environ['PGDATABASE'],'--no-owner','--no-privileges','--exit-on-error','--single-transaction','--role='+owner],input=data,capture_output=True,check=True)
    with psycopg.connect(autocommit=True) as conn:
        actual=snapshot(conn)
        assert actual==json.loads(Path(str(stem)+'.manifest.private').read_text()),'Restored data differs'
        apply(conn,owner) # verifies all seven unchanged checksums and ownership, no reapplication
    return {'tables':len(actual),'rows':sum(v['rows'] for v in actual.values()),'verified':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['migrate','backup','restore']);p.add_argument('--directory');p.add_argument('--stem');p.add_argument('--pg-bin',default='');args=p.parse_args()
    try:
        if args.action=='migrate':
            with psycopg.connect(autocommit=True) as conn:
                print(apply(conn,'ai_classifier_owner'));privileges(conn,'ai_classifier_owner')
        elif args.action=='backup':print(backup(args.directory,args.pg_bin))
        else:print(restore(args.stem,args.pg_bin))
    except Exception as error:
        # Do not echo database URLs, SQL parameters, dumps or credentials on failures.
        print('Operation failed:',type(error).__name__,file=sys.stderr);raise SystemExit(1)
