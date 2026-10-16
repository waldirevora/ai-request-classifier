"""CRUD de solicitações. O POST aciona IA automaticamente quando habilitada."""
from fastapi import APIRouter, HTTPException, Response, status

from app.database import conectar
from app.schemas import SolicitacaoEntrada
from app.triagem import CAMPOS_RETORNO, processar_solicitacao

router = APIRouter(prefix="/solicitacoes", tags=["Solicitações"])


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_solicitacao(dados: SolicitacaoEntrada):
    # A transação é confirmada ANTES da chamada externa à IA.
    with conectar() as conn:
        registro = conn.execute(
            f"""INSERT INTO solicitacoes (titulo, descricao)
                VALUES (%s, %s) RETURNING {CAMPOS_RETORNO}""",
            (dados.titulo, dados.descricao),
        ).fetchone()
    # Com a IA ativa, a chamada acontece automaticamente; não há botão manual.
    return processar_solicitacao(registro)


@router.get("")
def listar_solicitacoes():
    with conectar() as conn:
        return conn.execute(
            f"SELECT {CAMPOS_RETORNO} FROM solicitacoes ORDER BY id"
        ).fetchall()


@router.get("/{id_solicitacao}")
def obter_solicitacao(id_solicitacao: int):
    with conectar() as conn:
        registro = conn.execute(
            f"SELECT {CAMPOS_RETORNO} FROM solicitacoes WHERE id = %s",
            (id_solicitacao,),
        ).fetchone()
    if registro is None:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    return registro


@router.put("/{id_solicitacao}")
def atualizar_solicitacao(id_solicitacao: int, dados: SolicitacaoEntrada):
    with conectar() as conn:
        registro = conn.execute(
            f"""UPDATE solicitacoes SET titulo = %s, descricao = %s
                WHERE id = %s RETURNING {CAMPOS_RETORNO}""",
            (dados.titulo, dados.descricao, id_solicitacao),
        ).fetchone()
    if registro is None:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    # P13: atualizar um registro existente não gera nova classificação automática.
    return registro


@router.delete("/{id_solicitacao}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_solicitacao(id_solicitacao: int):
    with conectar() as conn:
        registro = conn.execute(
            "DELETE FROM solicitacoes WHERE id = %s RETURNING id",
            (id_solicitacao,),
        ).fetchone()
    if registro is None:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
