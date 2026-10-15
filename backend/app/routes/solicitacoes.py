from fastapi import APIRouter, HTTPException

from app.database import conectar
from app.schemas import SolicitacaoEntrada


router = APIRouter(
    prefix="/solicitacoes",
    tags=["Solicitações"]
)


@router.post("", status_code=201)
def criar_solicitacao(dados: SolicitacaoEntrada):
    with conectar() as conn:
        registro = conn.execute(
            """
            INSERT INTO solicitacoes (titulo, descricao)
            VALUES (%s, %s)
            RETURNING id, titulo, descricao, status, criado_em
            """,
            (dados.titulo, dados.descricao)
        ).fetchone()

    return registro


@router.get("")
def listar_solicitacoes():
    with conectar() as conn:
        registros = conn.execute(
            """
            SELECT id, titulo, descricao, status, criado_em
            FROM solicitacoes
            ORDER BY id
            """
        ).fetchall()

    return registros


@router.get("/{id_solicitacao}")
def detalhar_solicitacao(id_solicitacao: int):
    with conectar() as conn:
        registro = conn.execute(
            """
            SELECT id, titulo, descricao, status, criado_em
            FROM solicitacoes
            WHERE id = %s
            """,
            (id_solicitacao,)
        ).fetchone()

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )

    return registro


@router.put("/{id_solicitacao}")
def atualizar_solicitacao(
    id_solicitacao: int,
    dados: SolicitacaoEntrada
):
    with conectar() as conn:
        registro = conn.execute(
            """
            UPDATE solicitacoes
            SET titulo = %s, descricao = %s
            WHERE id = %s
            RETURNING id, titulo, descricao, status, criado_em
            """,
            (dados.titulo, dados.descricao, id_solicitacao)
        ).fetchone()

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )

    return registro


@router.delete("/{id_solicitacao}", status_code=204)
def excluir_solicitacao(id_solicitacao: int):
    with conectar() as conn:
        registro = conn.execute(
            """
            DELETE FROM solicitacoes
            WHERE id = %s
            RETURNING id
            """,
            (id_solicitacao,)
        ).fetchone()

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitacao nao encontrada"
        )
    