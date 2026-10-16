"""Testes integrados P14: somente no PostgreSQL isolado; sem chamadas DeepSeek."""
import pytest
from fastapi.testclient import TestClient

from app.database import conectar
from app.main import app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("PGDATABASE", "ai_request_classifier_test")
    monkeypatch.setenv("AI_ENABLED", "false")
    with conectar() as conn:
        if conn.info.dbname != "ai_request_classifier_test":
            raise RuntimeError("BLOQUEADO: conexão não é o banco de testes")
        conn.execute("TRUNCATE TABLE solicitacoes RESTART IDENTITY")
    return TestClient(app)


def criar(client):
    r = client.post("/solicitacoes", json={
        "titulo": "Sistema indisponível",
        "descricao": "Toda a equipe sem acesso ao sistema durante o expediente.",
    })
    assert r.status_code == 201
    return r.json()["id"]


def simular_sugestao(id_solicitacao):
    with conectar() as conn:
        conn.execute("""UPDATE solicitacoes SET status = 'aguardando_revisao',
                        categoria_sugerida = 'suporte_ti', impacto_sugerido = 'equipe',
                        urgencia_sugerida = 'alta', prioridade_sugerida = 'alta'
                        WHERE id = %s""", (id_solicitacao,))


def test_aceitar_sugestao_e_persistir_campos_finais(client):
    ident = criar(client)
    simular_sugestao(ident)
    resp = client.post(f"/revisoes/{ident}", json={"decisao": "aceitar"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "revisada"
    assert resp.json()["categoria_final"] == "suporte_ti"
    assert resp.json()["prioridade_final"] == "alta"
    assert resp.json()["decisao_revisao"] == "aceitar"
    assert client.get(f"/solicitacoes/{ident}").json()["revisado_em"] is not None


def test_corrigir_com_prioridade_do_backend(client):
    ident = criar(client)
    simular_sugestao(ident)
    resp = client.post(f"/revisoes/{ident}", json={
        "decisao": "corrigir", "categoria": "acessos_permissoes",
        "impacto": "individual", "urgencia": "alta",
        "observacao": "O problema é de permissão individual, não de TI.",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["categoria_final"] == "acessos_permissoes"
    assert body["prioridade_final"] == "media"
    assert body["categoria_sugerida"] == "suporte_ti"  # preserva histórico da IA


def test_falha_de_ia_permite_correcao_manual(client):
    ident = criar(client)
    with conectar() as conn:
        conn.execute("UPDATE solicitacoes SET status='classificacao_falhou' WHERE id=%s", (ident,))
    resp = client.post(f"/revisoes/{ident}", json={
        "decisao": "corrigir", "categoria": "outros",
        "impacto": "individual", "urgencia": "baixa",
        "observacao": "Registro tratado manualmente após falha da IA.",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "revisada"


def test_aceitar_sem_sugestao_e_bloqueado(client):
    ident = criar(client)
    assert client.post(f"/revisoes/{ident}", json={"decisao": "aceitar"}).status_code == 409


def test_revisao_duplicada_e_bloqueada(client):
    ident = criar(client)
    simular_sugestao(ident)
    assert client.post(f"/revisoes/{ident}", json={"decisao": "aceitar"}).status_code == 200
    assert client.post(f"/revisoes/{ident}", json={"decisao": "aceitar"}).status_code == 409


def test_campos_invalidos_sao_rejeitados(client):
    ident = criar(client)
    assert client.post(f"/revisoes/{ident}", json={
        "decisao": "corrigir", "categoria": "inventada",
        "impacto": "equipe", "urgencia": "alta", "observacao": "Justificativa suficiente",
    }).status_code == 422
    assert client.post(f"/revisoes/{ident}", json={
        "decisao": "corrigir", "categoria": "suporte_ti", "impacto": "equipe",
        "urgencia": "alta", "observacao": "curto",
    }).status_code == 422


def test_fila_e_historico(client):
    ident = criar(client)
    ids = [x["id"] for x in client.get("/revisoes/pendentes").json()]
    assert ident in ids
    assert client.get("/revisoes/concluidas").json() == []
    simular_sugestao(ident)
    client.post(f"/revisoes/{ident}", json={"decisao": "aceitar"})
    assert ident not in [x["id"] for x in client.get("/revisoes/pendentes").json()]
    assert ident in [x["id"] for x in client.get("/revisoes/concluidas").json()]


def test_registro_inexistente(client):
    assert client.post("/revisoes/999999", json={"decisao": "aceitar"}).status_code == 404
