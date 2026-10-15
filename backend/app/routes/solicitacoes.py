from fastapi import APIRouter, HTTPException

from app import storage
from app.schemas import SolicitacaoEntrada


router = APIRouter(
    prefix="/solicitacoes",
    tags=["Solicitações"]
)


@router.post("", status_code=201)
def criar_solicitacao(dados: SolicitacaoEntrada):
    nova_solicitacao = {
        "id": next(storage.contador_ids),
        "titulo": dados.titulo,
        "descricao": dados.descricao,
        "status": "pendente_classificacao"
    }

    storage.solicitacoes.append(nova_solicitacao)

    return nova_solicitacao


@router.get("")
def listar_solicitacoes():
    return storage.solicitacoes


@router.get("/{id_solicitacao}")
def detalhar_solicitacao(id_solicitacao: int):
    solicitacao = storage.encontrar_solicitacao(
        id_solicitacao
    )

    if solicitacao is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )

    return solicitacao


@router.put("/{id_solicitacao}")
def atualizar_solicitacao(
    id_solicitacao: int,
    dados: SolicitacaoEntrada
):
    solicitacao = storage.encontrar_solicitacao(
        id_solicitacao
    )

    if solicitacao is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )

    solicitacao["titulo"] = dados.titulo
    solicitacao["descricao"] = dados.descricao

    return solicitacao


@router.delete("/{id_solicitacao}", status_code=204)
def excluir_solicitacao(id_solicitacao: int):
    solicitacao = storage.encontrar_solicitacao(
        id_solicitacao
    )

    if solicitacao is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )

    storage.solicitacoes.remove(solicitacao)
    