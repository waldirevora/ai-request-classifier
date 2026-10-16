"""P15: testes offline para a métrica de avaliação; não acessam a DeepSeek nem o banco."""
from types import SimpleNamespace

import pytest

from evaluation.avaliar_ia import avaliar_casos, carregar_casos


def classificador_do_esperado(caso):
    return SimpleNamespace(
        categoria=caso["categoria_esperada"], impacto=caso["impacto"],
        urgencia=caso["urgencia"], prioridade=caso["prioridade_esperada"],
        tokens_entrada=100, tokens_saida=20, latencia_ms=500,
    )


def test_referencias_validas():
    assert len(carregar_casos()) == 10


def test_dez_acertos_perfeitos_simulados():
    casos = carregar_casos()
    iterador = iter(casos)
    resultado = avaliar_casos(casos, lambda _t, _d: classificador_do_esperado(next(iterador)))
    assert resultado["total"] == 10
    assert resultado["completos"] == 10
    assert resultado["taxas_percentuais"]["completo"] == 100
    assert resultado["tokens_entrada"] == 1000
    assert resultado["tokens_saida"] == 200
    assert resultado["latencia_media_ms"] == 500


def test_classificacao_incorreta_reduz_metricas():
    caso = carregar_casos()[0]
    resposta = classificador_do_esperado(caso)
    resposta.categoria = "outros"
    resultado = avaliar_casos([caso], lambda _t, _d: resposta)
    assert resultado["taxas_percentuais"]["categoria"] == 0
    assert resultado["taxas_percentuais"]["impacto"] == 100
    assert resultado["completos"] == 0


def test_falha_tecnica_conta_no_denominador():
    caso = carregar_casos()[0]
    def erro(_t, _d):
        raise TimeoutError("simulada")
    resultado = avaliar_casos([caso], erro)
    assert resultado["falhas_api"] == 1
    assert resultado["taxas_percentuais"]["completo"] == 0
    assert resultado["latencia_media_ms"] is None


def test_ids_duplicados_rejeitados(tmp_path):
    import json
    caso = carregar_casos()[0]
    arquivo = tmp_path / "duplicados.json"
    arquivo.write_text(json.dumps([caso, caso]), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        carregar_casos(arquivo)
