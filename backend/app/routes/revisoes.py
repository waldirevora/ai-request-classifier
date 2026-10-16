"""Fila de revisão humana e decisões persistidas no PostgreSQL.

Sem autenticação: SOMENTE ambiente local, até implementar controle de acesso.
"""
from fastapi import APIRouter, HTTPException

from app.classificacao import Impacto, Urgencia, calcular_prioridade
from app.database import conectar
from app.schemas_revisao import RevisaoEntrada
from app.triagem import CAMPOS_RETORNO

router = APIRouter(prefix="/revisoes", tags=["Revisão humana"])

PENDENTES = ("aguardando_revisao", "classificacao_falhou", "pendente_classificacao")


@router.get("/pendentes")
def listar_pendentes():
    """Inclui falhas da IA para permitir classificação manual pelo analista."""
    with conectar() as conn:
        return conn.execute(
            f"""SELECT {CAMPOS_RETORNO} FROM solicitacoes
                WHERE status IN (%s, %s, %s) ORDER BY criado_em, id""",
            PENDENTES,
        ).fetchall()


@router.get("/concluidas")
def listar_concluidas():
    with conectar() as conn:
        return conn.execute(
            f"""SELECT {CAMPOS_RETORNO} FROM solicitacoes
                WHERE status = %s ORDER BY revisado_em DESC, id DESC""",
            ("revisada",),
        ).fetchall()


@router.post("/{solicitacao_id}")
def registrar_revisao(solicitacao_id: int, dados: RevisaoEntrada):
    """Bloqueio FOR UPDATE impede decisões concorrentes sobre o mesmo registro."""
    with conectar() as conn:
        registro = conn.execute(
            """SELECT status, categoria_sugerida, impacto_sugerido, urgencia_sugerida
               FROM solicitacoes WHERE id = %s FOR UPDATE""",
            (solicitacao_id,),
        ).fetchone()
        if registro is None:
            raise HTTPException(status_code=404, detail="Solicitação não encontrada")
        if registro["status"] not in PENDENTES:
            raise HTTPException(status_code=409, detail="Solicitação já revisada")

        if dados.decisao == "aceitar":
            if registro["status"] != "aguardando_revisao":
                raise HTTPException(
                    status_code=409,
                    detail="Não existe sugestão válida para aceitar; faça correção manual",
                )
            if not all((registro["categoria_sugerida"],
                        registro["impacto_sugerido"], registro["urgencia_sugerida"])):
                raise HTTPException(status_code=409, detail="Sugestão incompleta")
            categoria = registro["categoria_sugerida"]
            impacto = registro["impacto_sugerido"]
            urgencia = registro["urgencia_sugerida"]
        else:
            categoria = dados.categoria.value
            impacto = dados.impacto.value
            urgencia = dados.urgencia.value

        prioridade = calcular_prioridade(Impacto(impacto), Urgencia(urgencia)).value
        return conn.execute(
            f"""UPDATE solicitacoes SET
                    categoria_final = %s,
                    impacto_final = %s,
                    urgencia_final = %s,
                    prioridade_final = %s,
                    decisao_revisao = %s,
                    observacao_revisao = %s,
                    revisado_em = CURRENT_TIMESTAMP,
                    status = 'revisada'
                WHERE id = %s AND status IN (%s, %s, %s)
                RETURNING {CAMPOS_RETORNO}""",
            (categoria, impacto, urgencia, prioridade, dados.decisao,
             dados.observacao, solicitacao_id, *PENDENTES),
        ).fetchone()
