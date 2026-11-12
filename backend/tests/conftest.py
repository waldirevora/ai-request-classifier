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


def clean_test_database(conn):
    from psycopg import sql
    assert conn.info.dbname == "ai_request_classifier_test"
    assert conn.execute("SELECT current_user AS name").fetchone()["name"] == "ai_classifier_test"
    names = [r["tablename"] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND (tablename='solicitacoes' OR tablename LIKE 'sf_%') AND tablename <> 'sf_schema_versions'").fetchall()]
    conn.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY").format(sql.SQL(',').join(sql.Identifier(n) for n in names)))
