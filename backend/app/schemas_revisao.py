"""Contrato HTTP da revisão humana; Pydantic valida antes de acessar SQL."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.classificacao import Categoria, Impacto, Urgencia


class RevisaoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decisao: Literal["aceitar", "corrigir"]
    categoria: Categoria | None = None
    impacto: Impacto | None = None
    urgencia: Urgencia | None = None
    observacao: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validar_decisao(self):
        if self.observacao is not None:
            self.observacao = self.observacao.strip()
        if self.decisao == "aceitar":
            if any(v is not None for v in (self.categoria, self.impacto, self.urgencia)):
                raise ValueError("Aceitar não permite alterar a classificação")
        else:
            if any(v is None for v in (self.categoria, self.impacto, self.urgencia)):
                raise ValueError("Correção exige categoria, impacto e urgência")
            if not self.observacao or len(self.observacao) < 10:
                raise ValueError("Correção exige observação com pelo menos 10 caracteres")
        return self
