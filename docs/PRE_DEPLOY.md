# Consolidação pré-deploy do SolicitaFlow

**Escopo:** publicar e consolidar o código válido. Não provisionar nem publicar a aplicação.
A base auditada é a V2.6.1, merge `8acaf71ef36bc74de353a248ddd100318f21a67e` (PR #14).
A entrega de consolidação é posterior: exemplos, proteção de arquivos locais,
documentação e alinhamento da dependência de testes. Não altera regras de negócio.

## Branches e PRs na base auditada

Após `git fetch --all --prune`, foram encontradas 15 branches reais no GitHub;
o ponteiro simbólico origin/HEAD não é uma branch adicional. Todos os 14 PRs
anteriores estão merged; não há PR aberto nem encerrado sem merge nesse ponto.
As 14 branches históricas são ancestrais da main. Diferenças de árvore ao comparar
uma branch antiga com main representam evolução posterior, não trabalho esquecido.

Contagens relativas ao SHA 8acaf71, antes da nova branch de consolidação:

| Branch remota | Último commit | À frente | Atrás | PR associado | Decisão |
| --- | --- | ---: | ---: | --- | --- |
| `ci/isolated-verification` | `d2ba74d` | 0 | 14 | #8 | Integrada — nenhum merge necessário. |
| `docs/v2-operations` | `ff16fae` | 0 | 8 | #11 | Integrada — nenhum merge necessário. |
| `feat/solicitaflow-identity` | `9e748d1` | 0 | 27 | #2 | Integrada — nenhum merge necessário. |
| `feat/ux-ui-learning-themes` | `eb4e381` | 0 | 29 | #1 | Integrada — nenhum merge necessário. |
| `feat/v2-5-onboarding-laboratory-ux` | `757afa0` | 0 | 6 | #12 | Integrada — nenhum merge necessário. |
| `feat/v2-6-1-brand-faq-dark-default` | `fc1ceb7` | 0 | 1 | #14 | Integrada — nenhum merge necessário. |
| `feat/v2-6-b2b-real-ai` | `c8604d8` | 0 | 4 | #13 | Integrada — nenhum merge necessário. |
| `feat/v2-demonstration-lab` | `fd4a395` | 0 | 19 | #6 | Integrada — nenhum merge necessário. |
| `feat/v2-portals` | `2a6a27a` | 0 | 23 | #4 | Integrada — nenhum merge necessário. |
| `feat/v2-routing` | `6610f60` | 0 | 25 | #3 | Integrada — nenhum merge necessário. |
| `feat/v2-workflow-sla` | `74d4846` | 0 | 21 | #5 | Integrada — nenhum merge necessário. |
| `fix/lab-clock-timestamps` | `f9ab072` | 0 | 10 | #10 | Integrada — nenhum merge necessário. |
| `fix/v2-resource-guards` | `d6e8cd2` | 0 | 17 | #7 | Integrada — nenhum merge necessário. |
| `fix/workflow-visibility` | `aeec188` | 0 | 12 | #9 | Integrada — nenhum merge necessário. |
| `main` | `8acaf71` | 0 | 0 | — | Integrada — nenhum merge necessário. |

Não fazer merge vazio para integrar novamente essas branches. Nenhuma foi excluída.
A branch `chore/predeploy-consolidation` acrescenta somente a preparação descrita
neste documento e terá PR próprio, sujeito à regressão e ao CI verde.

### Branches exclusivamente locais

- `feat/deploy-railway` aponta para 70274d2: zero commits à frente, 30 atrás da base.
  Apesar do nome, não contém um deploy novo commitado. Já é ancestral da main.
- `backup/p09-amend` aponta para 6e23d11: um SHA exclusivo e 39 commits atrás da base.
  O backend inteiro desse commit é **idêntico** ao de 6fb81df, já integrado; a diferença
  entre os dois commits está somente em três documentos de aprendizagem antigos.
  README, arquitetura e guia já evoluíram. Não restaurar armazenamento em memória,
  documentos antigos ou usar merge apenas para incluir o SHA de backup. A branch
  permanece local, preservada também em bundle privado verificável, sem force push.

As demais branches locais coincidem com suas equivalentes remotas integradas.
Não existe código funcional exclusivo a publicar da branch de backup.

## Cópia Windows

A cópia `D:\Projects\ai-request-classifier` ainda está em70274d2 e é histórica.
Seus nove arquivos rastreados modificados diferem apenas por LF/CRLF, conforme
comparação byte a byte após normalizar somente os finais de linha. Não importar
essas diferenças. As três peças Railway são idênticas às da cópia Linux. O pacote
original de marca permanece no Windows; os seis assets usados já estão na main.
Nenhuma alteração foi feita nessa cópia Windows.

## Arquivos Railway não promovidos

| Arquivo local anterior | Diagnóstico | Decisão |
| --- | --- | --- |
| backend/Dockerfile | Python 3.14 fora da matriz validada 3.12, host IPv6/porta fixa, não prepara scheduler/isolamento/TLS e copia migrador antigo | Não promover nem executar; preservar arquivo original |
| backend/.dockerignore | Regras úteis como referência, mas vinculadas ao build legado que não será usado | Preservar junto ao pacote legado |
| backend/migrate.py | Ledger schema_migrations distinto de sf_schema_versions, sem checksums, remove BEGIN/COMMIT dos SQLs e pode reaplicar 001–007 sobre objetos existentes | Não executar nem integrar |

Originais foram movidos de forma reversível para
`~/.local/share/ai-request-classifier/predeploy-consolidation/legacy-railway/`.
O manifesto privado contém caminhos originais, hashes e comandos de restauração.
As cópias Windows continuam intocadas. Não há descarte dos arquivos nem das branches.
Um eventual Dockerfile novo dependerá da arquitetura e de testes próprios; esta
consolidação não instala Docker nem valida o contêiner antigo como produção.

## Configuração segura de uma instalação nova

`backend/.env.example` usa 127.0.0.1:5432, banco principal e role `ai_classifier_app`.
`backend/.env.test.example` usa banco/role exclusivos de testes. Ambos têm chave de
IA vazia e os dois controles false. Não copiar templates sobre credenciais existentes.

| Responsabilidade | Identidade |
| --- | --- |
| Runtime principal | ai_classifier_app, sem TRUNCATE e sem administração do esquema |
| Proprietária do esquema | ai_classifier_owner, NOLOGIN |
| Manutenção/migrações | conexão administrativa autorizada que possa SET ROLE para a proprietária |
| Pytest e QA | ai_classifier_test, somente ai_request_classifier_test, sem CONNECT ao principal |

A aplicação lê PGHOST,PGPORT,PGDATABASE,PGUSER,PGPASSWORD; não consome DATABASE_URL
por conta própria. Variáveis libpq de TLS devem ser definidas/validadas para banco
remoto. `load_dotenv` não sobrescreve variáveis herdadas. O controlador local remove
PG/AI/DeepSeek/SF herdadas e lê o arquivo local correspondente.

Para IA: AI_ENABLED e SF_REAL_AI_ENABLED, DEEPSEEK_API_KEY somente no backend,
AI_MODEL=deepseek-flash e limites SF_AI_* do exemplo. SF_SECURE_LEGACY permanece true;
SF_QA_MODE não é um modo público. SF_CONTACT_URL é opcional e precisa ser confirmado.
Preços/reservas devem ser revalidados antes de habilitar IA pública; nenhuma chamada
paga é necessária para consolidar ou executar a regressão.

O .gitignore agora cobre dumps, backups, logs, PIDs, caches e chaves locais. Só os dois
templates .env conhecidos são liberados. Ignore não substitui revisão de diff e scan
de segredos. Não executar git add indiscriminado nem publicar arquivos operacionais.

## Dependências e qualidade

Python 3.12 e Node 24 são a matriz já executada. O lockfile npm é preservado.
A dependência de desenvolvimento foi alinhada a httpx2, que já está no ambiente
local e é o adaptador atual do TestClient. Não é uma troca de cliente da API em
produção. A recomendação consta na [documentação Starlette](https://starlette.dev/testclient/).
Não há atualização indiscriminada das bibliotecas de runtime.

Os requisitos Python ainda não formam um lock transitivo completo. Para a publicação,
fixar e validar um conjunto reprodutível na imagem/plataforma escolhida, conferir
vulnerabilidades e manter um processo de atualização. Não reaproveitar o Dockerfile
3.14 como evidência de compatibilidade.

```bash
cd ~/projects/ai-request-classifier
backend/.venv/bin/python scripts/local_services.py test
# Somente depois que pytest terminar:
backend/.venv/bin/python scripts/qa_local.py start
backend/.venv/bin/python scripts/qa_local.py browser
backend/.venv/bin/python scripts/qa_local.py stop
```

O primeiro comando confirma DB/role/porta/versão/isolamento e snapshot do principal.
O QA limpa somente o banco de testes, usa mocks e portas 18000/5174. Nunca executar
pytest e o QA simultaneamente. Testes frontend: npm test; build: npm run build. Na instalação recuperada, adicionar
`~/.local/opt/ai-request-classifier/node/bin` ao PATH como no guia, para usar Node24
em vez de um executável global antigo.
CI repete banco efêmero, migrações, regressão, segurança, isolamento e navegador.
Os resultados efetivos de cada execução ficam no PR, nos checks e na auditoria local.

## Migrações e banco existente

001–003 continuam os SQLs oficiais originais; 004–007 são aditivos e têm checksum.
O runner atual é scripts/migrate_v2.py, com roles separadas; não provisiona bancos
nem permissões. Instalação nova exige bootstrap revisado e permissões mínimas depois
das migrações. scripts/ci_database.py é **somente CI efêmero**, não é instalador local
ou de produção. Nenhuma migração foi executada no banco principal nesta consolidação.
Não renomear ou reinstalar o PostgreSQL18 atual para preparar o deploy.

## Bloqueios concretos antes da publicação

O GitHub consolidado é uma base para **iniciar a fase de deploy**, não autorização
para expor o serviço local atual. Não foi criado serviço, banco ou conta em nuvem.

| Item | Evidência no código | Próxima validação necessária |
| --- | --- | --- |
| Domínio/origem | local_origin_guard aceita somente localhost/127.0.0.1 | allowlist explícita de origem pública e testes CSRF; não liberar wildcard |
| Cookies | secure=False para HTTP local | Secure sobre HTTPS, domínio e SameSite coerentes com a topologia |
| Caminho /api | proxy só no servidor Vite; dist não inclui proxy | gateway/rewrite comprovado para POST/GET/cookies ou app sob mesma origem; não usar Vite dev em produção |
| Rede e PORT | controlador inicia em loopback/8000 | comando de produção que escute a interface/porta exigidas pela plataforma; não reutilizar controlador WSL na nuvem |
| Healthcheck | /health é liveness e não consulta banco | readiness limitado, timeout e checagem de conexão/schema sem expor detalhes |
| Banco remoto | sessão advisory lock na concorrência e no runner | endpoint direto/TLS, roles mínimas e número de conexões medido |
| Execução IA | BackgroundTasks no processo web | fila durável ou recuperação de interrupção testada, sem retries pagos desconhecidos |
| SLA | scheduler separado em loop de 60s | agendamento compatível com suspensão do free tier; não prometer monitoração contínua |
| Abuso e custo | limites no PostgreSQL e por peerIP | perímetro/proxy confiável, teto no provedor e teste de concorrência em ambiente remoto |
| Dados fictícios | sessão 2h, workspace 24h; expirar não apaga tabelas | política de retenção, expurgo sem apagar diário de orçamento, backups e restauração testada |
| Acesso técnico | contas locais continuam com privilégios reais | impedir exposição de contas de administração na demonstração pública |
| Repositório | main sem proteção exigida no momento da auditoria | considerar regra de PR/check obrigatório; os merges desta entrega continuam verificando CI sem bypass |

## Render e Neon: viabilidade a validar, sem provisionamento

Consulta documental em 2026-11-13. Para portfólio de baixo tráfego, Render Static Site
+ API Web Service + Neon é uma possibilidade, sujeita aos bloqueios acima. As regras
de [rewrite](https://render.com/docs/redirects-rewrites) precisam ser testadas com
mutações e cookies: um redirect ou fallback SPA não prova um proxy seguro da API.

O [Render Free](https://render.com/docs/free) pode suspender o web service após 15 min
ocioso e usa filesystem efêmero. Isso implica cold start e interrupções de tarefas.
Não armazenar dados ou segredos gerados em arquivos locais do container. O scheduler
atual não será um serviço contínuo gratuito garantido; [cron no Render](https://render.com/docs/cronjobs)
tem cobrança mínima própria. Para demonstração guiada, avaliar as verificações síncronas
já acionadas pelo relógio fictício; monitoramento contínuo exige desenho separado.

O [Neon Free](https://neon.com/docs/introduction/plans), na consulta, oferece 100 CU-h/mês
por projeto, 1 GB por projeto e histórico de restauração de até 6h, sujeito aos demais
limites do plano. Não equivale a backup independente. Validar a região, versão do
PostgreSQL, limites de conexões, retomada após suspensão e restauração do esquema 001–007.

**Não trocar silenciosamente para o hostname com -pooler.** O código usa locks de
sessão; o [pool transacional Neon](https://neon.com/docs/connect/connection-pooling)
não suporta essa semântica. A opção conservadora é endpoint direto, com conexões
controladas, até uma revisão explícita. O driver deve usar
[TLS verificado](https://neon.com/docs/connect/connect-securely), CA confiável e
identidade de runtime limitada; credenciais só no backend da plataforma.

Alternativa a provar: um único aplicativo que sirva o build React e a API sob o mesmo
domínio, sem processo Vite em produção. Reduz questões de cookies/CORS, mas requer
adaptação de rotas, build e testes. Não foi implementada aqui. Para garantias reais de
agenda/uptime, avaliar compute pago; a solução continua um portfólio, não operação SaaS.

## Versão e baseline

A tag anotada v2.6.1, se ainda inexistente e publicada pela consolidação, aponta
para 8acaf71 (a versão entregue pelo PR #14). Não deve ser movida ao merge posterior.
O novo baseline pré-deploy é o SHA final da main depois do PR de consolidação,
registrado nos checks e no relatório final. Nenhuma tag existente deve ser sobrescrita.
