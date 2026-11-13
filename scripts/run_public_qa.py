"""Disposable HTTPS browser fixture. Only the isolated local/CI test DB is accepted."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import argparse,ipaddress,os,subprocess,sys,tempfile,time,ssl,urllib.request
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/tests')]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--axe',type=Path);p.add_argument('--channel');p.add_argument('--browser-python',default=sys.executable);a=p.parse_args()
    assert os.getenv('PGDATABASE')=='ai_request_classifier_test' and os.getenv('PGUSER')=='ai_classifier_test'
    assert os.getenv('PGHOST') in ('127.0.0.1','localhost')
    from app.database import conectar
    from conftest import clean_test_database
    from app.bootstrap import seed
    with conectar() as conn:
        assert not conn.execute("SELECT has_database_privilege(current_user,'ai_request_classifier','CONNECT') AS yes").fetchone()['yes']
        clean_test_database(conn);seed(conn)
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes,serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    with tempfile.TemporaryDirectory() as directory:
        tmp=Path(directory);key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'localhost QA only')])
        cert=x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc)-timedelta(minutes=1)).not_valid_after(datetime.now(timezone.utc)+timedelta(hours=2)).add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).sign(key,hashes.SHA256())
        (tmp/'tls.key').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));(tmp/'tls.key').chmod(0o600)
        (tmp/'tls.crt').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        env=dict(os.environ,AI_ENABLED='true',SF_REAL_AI_ENABLED='true',SF_QA_MODE='true',DEEPSEEK_API_KEY='OFFLINE_TESTS_NO_REAL_KEY',AI_MODEL='deepseek-flash',SF_AI_DAILY_CALLS='10',SF_AI_WORKSPACE_CALLS='2',SF_AI_HOURLY_IP_CALLS='10',SF_AI_DAILY_TOKENS='100000',SF_AI_DAILY_USD='0.05',SF_AI_CONCURRENT='1',SF_QA_TLS_KEY=str(tmp/'tls.key'),SF_QA_TLS_CERT=str(tmp/'tls.crt'))
        a.output.mkdir(parents=True,exist_ok=True)
        with (a.output/'qa-public.log').open('w') as log:
            process=subprocess.Popen([sys.executable,str(ROOT/'scripts/browser_public_backend.py')],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            try:
                for _ in range(50):
                    try:
                        with urllib.request.urlopen('https://127.0.0.1:18443/health',context=ssl._create_unverified_context(),timeout=1) as r:assert r.status==200
                        break
                    except Exception:
                        if process.poll() is not None:raise RuntimeError('QA server failed; inspect private QA log')
                        time.sleep(.2)
                else:raise RuntimeError('QA HTTPS unavailable')
                args=[a.browser_python,str(ROOT/'scripts/browser_public.py'),'--output',str(a.output)]
                if a.axe:args+=['--axe',str(a.axe)]
                if a.channel:args+=['--channel',a.channel]
                subprocess.run(args,cwd=ROOT,check=True)
            finally:process.terminate();process.wait(timeout=30)
if __name__=='__main__':main()
