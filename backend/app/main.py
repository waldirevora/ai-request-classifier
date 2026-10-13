from fastapi import FastAPI

app = FastAPI(title="Ai Request Classifier")


@app.get("/health")
def verificar_saude():
    return{"status": "ok"}
