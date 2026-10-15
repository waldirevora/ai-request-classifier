from fastapi import FastAPI

from app.routes.solicitacoes import router as solicitacoes_router


app = FastAPI(title="AI Request Classifier")


@app.get("/health")
def verificar_saude():
    return {"status": "ok"}


app.include_router(solicitacoes_router)
