# AI Request Classifier

Projeto prático de Engenharia de IA para classificação automática de solicitações internas de empresas.

## Objetivo

Receber solicitações, utilizar inteligência artificial para sugerir categoria e prioridade e disponibilizar as sugestões em um pipeline para revisão humana.

## Tecnologias planejadas

- Python e FastAPI: backend e API.
- PostgreSQL: armazenamento de dados.
- React: interface web e pipeline de revisão.
- API de modelo de IA: classificação automática.
- Git e GitHub: versionamento de documentação.

## Fluxo de funcionamento

1. O funcionário registra uma solicitação.
2. O backend valida e salva os dados.
3. A IA realiza a classificação automaticamente.
4. O analista recebe a sugestão no pipeline.
5. O analista aceita ou corrige a classificação.
6. O sistema registra a decisão final.

## Estado do projeto

Em desenvolvimento e aprendizagem. As funcionalidades ainda não foram implementadas.

## Plano de estudos

Consulte [Plano de Estudos e Dicas](docs/PLANO_DE_ESTUDOS_E_DICAS.md).

## Desenvolvimento

Projeto desenvolvido incrementalmente, com implementação manual do backend, testes e documentação das decisões técnicas.

## Execução local

Na pasta backend:

1. Instalar dependências de desenvolvimento:

   python -m pip install -r requirements-dev.txt

2. Iniciar API:

   python -m uvicorn app.main:app --reload

3. Abrir documentação:

   http://127.0.0.1:8000/docs

4. Executar testes:

   python -m pytest -q


## Banco de dados PostgreSQL

O projeto utiliza PostgreSQL 18 para desenvolver a camada de persistência.

A estrutura inicial está definida em
`backend/sql/001_create_solicitacoes.sql`.

### Ambiente local de desenvolvimento

- PostgreSQL: 18.6
- Host: 127.0.0.1
- Porta: 5433
- Banco: ai_request_classifier

### Criar a estrutura

Na raiz do projeto, com PostgreSQL instalado e o banco criado:

```powershell
psql -U postgres -h 127.0.0.1 -p 5433 -d ai_request_classifier -v ON_ERROR_STOP=1 -f .\backend\sql\001_create_solicitacoes.sql
```

### Estado atual

O banco e a tabela de solicitações foram criados e testados.
A API FastAPI ainda utiliza armazenamento temporário em memória.

A conexão entre FastAPI e PostgreSQL será implementada na P11.
