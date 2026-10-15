from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from itertools import count


app = FastAPI(title="Ai Request Classifier")

solicitacoes = []
contador_ids = count(1) # contagem comeca do 1 


class SolicitacaoEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=10, max_length=2000)

def encontrar_solicitacao(id_solicitacao: int):
    for solicitacao in solicitacoes:
        if solicitacao["id"] == id_solicitacao:
            return solicitacao

    return None


@app.get("/health")
def verificar_saude():
    return{"status": "ok"}

@app.post("/solicitacoes", status_code=201)
def criar_solicitacao(dados: SolicitacaoEntrada):
    nova_solicitacao = {
        "id": next(contador_ids),
        "titulo": dados.titulo,
        "descricao": dados.descricao,
        "status": "pendente_classificacao"
    }

    solicitacoes.append(nova_solicitacao)

    return nova_solicitacao

@app.get("/solicitacoes")
def lista_solicitacoes():
    return solicitacoes

@app.get("/solicitacoes/{id_solicitacao}")
def detalhar_solicitacao(id_solicitacao: int):
    solicitacao = encontrar_solicitacao(id_solicitacao)

    if solicitacao is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )

    return solicitacao

@app.put("/solicitacoes/{id_solicitacao}")
def actualizar_solicitacao(
    id_solicitacao: int,
    dados: SolicitacaoEntrada
):
    solicitacao = encontrar_solicitacao(id_solicitacao)

    if solicitacao is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )

    solicitacao["titulo"] = dados.titulo
    solicitacao["descricao"] = dados.descricao

    return solicitacao

@app.delete("/solicitacoes/{id_solicitacao}", status_code=204)
def excluir_solicitacao(id_solicitacao: int):
    solicitacao = encontrar_solicitacao(id_solicitacao)

    if solicitacao is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )

    solicitacoes.remove(solicitacao)
