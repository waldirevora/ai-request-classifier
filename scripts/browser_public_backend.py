"""Loopback HTTPS QA ONLY. Cannot connect to the primary or a provider database."""
from pathlib import Path
import os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
assert os.getenv('SF_QA_MODE')=='true' and os.getenv('PGDATABASE')=='ai_request_classifier_test'
assert os.getenv('PGHOST') in ('127.0.0.1','localhost')
from browser_backend import mock_provider
from app import ia
from app.cloud import create_public_app
from app.deployment import PublicSettings
os.environ['SF_ENV']='production'
os.environ['SF_CLEANUP_USER']=os.environ['PGUSER'];os.environ['SF_CLEANUP_PASSWORD']=os.environ['PGPASSWORD']
ia.urlopen=mock_provider
app=create_public_app(PublicSettings('https://127.0.0.1:18443',maintenance=False,require_tls=False))
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=18443,proxy_headers=False,ssl_keyfile=os.environ['SF_QA_TLS_KEY'],ssl_certfile=os.environ['SF_QA_TLS_CERT'])
