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


## Camada de persistência

### PostgreSQL

A estrutura inicial do banco de dados foi criada na P10.

Tabela: `solicitacoes`

| Coluna | Tipo | Responsabilidade |
|---|---|---|
| id | BIGINT IDENTITY | Identificador único |
| titulo | VARCHAR(120) | Título da solicitação |
| descricao | TEXT | Descrição da solicitação |
| status | VARCHAR(40) | Estado da classificação |
| criado_em | TIMESTAMPTZ | Data e hora do cadastro |

### Integridade dos dados

O banco implementa:

- PRIMARY KEY para identificar registros.
- NOT NULL para campos obrigatórios.
- DEFAULT para preencher status e data de criação.
- CHECK para validar o comprimento de título e descrição.

### Validação realizada

Foram testados INSERT, SELECT, UPDATE, DELETE,
CHECK, NOT NULL, transações com ROLLBACK
e persistência após reconexão.

### Limitação atual

A API continua utilizando `storage.py` com uma lista
Python em memória. O PostgreSQL já está operacional,
mas ainda não está conectado ao FastAPI.

### Próxima evolução

Na P11, implementaremos conexão via driver Python,
consultas SQL parametrizadas e persistência real
nos endpoints existentes.
