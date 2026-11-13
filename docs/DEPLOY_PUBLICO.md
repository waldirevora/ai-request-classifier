# Deploy e operação da demonstração pública

**Demonstração publicada:** [https://solicitaflow.onrender.com](https://solicitaflow.onrender.com).
O proprietário confirmou seu funcionamento. Este guia descreve o ambiente entregue,
seus limites e procedimentos de manutenção; não é uma autorização para reprovisionar
recursos ou alterar configuração em uma revisão documental.

## Infraestrutura e versão em execução

| Componente | Configuração validada na publicação de 13/11/2026 |
| --- | --- |
| Render | Um Web Service Free, workspace Hobby sem método de pagamento, região Virginia |
| Runtime | Python 3.12, Node.js 24 para build; um worker e uma instância |
| Aplicação | React compilado + FastAPI em `/api`, mesma origem HTTPS |
| Build / start | `python scripts/build_cloud.py` / `python scripts/start_cloud.py` |
| Porta / healthcheck | `$PORT` fornecida pelo Render / `/health` sem consulta ao banco |
| Neon | Projeto Free separado, região AWS us-east-1, compute fixo em 0,25 CU |
| Banco | `solicitaflow_demo`, PostgreSQL 18; SQL da homologação retornou 18.7 |
| Conexão | Endpoint direto, TLS `verify-full`, CA `/etc/ssl/certs/ca-certificates.crt` |
| IA | DeepSeek `deepseek-flash`, habilitada dentro das cotas persistentes |
| Automação de prazos | Eventos e relógio fictício; sem worker/cron permanente |
| Deploy automático | Desabilitado |

O SHA funcional publicado é
[`e8944877d1d208a24cf0061ea5caa3c417f69d87`](https://github.com/waldirevora/solicitaflow/commit/e8944877d1d208a24cf0061ea5caa3c417f69d87),
validado pelo [CI do baseline](https://github.com/waldirevora/solicitaflow/actions/runs/43471847935).
A `main` recebe um encerramento exclusivamente documental depois desse SHA.
Essa diferença é intencional: merge documental não dispara redeploy nem muda o
código/configuração em execução. A tag histórica `v2.6.1` continua em `8acaf71`.

O serviço entrega arquivos de `frontend/dist`; Vite não é servidor público. O build
usa `npm ci` e o snapshot Python em `backend/constraints.txt`, filtrando variáveis de
backend antes do processo Node. O launcher usa a porta do ambiente, um worker,
concorrência HTTP 20, sem confiar automaticamente em headers de proxy. Não inicia
PostgreSQL, scheduler local, Docker ou processos adicionais.

O banco público não contém uma cópia automática dos bancos WSL. O ambiente local,
suas credenciais e o outro projeto Neon preexistente foram preservados.

## Suspensão nativa, custo e disponibilidade

Os planos Render e Neon selecionados são gratuitos. Não foram contratados worker,
cron, disco persistente ou domínio pago. DeepSeek pode consumir créditos existentes.

Na consulta de 13/11/2026, o [Render Free](https://render.com/docs/free) oferece
750 horas de instância por workspace/mês e suspende o serviço após 15 minutos sem
tráfego. A primeira requisição inicia o serviço novamente, normalmente com espera
da ordem de um minuto; não há garantia desse tempo. O filesystem é efêmero.
Hobby inclui [500 minutos de build](https://render.com/docs/build-pipeline) e
[5 GB de saída](https://render.com/docs/outbound-bandwidth) por mês. Sem método de
pagamento, o esgotamento suspende o uso; adicionar pagamento pode mudar essa regra.

O [Neon Free](https://neon.com/docs/introduction/plans) inclui 100 CU-h/projeto/mês,
1 GB/projeto, 5 GB de transferência e histórico de recuperação de seis horas,
limitado pelo volume de mudanças. O compute ocioso suspende após cinco minutos.
No endpoint validado, a API reportou intervalo `0` gerenciado pelo plano e recusou
alteração manual; o histórico comprovou suspensão e retomada automáticas.
Revalidar franquias/preços antes de mudanças. Não habilitar upgrade automático.

**Não foi instalado gatilho periódico do Neon, keep-alive externo ou cron para
impedir suspensão.** Preservar o comportamento nativo de inicialização do Render.
`/health` é liveness e não abre conexão SQL. `/ready` exige Bearer operacional para
não permitir sondagens públicas que mantenham o Neon acordado; confere TLS, role,
versão, sete checksums, 22 colunas e ausência de TRUNCATE. No Neon, TLS termina no
proxy; a verificação correta usa `conn.pgconn.ssl_in_use`, não apenas `pg_stat_ssl`.

O SLA do produto é fictício e avaliado em consultas/eventos ou ao avançar o relógio.
Não se promete monitoramento 24/7 ou SLA empresarial durante suspensão.

## Banco, migrações e privilégios

As migrações oficiais são as únicas alterações de esquema aplicadas no banco público:

| Ordem | Arquivo | Finalidade |
| --- | --- | --- |
| 001 | `001_create_solicitacoes.sql` | Cadastro original, cinco colunas |
| 002 | `002_add_classificacao_ia.sql` | Sugestão e consumo de IA, 15 colunas |
| 003 | `003_add_revisao_humana.sql` | Revisão humana, 22 colunas |
| 004 | `004_routing.sql` | Workspaces, departamentos, roteamento e eventos |
| 005 | `005_identity.sql` | Contas, sessões e limites |
| 006 | `006_workflow_sla.sql` | Atendimento, políticas e notificações de SLA |
| 007 | `007_controlled_ai.sql` | Estados da análise, idempotência e ledger de reservas |

`scripts/cloud_schema.py` aplica os arquivos intactos, respeita suas transações e
registra checksums em `sf_schema_versions`. Recusa esquema preexistente inesperado;
reexecução valida o ledger e não reaplica migrações. `scripts/cloud_ops.py migrate`
é uma operação administrativa manual, com ambiente privado e banco dedicado.
Não executar no boot, contra o banco local por engano, ou com a role da aplicação.
Não usar o `backend/migrate.py` legado de Railway.

Verificação do baseline: 16 tabelas incluindo ledger, 34 índices, cinco sequências,
16 PKs, 22 FKs, 22 CHECKs e 11 UNIQUE; objetos pertencem a `ai_classifier_owner`.
A tabela `solicitacoes` mantém 22 colunas. As contagens são evidência dessa revisão,
não motivo para reaplicar scripts quando um ambiente já está provisionado.

| Role | Fronteira de privilégio |
| --- | --- |
| `ai_classifier_owner` | NOLOGIN, proprietária dos objetos |
| `ai_classifier_migrator` | LOGIN, NOINHERIT, membro da owner para SET ROLE; fora do Render |
| `ai_classifier_app` | LOGIN, CRUD limitado, sem superuser/CREATEDB/CREATEROLE/BYPASSRLS ou membership administrativa; sem DDL/TRUNCATE |
| `ai_classifier_cleanup` | Credencial distinta, SELECT/DELETE em temporários e UPDATE para anonimização; sem DDL/administração |

Eventos não admitem UPDATE/DELETE pela aplicação; o ledger de consumo não admite
DELETE. A limpeza recebe INSERT no marcador e `UPDATE(name)` em `sf_workspaces`,
necessário ao SELECT FOR UPDATE, sem permitir alterar o prazo de expiração.
A aplicação não conecta a `neondb` nem a `solicitaflow_restore_test`.

Roles de runtime foram criadas por SQL, sem herdar `neon_superuser`.
[Roles criadas pelo console/API Neon podem receber privilégios administrativos](https://neon.com/docs/manage/roles).
A conexão é **direta**: [pooling transacional](https://neon.com/docs/connect/connection-pooling)
não suporta os advisory locks de sessão usados nos slots de IA. A reserva durável
adicional mantém o bloqueio mesmo se a conexão do lock cair.

## Configuração e segredos

`backend/.env.production.example` é referência sem segredos. O arquivo preenchido
fica fora do Git e é enviado como secret file Render `solicitaflow.env`; o launcher
lê `/etc/secrets/solicitaflow.env`, sem sobrescrever variáveis já herdadas.
Não copiar credenciais em argumentos, frontend, logs, relatórios ou capturas.

| Grupo | Variáveis / comportamento |
| --- | --- |
| Ambiente | `SF_ENV=production`, `SF_SECURE_LEGACY=true`, `SF_QA_MODE=false` |
| Origem | `SF_PUBLIC_ORIGIN` exata ou `RENDER_EXTERNAL_URL`; sem wildcard |
| PostgreSQL | `PGHOST`, `PGPORT=5432`, `PGDATABASE=solicitaflow_demo`, `PGUSER=ai_classifier_app`, senha privada, `PGSSLMODE=verify-full`, CA explícita |
| Limpeza | `SF_CLEANUP_USER=ai_classifier_cleanup` e senha própria privada |
| Manutenção | `SF_MAINTENANCE` e token operacional privado; nenhuma credencial no URL |
| IA | `AI_ENABLED`, `SF_REAL_AI_ENABLED`, `DEEPSEEK_API_KEY`, `AI_MODEL=deepseek-flash` |
| Proxy | Somente peers explicitamente validados; na publicação, `127.0.0.1/32` |

A configuração publicada está fora de manutenção, com os dois flags de IA
habilitados. O template inicia com manutenção e IA desligada para provisionamentos
novos: não representa os valores ativos nem deve sobrescrevê-los automaticamente.
O token operacional permite inspecionar a publicação em manutenção, mas não cria
uma identidade corporativa ou acesso a outro workspace.

## IA e interrupções

| Variável | Valor público validado |
| --- | --- |
| `SF_AI_DAILY_CALLS` | 10 por dia UTC global |
| `SF_AI_WORKSPACE_CALLS` | 2 por workspace |
| `SF_AI_HOURLY_IP_CALLS` | 5 por rede/hora |
| `SF_AI_DAILY_TOKENS` | 100000 reservados/dia |
| `SF_AI_DAILY_USD` | 0.05 reservado/dia |
| `SF_AI_CONCURRENT` | 1 |
| `SF_AI_INPUT_USD_PER_M` / `SF_AI_OUTPUT_USD_PER_M` | 0.60 / 2.40, preços conservadores de reserva |

Saída máxima 400 tokens; timeout 12 segundos; sem retry pago automático.
Criação de laboratórios: 10 novas sessões por rede/hora, máximo global de 30 novos
workspaces/dia e 30 ativos. Uma sessão válida é retomada sem consumir nova criação.
Cada laboratório admite até 20 pedidos, mesmo quando a cota de análises já terminou.

A reserva é gravada antes da chamada e não é devolvida automaticamente em falha.
Repetir a mesma chave de envio retorna o mesmo pedido. Casos interrompidos seguem
para exceção após cinco minutos na próxima atividade; o consumo desconhecido
continua bloqueando chamadas até conferência do operador, inclusive em outro dia.
Nunca limpar o ledger, gerar retries ou marcar sucesso para liberar orçamento.
Em dúvida, manter a IA desligada. O envelope não é teto de faturamento da conta
DeepSeek inteira; preços e consumidores compartilhados precisam de acompanhamento.

## Sessões, retenção e recuperação

Sessão de até duas horas, limitada pelo workspace de 24 horas. Atualizar a página
não renova a sessão; IP não recupera laboratório expirado. Na próxima atividade,
no máximo uma limpeza por hora, dados textuais de laboratórios expirados são
anonimizados e eventos temporários removidos. Metadados/consumo mínimos ficam por
32 dias; somente depois ocorre expurgo, preservando consumo recente e reservas
pendentes. Workspaces locais e ativos não são alvo. Ocioso não significa remoção
física imediata. A política detalhada e as fronteiras estão em [Segurança](SEGURANCA.md).

## Backup e restauração

A homologação restaurou um backup criptografado pré-liberação em banco isolado:
**16 tabelas e 114 registros comparados**, sete checksums e ownership verificados.
A role limitada de limpeza também foi testada nessa cópia; o banco público permaneceu
inalterado. A role de aplicação não pode conectar ao banco de restauração.

A rotina é manual, usando clientes PostgreSQL 18 e ambiente operacional privado com
`backend/requirements-ops.txt`. Antes de gerar manifesto/dump, colocar o serviço em
manutenção, desligar IA e aguardar chamadas terminarem: o manifesto e o dump são
obtidos separadamente e precisam dessa quiescência para comparação consistente.
Não executar comandos abaixo nesta etapa documental.

```bash
# PG* carregadas de armazenamento privado autorizado, sem senha no comando.
# Selecionar explicitamente o banco público como origem do backup.
python scripts/cloud_ops.py backup --directory /caminho/privado/backups --pg-bin /caminho/pg18/bin
# Só para um solicitaflow_restore_test novo e vazio, com PGDATABASE conferido.
python scripts/cloud_ops.py restore --stem /caminho/privado/solicitaflow-TIMESTAMP --pg-bin /caminho/pg18/bin
```

Fernet criptografa/autentica o dump sem gravá-lo em claro. Diretório 0700, arquivos
0600; chave e arquivo `.backup.fernet` precisam de cópias offline separadas. O
manifesto guarda contagens/hashes. Restore recusa alvo preenchido ou outro nome de
banco; compara linhas e checksums. Dumps excluem ACL/ownership: aplicar os privilégios
explícitos antes de considerar uma recuperação utilizável pela aplicação.

Guardar backup antes de mudanças de esquema/release e de demonstrações que precisem
ser preservadas. Revisar semanalmente; política manual de até 35 dias, removendo
somente bundles identificados depois de verificar uma cópia de recuperação. A
janela Neon não substitui esse procedimento nem garante backup local automático.
Não publicar dumps, chaves, manifests privados ou logs.

Para recuperação pública, usar banco novo sob manutenção/IA desligada. Não restaurar
um ledger antigo e reabrir cotas do mesmo dia: reconciliar o consumo ou bloquear
conservadoramente o dia corrente até o próximo UTC. Reservas desconhecidas não são
apagadas. Revalidar TLS, role, schema, isolamento e orçamento antes de reabrir.

## Manutenção e atualizações futuras

1. Conferir o incidente ou necessidade; uma mudança documental não exige redeploy.
2. Para mudança funcional, trabalhar em branch, revisar diff/segredos e executar testes com IA simulada.
3. Abrir PR e integrar somente após CI e proteções aprovados; não alterar a tag histórica.
4. Para uma atualização de serviço, colocar em manutenção, desligar IA e conferir consumo pendente; suspender no painel em emergência.
5. Fazer/verificar backup antes de migrações; aplicar somente migrações futuras explicitamente aprovadas, nunca automaticamente no boot.
6. Implantar um SHA aprovado, validar HTTPS/readiness, permissões e isolamento e só então retirar manutenção.
7. Registrar SHA efetivamente implantado e resultados. Merge não substitui deploy e auto-deploy continua desabilitado.

Flags de manutenção são `SF_MAINTENANCE=true`, `AI_ENABLED=false` e
`SF_REAL_AI_ENABLED=false`. Alterar o secret file exige redeploy para atingir o
processo; não afirmar suspensão imediata apenas por salvar variáveis. Healthcheck
público `/health` é suficiente para uma verificação pontual sem gerar dados de IA.
Não instalar gatilho periódico do Neon ou keep-alive como parte da manutenção normal.

Rollback de código requer um SHA anterior compatível, aprovado e disponível no
provedor; não reverter banco/migrações automaticamente. O primeiro baseline público
homologado é `e894487`; revisões anteriores não devem ser presumidas equivalentes.
Configuração e segredos devem ser conferidos separadamente de um rollback. Na
incerteza, manutenção/suspensão preservando o banco é o fallback seguro.

Encerramento de recursos, se futuramente autorizado: suspender o serviço, retirar
a chave do secret file e desligar a integração pública, preservar/validar backups e
excluir somente recursos identificados. A chave atual também atende o ambiente
local: não revogá-la globalmente sem conferir outros consumidores. Considerar chave
exclusiva em uma futura rotação autorizada. Não apagar outros projetos Neon, bancos
WSL, distribuição, Docker ou histórico Git.

Evidências do marco e separação entre desenvolvimento concluído e operação contínua:
[ENCERRAMENTO.md](ENCERRAMENTO.md).
