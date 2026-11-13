"""One HTTPS origin: compiled React + scoped API. Starts in maintenance by default."""
import asyncio,hashlib,hmac,logging,os
from pathlib import Path
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse,HTMLResponse
from starlette.staticfiles import StaticFiles
from app.deployment import PublicSettings,client_network

MAINTENANCE='''<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SolicitaFlow · Preparação</title></head><body><main><h1>SolicitaFlow</h1><p>A demonstração está em validação. Volte em breve.</p><p>Nenhuma solicitação ou análise de IA é recebida nesta página.</p></main></body></html>'''
SAFE=('GET','HEAD','OPTIONS')

class Security:
    def __init__(self,app,settings):self.app=app;self.settings=settings
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        settings=self.settings;headers=dict(scope['headers']);path=scope['path'];method=scope['method']
        auth=headers.get(b'authorization',b'').decode('latin1')
        operator=bool(settings.maintenance_token) and hmac.compare_digest(auth.encode('utf-8'),('Bearer '+settings.maintenance_token).encode('utf-8'))
        health=path in ('/health','/ready','/api/health','/api/ready')
        response_started=False
        async def secured(message):
            nonlocal response_started
            if message['type']=='http.response.start':
                response_started=True
                extra={b'x-content-type-options':b'nosniff',b'x-frame-options':b'DENY',b'referrer-policy':b'same-origin',b'strict-transport-security':b'max-age=31536000',b'permissions-policy':b'camera=(), microphone=(), geolocation=(), payment=()',b'content-security-policy':b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"}
                if path.startswith('/assets/'):extra[b'cache-control']=b'public, max-age=31536000, immutable'
                else:extra[b'cache-control']=b'no-store'
                message['headers']=[(k,v) for k,v in message.get('headers',[]) if k.lower() not in extra]+list(extra.items())
            await send(message)
        async def deny(status,detail):
            response=JSONResponse({'detail':detail},status_code=status,headers={'Retry-After':'30'} if status==503 else None)
            await response(scope,receive,secured)
        if path in ('/ready','/api/ready') and not operator:return await deny(404,'Recurso indisponível')
        expected=settings.origin.split('://',1)[1]
        if not health and headers.get(b'host',b'').decode('latin1').lower()!=expected.lower():return await deny(400,'Host não autorizado')
        if settings.maintenance and not operator and not health:
            return await HTMLResponse(MAINTENANCE,status_code=503,headers={'Retry-After':'60'})(scope,receive,secured) if not path.startswith('/api') else await deny(503,'A demonstração está em validação.')
        if path.startswith('/api/'):
            if path in ('/api/v2/login','/api/docs','/api/openapi.json','/api/redoc') or path.startswith(('/api/solicitacoes','/api/revisoes')):return await deny(404,'Recurso indisponível')
            if path=='/api/v2/session' and headers.get(b'x-solicitaflow-context')!=b'lab':return await deny(401,'Entre para continuar')
            if not health and headers.get(b'x-solicitaflow-context')!=b'lab':return await deny(403,'Use o laboratório fictício')
        if method not in SAFE:
            if headers.get(b'origin',b'').decode('latin1')!=settings.origin or headers.get(b'sec-fetch-site',b'same-origin') not in (b'same-origin',b'none'):
                return await deny(403,'Origem não autorizada')
            if headers.get(b'content-type',b'').split(b';',1)[0]!=b'application/json':return await deny(415,'Envie conteúdo JSON')
            chunks=[];size=0
            try:
                async with asyncio.timeout(10):
                    while True:
                        message=await receive()
                        if message['type']=='http.disconnect':return
                        chunk=message.get('body',b'');size+=len(chunk)
                        if size>32768:return await deny(413,'Solicitação maior que o limite permitido')
                        chunks.append(chunk)
                        if not message.get('more_body',False):break
            except TimeoutError:return await deny(408,'Tempo de envio excedido')
            original=receive;delivered=False
            async def replay():
                nonlocal delivered
                if not delivered:delivered=True;return {'type':'http.request','body':b''.join(chunks),'more_body':False}
                return await original()
            receive=replay
        scope=dict(scope);scope['state']=dict(scope.get('state',{}));scope['state']['transport_peer']=(scope.get('client') or ('unknown',0))[0];scope['client']=(client_network(scope,settings),0)
        try:
            if path.startswith('/api/') and not health:
                from app.database import conectar
                from app.identity import rate_limit
                with conectar() as conn:allowed=rate_limit(conn,'public-http:'+scope['client'][0],1200)
                if not allowed:return await deny(429,'Muitas operações nesta rede. Aguarde a próxima hora.')
            return await self.app(scope,receive,secured)
        except Exception as error:
            logging.getLogger('solicitaflow').warning('request_unavailable type=%s sqlstate=%s',type(error).__name__,getattr(error,'sqlstate','-'))
            if response_started:return
            return await deny(503,'Serviço temporariamente indisponível. O pedido pode ter sido salvo; consulte antes de reenviar.')

class PublicFiles(StaticFiles):
    async def get_response(self,path,scope):
        if any(part.startswith('.') for part in path.split('/')):return JSONResponse({'detail':'Recurso indisponível'},404)
        return await super().get_response(path,scope)


def readiness(settings):
    try:
        from app.database import conectar
        with conectar() as conn:
            row=conn.execute("SELECT current_user AS role,current_setting('server_version_num')::int/10000 AS version").fetchone()
            if row['version']!=18 or (settings.require_tls and (not conn.pgconn.ssl_in_use or row['role']!='ai_classifier_app')):raise ValueError('Database identity')
            versions={v['version']:v['sha256'] for v in conn.execute('SELECT version,sha256 FROM sf_schema_versions').fetchall()}
            for file in (Path(__file__).resolve().parents[1]/'sql').glob('00[1-7]_*.sql'):
                if versions.get(file.name)!=hashlib.sha256(file.read_bytes()).hexdigest():raise ValueError('Schema mismatch')
            if conn.execute("SELECT count(*) AS n FROM information_schema.columns WHERE table_schema='public' AND table_name='solicitacoes'").fetchone()['n']!=22:raise ValueError('Columns')
            if settings.require_tls and conn.execute("SELECT has_table_privilege(current_user,'solicitacoes','TRUNCATE') AS bad").fetchone()['bad']:raise ValueError('Runtime privileges')
        return JSONResponse({'status':'ready'})
    except Exception:return JSONResponse({'status':'unavailable'},503,headers={'Retry-After':'15'})


def create_public_app(settings=None):
    settings=settings or PublicSettings.from_env()
    if not (settings.dist/'index.html').is_file():raise ValueError('Build frontend before starting the public service')
    from app.main import create_api
    outer=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
    @outer.get('/health')
    def health():return {'status':'ok'}
    @outer.get('/ready')
    def ready():return readiness(settings)
    api=create_api(public=True)
    async def api_failure(request,error):
        logging.getLogger('solicitaflow').warning('api_unavailable type=%s sqlstate=%s',type(error).__name__,getattr(error,'sqlstate','-'))
        return JSONResponse({'detail':'Serviço temporariamente indisponível. Consulte seu pedido antes de reenviar.'},503,headers={'Retry-After':'30'})
    api.add_exception_handler(Exception,api_failure)
    @api.get('/ready')
    def api_ready():return readiness(settings)
    @outer.get('/')
    def index():
        content=(settings.dist/'index.html').read_text().replace('<html lang="pt-BR">','<html lang="pt-BR" data-public-demo="true">',1)
        return HTMLResponse(content)
    @outer.get('/_operator/status')
    def operator_status(request:Request):
        if not settings.maintenance:return JSONResponse({'detail':'Recurso indisponível'},404)
        return {'release':os.getenv('RENDER_GIT_COMMIT','development'),'ready':readiness(settings).status_code==200,'network_fingerprint':hashlib.sha256(request.client.host.encode()).hexdigest(),'transport_peer':request.state.transport_peer,'cf_present':bool(request.headers.get('CF-Connecting-IP'))}
    outer.mount('/api',api)
    outer.mount('/',PublicFiles(directory=settings.dist,html=True))
    outer.add_middleware(Security,settings=settings)
    return outer
