import pytest

from fastapi.testclient import TestClient

from app.database import conectar
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def preparar_banco_teste(monkeypatch):
    monkeypatch.setenv(
        "PGDATABASE",
        "ai_request_classifier_test"
    )

    with conectar() as conn:
        if conn.info.dbname != "ai_request_classifier_test":
            raise RuntimeError(
                "Banco de testes incorreto"
            )

        conn.execute(
            "TRUNCATE TABLE solicitacoes RESTART IDENTITY"
        )


def dados_validos(titulo="Meu computador nao liga"):
    return {
        "titulo": titulo,
        "descricao": "O equipamento nao inicia desde hoje."
    }


def test_health_e_lista_vazia():
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}

    resposta_lista = client.get("/solicitacoes")

    assert resposta_lista.status_code == 200
    assert resposta_lista.json() == []


def test_criar_listar_e_consultar():
    resposta = client.post(
        "/solicitacoes",
        json=dados_validos()
    )

    assert resposta.status_code == 201
    assert resposta.json()["id"] == 1
    assert resposta.json()["status"] == "pendente_classificacao"
    assert "criado_em" in resposta.json()

    lista = client.get("/solicitacoes").json()

    assert len(lista) == 1
    assert client.get("/solicitacoes/1").status_code == 200


def test_validacao_e_registro_inexistente():
    resposta = client.post(
        "/solicitacoes",
        json={"titulo": "Oi", "descricao": "Curta"}
    )

    assert resposta.status_code == 422
    assert client.get("/solicitacoes").json() == []

    assert client.get("/solicitacoes/999").status_code == 404
    assert client.get("/solicitacoes/abc").status_code == 422


def test_atualizar_e_excluir():
    client.post("/solicitacoes", json=dados_validos())

    atualizacao = client.put(
        "/solicitacoes/1",
        json=dados_validos("Problema no carregador")
    )

    assert atualizacao.status_code == 200
    assert atualizacao.json()["titulo"] == "Problema no carregador"

    invalido = client.put(
        "/solicitacoes/1",
        json={"titulo": "Oi", "descricao": "Curta"}
    )

    assert invalido.status_code == 422

    exclusao = client.delete("/solicitacoes/1")

    assert exclusao.status_code == 204
    assert exclusao.content == b""

    assert client.get("/solicitacoes/1").status_code == 404


def test_id_nao_reutilizado_apos_exclusao():
    client.post("/solicitacoes", json=dados_validos())

    client.post(
        "/solicitacoes",
        json=dados_validos("Acesso ao financeiro")
    )

    assert client.delete("/solicitacoes/1").status_code == 204

    resposta = client.post(
        "/solicitacoes",
        json=dados_validos("Problema no carregador")
    )

    assert resposta.status_code == 201
    assert resposta.json()["id"] == 3
    