from pydantic import BaseModel, Field


class SolicitacaoEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=10, max_length=2000)
    