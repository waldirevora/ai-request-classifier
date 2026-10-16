"""Orquestra persistência da sugestão de IA após COMMIT do cadastro."""
import logging
import os

from app.database import conectar
from app.ia import ErroClassificacao, classificar_solicitacao

logger = logging.getLogger(__name__)

CAMPOS_RETORNO = """id, titulo, descricao, status, criado_em,
    categoria_sugerida, impacto_sugerido, urgencia_sugerida,
    prioridade_sugerida, justificativa_ia, modelo_ia,
    tokens_entrada, tokens_saida, latencia_ia_ms, classificado_em,
    categoria_final, impacto_final, urgencia_final, prioridade_final,
    decisao_revisao, observacao_revisao, revisado_em"""


def ia_ativa() -> bool:
    return os.getenv("AI_ENABLED", "false").strip().lower() == "true"


def processar_solicitacao(registro: dict) -> dict:
    """Atualiza sugestão em nova transação. Não apaga o registro em falhas da IA."""
    if not ia_ativa():
        return registro  # mantém status pendente_classificacao

    try:
        resultado = classificar_solicitacao(registro["titulo"], registro["descricao"])
        with conectar() as conn:
            registro_atualizado = conn.execute(
                f"""UPDATE solicitacoes SET
                    categoria_sugerida = %s, impacto_sugerido = %s,
                    urgencia_sugerida = %s, prioridade_sugerida = %s,
                    justificativa_ia = %s, modelo_ia = %s,
                    tokens_entrada = %s, tokens_saida = %s,
                    latencia_ia_ms = %s, classificado_em = CURRENT_TIMESTAMP,
                    status = 'aguardando_revisao'
                WHERE id = %s
                RETURNING {CAMPOS_RETORNO}""",
                (resultado.categoria, resultado.impacto, resultado.urgencia,
                 resultado.prioridade, resultado.justificativa, resultado.modelo,
                 resultado.tokens_entrada, resultado.tokens_saida,
                 resultado.latencia_ms, registro["id"]),
            ).fetchone()
        return registro_atualizado or registro
    except ErroClassificacao as exc:
        # Somente códigos genéricos; não registrar título, descrição ou credenciais.
        logger.warning("IA indisponível para solicitação id=%s: %s", registro["id"], exc)
        try:
            with conectar() as conn:
                novo = conn.execute(
                    f"""UPDATE solicitacoes SET status = 'classificacao_falhou'
                        WHERE id = %s RETURNING {CAMPOS_RETORNO}""",
                    (registro["id"],),
                ).fetchone()
            return novo or registro
        except Exception:
            logger.exception("Não foi possível persistir falha da IA para id=%s", registro["id"])
            return registro  # o INSERT original foi confirmado
    except Exception:
        logger.exception("Não foi possível salvar sugestão para id=%s", registro["id"])
        # Tenta sinalizar a falha também quando o UPDATE principal não funcionou.
        try:
            with conectar() as conn:
                novo = conn.execute(
                    f"""UPDATE solicitacoes SET status = 'classificacao_falhou'
                        WHERE id = %s RETURNING {CAMPOS_RETORNO}""",
                    (registro["id"],),
                ).fetchone()
            return novo or registro
        except Exception:
            logger.exception("Falha ao registrar estado de erro para id=%s", registro["id"])
            return registro  # INSERT original já confirmado; pode exigir reconciliação
