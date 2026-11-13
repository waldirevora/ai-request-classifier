"""Local API and reusable router factory; production uses app.cloud."""
import os
from fastapi import FastAPI,Depends,Request
from fastapi.responses import JSONResponse
from app.identity import legacy_guard
from app.portals import router as portals_router
from app.operations import router as operations_router
from app.laboratory import router as laboratory_router
from app.presentation import router as presentation_router
from app.routes.revisoes import router as revisoes_router
from app.routes.solicitacoes import router as solicitacoes_router

def create_api(public=False):
    api=FastAPI(title="SolicitaFlow",version="2.6.1",docs_url=None if public else '/docs',redoc_url=None if public else '/redoc',openapi_url=None if public else '/openapi.json')
    api.state.public_demo=public
    for router in (presentation_router,portals_router,operations_router,laboratory_router):api.include_router(router)
    if not public:
        api.include_router(solicitacoes_router,dependencies=[Depends(legacy_guard)])
        api.include_router(revisoes_router,dependencies=[Depends(legacy_guard)])
    @api.get('/health',tags=['Sistema'])
    def health():return {'status':'ok'}
    if not public:
        @api.get('/configuracao',tags=['Sistema'])
        def configuracao():
            from app.triagem import ia_ativa
            return {'ai_enabled':ia_ativa(),'ai_configured':bool(os.getenv('DEEPSEEK_API_KEY','').strip()),'ai_model':os.getenv('AI_MODEL','deepseek-flash').strip() or 'deepseek-flash'}
    if not public:
        @api.middleware("http")
        async def local_origin_guard(request: Request, call_next):
            origin=request.headers.get("origin")
            if os.getenv("PGDATABASE")=="ai_request_classifier_test" and origin=="http://127.0.0.1:5174":origin="http://127.0.0.1:5173"
            if request.method not in ("GET","HEAD","OPTIONS") and origin and origin not in ("http://localhost:5173","http://127.0.0.1:5173","http://localhost:8000","http://127.0.0.1:8000"):
                return JSONResponse(status_code=403,content={"detail":"Origem não autorizada"})
            response=await call_next(request)
            response.headers["X-Content-Type-Options"]="nosniff"
            response.headers["Referrer-Policy"]="same-origin"
            response.headers["Cache-Control"]="no-store"
            return response
    return api

app=create_api()
