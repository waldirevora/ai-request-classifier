"""Testes P13 com PostgreSQL isolado e IA simulada (nenhuma chamada real)."""
import pytest
from fastapi.testclient import TestClient

from app.database import conectar
from app.ia import ErroClassificacao, ResultadoIA
from app.main import app
from app import triagem


@pytest.fixture()
def cliente_teste(monkeypatch):
    monkeypatch.setenv("PGDATABASE", "ai_request_classifier_test")
    monkeypatch.setenv("AI_ENABLED", "true")
    with conectar() as conn:
        if conn.info.dbname != "ai_request_classifier_test":
            raise RuntimeError("BLOQUEADO: conexão não é o banco de testes")
        conn.execute("TRUNCATE TABLE solicitacoes RESTART IDENTITY")
    return TestClient(app)


def test_post_classifica_automaticamente_e_salva(cliente_teste, monkeypatch):
    def fake_ia(titulo, descricao):
        return ResultadoIA("suporte_ti", "equipe", "alta", "alta",
                           "Equipe impedida de acessar a aplicação de trabalho.",
                           "mock-local", 80, 30, 42)

    monkeypatch.setattr(triagem, "classificar_solicitacao", fake_ia)
    resposta = cliente_teste.post("/solicitacoes", json={
        "titulo": "Sistema indisponível",
        "descricao": "Toda a equipe está sem acesso ao sistema de trabalho.",
    })
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "aguardando_revisao"
    assert corpo["categoria_sugerida"] == "suporte_ti"
    assert corpo["prioridade_sugerida"] == "alta"
    with conectar() as conn:
        registro = conn.execute(
            "SELECT status, prioridade_sugerida FROM solicitacoes WHERE id = %s",
            (corpo["id"],),
        ).fetchone()
    assert registro == {"status": "aguardando_revisao", "prioridade_sugerida": "alta"}


def test_post_sobrevive_erro_de_ia(cliente_teste, monkeypatch):
    def fake_erro(*_args):
        raise ErroClassificacao("falha_rede")

    monkeypatch.setattr(triagem, "classificar_solicitacao", fake_erro)
    resposta = cliente_teste.post("/solicitacoes", json={
        "titulo": "Acesso a sistema",
        "descricao": "Preciso acessar o sistema de ponto na empresa.",
    })
    assert resposta.status_code == 201
    registro = resposta.json()
    assert registro["status"] == "classificacao_falhou"
    assert cliente_teste.get(f"/solicitacoes/{registro['id']}").status_code == 200


def test_ia_desabilitada_mantem_pendente(cliente_teste, monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    def nao_deve_chamar(*_args):
        raise AssertionError("IA não deveria ser chamada")
    monkeypatch.setattr(triagem, "classificar_solicitacao", nao_deve_chamar)
    resposta = cliente_teste.post("/solicitacoes", json={
        "titulo": "Solicitação simples",
        "descricao": "Ajuste de preferência não urgente no equipamento.",
    })
    assert resposta.status_code == 201
    assert resposta.json()["status"] == "pendente_classificacao"
