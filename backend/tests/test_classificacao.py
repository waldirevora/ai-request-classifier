import json
from pathlib import Path

import pytest

from app.classificacao import Categoria, Impacto, Urgencia, calcular_prioridade

CASOS = json.loads(
    (Path(__file__).resolve().parents[1] / "evaluation" / "casos_referencia.json")
    .read_text(encoding="utf-8")
)


@pytest.mark.parametrize("impacto,urgencia,esperada", [
    ("individual", "baixa", "baixa"),
    ("individual", "media", "baixa"),
    ("individual", "alta", "media"),
    ("equipe", "baixa", "baixa"),
    ("equipe", "media", "media"),
    ("equipe", "alta", "alta"),
    ("empresa", "baixa", "media"),
    ("empresa", "media", "alta"),
    ("empresa", "alta", "alta"),
])
def test_matriz(impacto, urgencia, esperada):
    assert calcular_prioridade(Impacto(impacto), Urgencia(urgencia)).value == esperada


def test_conjunto_de_referencia():
    assert len(CASOS) == 10
    assert len({c["id"] for c in CASOS}) == 10
    assert {c["categoria_esperada"] for c in CASOS} == {x.value for x in Categoria}


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_caso_consistente(caso):
    assert 3 <= len(caso["titulo"].strip()) <= 120
    assert 10 <= len(caso["descricao"].strip()) <= 2000
    assert caso["justificativa_esperada"].strip()
    Categoria(caso["categoria_esperada"])
    assert calcular_prioridade(
        Impacto(caso["impacto"]), Urgencia(caso["urgencia"])
    ).value == caso["prioridade_esperada"]
