"""Ponto de entrada FastAPI do SolicitaFlow."""
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from app.identity import legacy_guard
from app.portals import router as portals_router
from app.operations import router as operations_router
from app.laboratory import router as laboratory_router

from app.routes.revisoes import router as revisoes_router
from app.routes.solicitacoes import router as solicitacoes_router

app = FastAPI(title="SolicitaFlow", version="2.4.0")
app.include_router(portals_router)
app.include_router(operations_router)
app.include_router(laboratory_router)
app.include_router(solicitacoes_router, dependencies=[Depends(legacy_guard)])
app.include_router(revisoes_router, dependencies=[Depends(legacy_guard)])


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}


@app.get("/configuracao", tags=["Sistema"])
def configuracao():
    """Estado efetivo da IA para a interface local, sem retornar segredos."""
    import os
    from app.triagem import ia_ativa
    return {
        "ai_enabled": ia_ativa(),
        "ai_configured": bool(os.getenv("DEEPSEEK_API_KEY", "").strip()),
        "ai_model": os.getenv("AI_MODEL", "deepseek-flash").strip() or "deepseek-flash",
    }


@app.middleware("http")
async def local_origin_guard(request: Request, call_next):
    origin=request.headers.get("origin")
    if request.method not in ("GET","HEAD","OPTIONS") and origin and origin not in ("http://localhost:5173","http://127.0.0.1:5173","http://localhost:8000","http://127.0.0.1:8000"):
        return JSONResponse(status_code=403,content={"detail":"Origem não autorizada"})
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="same-origin"
    response.headers["Cache-Control"]="no-store"
    return response
