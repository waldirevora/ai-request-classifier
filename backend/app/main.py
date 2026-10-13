from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Ai Request Classifier")

solicitacoes = []


class SolicitacaoEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=10, max_length=2000)


@app.get("/health")
def verificar_saude():
    return{"status": "ok"}

@app.post("/solicitacoes", status_code=201)
def criar_solicitacao(dados: SolicitacaoEntrada):
    nova_solicitacao = {
        "id": len(solicitacoes) + 1,
        "titulo": dados.titulo,
        "descricao": dados.descricao,
        "status": "pendente_classificacao"
    }

    solicitacoes.append(nova_solicitacao)

    return nova_solicitacao
