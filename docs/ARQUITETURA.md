# Arquitetura | AI Request Classifier

## Problema de negócio

A classificação inicial de solicitações internas pode
exigir análise manual repetitiva e dificultar a
padronização da triagem.

## Objetivo do produto

Receber solicitações e, futuramente, utilizar IA
para sugerir categoria, prioridade e justificativa,
com revisão humana.

## Arquitetura atual

- Python e FastAPI no backend.
- Pydantic para validação.
- APIRouter para organização dos endpoints.
- Armazenamento temporário em memória.
- pytest e TestClient para testes automatizados.

## Responsabilidades dos módulos

- main.py: inicialização da aplicação.
- schemas.py: validação de dados.
- storage.py: armazenamento temporário.
- routes/solicitacoes.py: operações HTTP.
- tests/test_api.py: testes automatizados.

## Limitações atuais

- Sem PostgreSQL.
- Sem IA integrada.
- Sem frontend React.
- Sem autenticação.
- Sem persistência após reinício.

## Próximas evoluções

PostgreSQL, classificação automática por IA,
tratamento de erros e pipeline de revisão humana.
