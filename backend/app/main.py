"""Ponto de entrada FastAPI do AI Request Classifier."""
from fastapi import FastAPI

from app.routes.revisoes import router as revisoes_router
from app.routes.solicitacoes import router as solicitacoes_router

app = FastAPI(title="AI Request Classifier", version="0.14.0")
app.include_router(solicitacoes_router)
app.include_router(revisoes_router)


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
