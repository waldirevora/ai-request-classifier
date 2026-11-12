"""Comprova o bloqueio mesmo quando um teste ativa o fluxo de IA."""
import pytest
from app.ia import classificar_solicitacao


def test_provedor_real_bloqueado_mesmo_com_ia_ativada(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    with pytest.raises(AssertionError, match="Chamada real de IA bloqueada"):
        classificar_solicitacao(
            "Teste fictício sem rede",
            "Descrição sintética que nunca deve alcançar o provedor real.",
        )
