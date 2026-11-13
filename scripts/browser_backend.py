"""QA-only provider double. Never load in the local portfolio's real backend."""
import os, json, sys
from pathlib import Path
from io import BytesIO
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
assert os.getenv('SF_QA_MODE')=='true'
assert os.getenv('PGDATABASE')=='ai_request_classifier_test' or os.getenv('GITHUB_ACTIONS')=='true'
from app.main import app
from app import ia
from app.routing import simulate

class Response(BytesIO):
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

def mock_provider(request,timeout):
    assert request.full_url=='https://api.deepseek.com/chat/completions'
    payload=json.loads(request.data)
    data=json.loads(payload['messages'][-1]['content'])
    if data['titulo']=='QA falha de API':
        from urllib.error import HTTPError
        raise HTTPError(request.full_url,503,'Mock unavailable',{},None)
    result=simulate(data['titulo'],data['descricao'])
    content={k:getattr(result,k) for k in ('categoria','impacto','urgencia','justificativa')}
    return Response(json.dumps({'model':'mock-deepseek','choices':[{'finish_reason':'stop','message':{'content':json.dumps(content)}}],'usage':{'prompt_tokens':100,'completion_tokens':50}}).encode())

ia.urlopen=mock_provider

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=int(os.getenv('SF_QA_PORT','8000')),proxy_headers=False)
