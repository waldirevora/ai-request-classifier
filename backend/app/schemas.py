from pydantic import BaseModel, Field, field_validator


class SolicitacaoEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=10, max_length=2000)

    @field_validator("titulo", "descricao", mode="before")
    @classmethod
    def remover_espacos(cls, valor):
        if isinstance(valor, str):
            return valor.strip()

        return valor
    