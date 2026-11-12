"""Proteção de custos: testes não chamam o provedor de IA real."""
import pytest
from app import ia


@pytest.fixture(autouse=True)
def bloquear_ia_real(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "CHAVE_FICTICIA_SEM_CREDITOS")

    def rede_bloqueada(*args, **kwargs):
        raise AssertionError("Chamada real de IA bloqueada durante os testes")

    # Cada teste pode substituir este stub por sua própria resposta simulada.
    monkeypatch.setattr(ia, "urlopen", rede_bloqueada)
