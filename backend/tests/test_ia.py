"""Testes da validação JSON, incluindo simulação local (sem consumir API paga)."""
import json
from io import BytesIO

import pytest
from pydantic import ValidationError

from app import ia
from app.ia import ErroClassificacao, RespostaLLM


def test_rejeita_categoria_fora_da_taxonomia():
    with pytest.raises(ValidationError):
        RespostaLLM.model_validate({
            "categoria": "marketing", "impacto": "equipe", "urgencia": "alta",
            "justificativa": "A equipe não consegue operar no horário previsto.",
        })


def test_rejeita_chave_extra_no_json():
    with pytest.raises(ValidationError):
        RespostaLLM.model_validate({
            "categoria": "suporte_ti", "impacto": "equipe", "urgencia": "alta",
            "justificativa": "A equipe não consegue operar no horário previsto.",
            "prioridade": "alta",
        })


def test_chave_ausente_gera_erro_sem_vazar_segredo(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ErroClassificacao, match="configuracao_ausente"):
        ia.classificar_solicitacao("Computador não liga", "Equipamento do escritório sem inicializar.")


def test_classificacao_simulada_usa_prioridade_da_matriz(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "CHAVE_APENAS_PARA_TESTES")

    resposta_llm = {
        "choices": [{"finish_reason": "stop", "message": {"content": json.dumps({
            "categoria": "suporte_ti", "impacto": "equipe", "urgencia": "alta",
            "justificativa": "Equipe bloqueada na atividade principal do expediente.",
        })}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 45},
    }

    class RespostaHTTP(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    def urlopen_simulado(pedido, timeout):
        assert timeout == 12
        assert pedido.full_url == "https://api.deepseek.com/chat/completions"
        assert json.loads(pedido.data)["response_format"] == {"type": "json_object"}
        return RespostaHTTP(json.dumps(resposta_llm).encode("utf-8"))

    monkeypatch.setattr(ia, "urlopen", urlopen_simulado)
    resultado = ia.classificar_solicitacao(
        "Sistema indisponível", "Toda equipe está sem acesso ao sistema.")
    assert resultado.categoria == "suporte_ti"
    assert resultado.prioridade == "alta"
    assert resultado.tokens_entrada == 100
    assert resultado.tokens_saida == 45


def test_resposta_truncada_e_recusada(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "CHAVE_APENAS_PARA_TESTES")

    class RespostaHTTP(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    monkeypatch.setattr(ia, "urlopen", lambda *_args, **_kwargs: RespostaHTTP(
        b'{"choices":[{"finish_reason":"length","message":{"content":"{}"}}]}'
    ))
    with pytest.raises(ErroClassificacao, match="resposta_incompleta"):
        ia.classificar_solicitacao("Falha", "Equipe sem acesso.")
