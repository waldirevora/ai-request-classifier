# Demonstração pública: Render Free + Neon Free

Esta é uma demonstração de portfólio B2B com dados fictícios, não um serviço corporativo continuamente operado. O ambiente WSL e seus bancos não são copiados nem alterados pelo provisionamento público.

## Arquitetura e custo

Um Render Web Service **Free**, Python 3.12 e Node 24, serve React compilado e FastAPI em `/api`, na mesma origem HTTPS. Build: `python scripts/build_cloud.py`. Inicialização: `python scripts/start_cloud.py`. O processo usa `$PORT`, um worker, concorrênciaHTTP 20, sem Vite, cron, disco pago ou scheduler permanente. Dependências Python têm um snapshot testado em `backend/constraints.txt`; frontend usa `npm ci`.

Neon: projeto novo Free, PostgreSQL18, conexão **direta** (sem `-pooler`), TLS `verify-full`, CA explícita `/etc/ssl/certs/ca-certificates.crt`. A verificação usa `conn.pgconn.ssl_in_use`: no Neon, o proxy termina TLS e `pg_stat_ssl` do servidor pode indicar `false` mesmo com conexão do cliente criptografada e certificado validado. Compute fixo 0.25CU, suspensão automática de 5 min. PgBouncer transacional não suporta os locks de sessão utilizados pela IA. Além desses locks, reservas persistentes impedem uma segunda chamada quando a conexão do lock cai.

Limites consultados em 13/11/2026: Render Free 750horas/workspace/mês, suspensão após 15 min ocioso; Hobby 500minutos de build e5 GB de saída. **Sem método de pagamento**, o esgotamento suspende o uso, em vez de contratar capacidade. Neon Free 100CUh/projeto/mês,1 GB/projeto,5 GB de saída e janela de restauração de 6 h limitada pelo volume de mudanças. Não habilitar upgrades, planos pagos ou autoscaling maior sem nova autorização.

Fontes: [Render Free](https://render.com/docs/free), [build](https://render.com/docs/build-pipeline), [bandwidth](https://render.com/docs/outbound-bandwidth), [Neon Free](https://neon.com/docs/introduction/plans), [pooling](https://neon.com/docs/connect/connection-pooling). Preços e limites devem ser reconferidos antes de mudanças de plano.

O `/health` é liveness, **não abre conexão com o banco**: use-o como healthcheck do Render para permitir que o Neon suspenda. `/ready` valida TLS, role, PostgreSQL18, sete checksums, 22 colunas e ausência deTRUNCATE; exige Bearer de manutenção para evitar que visitantes mantenham o banco ativo com sondagens. Primeiro acesso após suspensão pode demorar. Não usar serviços externos de keep-alive.

## Segredos e provisionamento

Use `backend/.env.production.example` somente como referência. O arquivo preenchido fica fora do repositório, modo 0600, enviado como secret file Render `solicitaflow.env`; o launcher lê `/etc/secrets/solicitaflow.env`. Nunca usar os valores em argumentos de CLI, frontend, prints ou PR. A chave DeepSeek permanece no backend. O build filtra variáveisPG/AI/SF antes de executar Node.

Criar roles por SQL: roles criadas pela API/console Neon normalmente recebem `neon_superuser` e não são adequadas para runtime.

- `ai_classifier_owner`: NOLOGIN, proprietária do banco/esquema.
- `ai_classifier_migrator`: LOGIN, NOINHERIT, membro somente da owner, utilizada em operação manual e nunca enviada ao Render.
- `ai_classifier_app`: LOGIN, sem superuser/CREATEDB/CREATEROLE/BYPASSRLS/membership de owner; CONNECT somente ao banco da demonstração; CRUD limitado; semTRUNCATE, semUPDATE/DELETE nos eventos nemDELETE no livro de consumo.
- `ai_classifier_cleanup`: LOGIN separado, semDDL ou administração, apenasSELECT/DELETE nos dados temporários,UPDATE para anonimização eINSERT no marcador de limpeza. Credencial restrita ao backend.

Banco novo `solicitaflow_demo`; não importar dados locais. Usar `scripts/cloud_ops.py migrate` com a credencial de migração em variáveis privadas. O runner exige banco dedicado, PG18, recusa esquema inesperado e aplica **somente 001–007** na ordem oficial, respeitandoBEGIN/COMMIT. Registra checksums em `sf_schema_versions`, valida 5/15/22 colunas, proprietários e sequência. Segunda execução confere o ledger e não reaplica SQL. Nunca executar migrações no boot do Render.

## Publicação controlada

1. CI e revisão do diff aprovados, SHA integrado àmain.
2. Novo projeto Neon Free; roles mínimas, migrações e testes de permissões.
3. Serviço Render Free, auto-deploy desabilitado, `/health`, secret file, `SF_MAINTENANCE=true`, IA desligada.
4. Sem Bearer, a home/API retornam503. O operador fornece `Authorization: Bearer <token>` **por cabeçalho privado**, nunca por URL ou localStorage.
5. Validar certificadoHTTPS, `/ready`, sessões, isolamento, origem, headers e fluxo fictício. `/_operator/status` só funciona em manutenção, mostraSHA e diagnóstico do proxy sem segredos.
6. Backup criptografado e restauração em banco vazio separado.
7. Habilitar IA apenas com orçamento/cotas comprovados; executar pouquíssimos testes reais, com idempotência e registro de tokens. Sem retries automáticos.
8. Liberar `SF_MAINTENANCE=false` após validação e redeploy. Validar acesso anônimo eSHA realmente implantado.

Cookies `__Host-sf_lab`: Secure, HttpOnly, SameSiteStrict, Path/, semDomain. CSRF: origem HTTPS exata, JSON, cabeçalho de contexto e FetchMetadata; autorizações continuam no backend. Sem CORS público. Swagger/OpenAPI, login corporativo e endpoints legados não são expostos. CSP, HSTS, proteção de frames e corpo máximo32 KiB. O Uvicorn ignora headers de proxy. X-Forwarded-For nunca cria identidade/cota. CF-Connecting-IP só é considerado para peers de transporte explicitamente confiáveis e após teste de spoofing na infraestrutura real; o padrão é conservador, por rede do peer, podendo compartilhar cotas entre visitantes.

## IA e interrupções

Envelope público máximo:10 tentativas/diaUTC,2 por workspace,5 por rede/hora,100000 tokens/dia,US$ 0.05 reservado/dia,1 chamada concorrente. Reserva conservadora inclui entrada em bytes, instruções, margem de protocolo e saída limitada400 tokens; preços configurados devem exceder os preços oficiais vigentes. Novas chamadas param quando qualquer limite é atingido. Isso limita a integração da demonstração; não é um teto financeiro configurado na conta DeepSeek, que pode ser usada por outros projetos.

A reserva é gravada **antes** da chamada e nunca devolvida em falha. Repetir a mesma chave de envio retorna o mesmo pedido; não chama novamente. Reinício/queda não repete trabalho. Casos interrompidos passam para exceção após 5 min na próxima atividade. Uma reserva desconhecida continua bloqueando chamadas novas, inclusive em outro dia, até conferência pelo responsável. Nunca limpar contadores, reenviar automaticamente ou marcar sucesso sem resposta validada. Para reconciliar, parar a IA em manutenção, comprovar ausência de execução, consultar o consumo no provedor e marcar somente a tentativa específica como falha auditada; manter todos os valores reservados. Em dúvida, manter a IA desabilitada.

## SLA demonstrativo e retenção

SLA é avaliado nas consultas de pedidos e ao avançar o relógio fictício. Não há monitoramento24/7 enquanto o Render dorme. Atendimento, cobranças, escalonamento e resolução são fictícios; notificações não vão para contatos externos.

Sessão 2 h, workspace 24 h. Após expiração, cookie antigo não recupera o workspace; IP não é identidade. Na próxima atividade, no máximo 1 limpeza/hora, descrições/justificativas/observações/resoluções e eventos de laboratórios expirados são removidos ou anonimizados. Metadados e consumo mínimo ficam 32 dias; só depois ocorre purge do workspace expirado. Reservas desconhecidas e consumo recente impedem purge. Workspaces locais/ativos nunca são alvo. Contadores correntes são preservados. Em ociosidade, a remoção física aguarda a próxima atividade. Não enviar dados pessoais; dados fictícios persistem no backup até sua expiração operacional.

## Backup e restauração

Instalar ferramentas num ambiente operacional privado: `pip install -r backend/requirements-ops.txt`. Usar clientesPG18, credencial de migração/admin por ambiente privado e diretório foraGit, modo0700.

```bash
# PG* carregadas de armazenamento privado, nunca copiadas para histórico/relatórios.
python scripts/cloud_ops.py backup --directory "$HOME/.local/share/ai-request-classifier/public-deploy/backups" --pg-bin /caminho/pg18/bin
# Trocar PGDATABASE para solicitaflow_restore_test, criado vazio separadamente.
python scripts/cloud_ops.py restore --stem /caminho/privado/solicitaflow-TIMESTAMP --pg-bin /caminho/pg18/bin
```

O dump nunca é escrito em claro; é criptografado e autenticado comFernet. `.key` e `.backup.fernet` devem ter cópias offline **separadas**; perder a chave impede recuperação. O manifesto guarda hashes e contagens, não conteúdo. Restore recusa destino preenchido e qualquer banco diferente de `solicitaflow_restore_test`. Compara todas as linhas e sete checksums. Reaplicar privilégios explícitos após recuperação; dumps excluemACL e ownership.

Realizar backup antes de migrações/releases e após demonstrações que devam ser preservadas; revisar semanalmente e manter por até 35 dias, removendo somente bundles identificados após verificar a cópia de recuperação. O históricoNeon não substitui esse procedimento. BackupWSL é manual, não uma promessa de rotina automática ou alta disponibilidade.

Em recuperação pública real, permanecer em manutenção com IA desligada. Não restaurar um ledger antigo e reabilitar a IA no mesmo dia: reconciliar consumo/reservas ou aguardar o próximoUTC com bloqueio conservador para o dia corrente. Nunca apagar reservas desconhecidas para liberar cota.

## Manutenção, rollback e encerramento

Auto-deploy fica desabilitado: cada release exigeCI, manutenção e deploy doSHA aprovado. Para suspensão emergencial, usar o painelRender para suspender o serviço ou reimplantar com `SF_MAINTENANCE=true`, `AI_ENABLED=false` e `SF_REAL_AI_ENABLED=false`. Token não concede identidade corporativa; o laboratório continua isolado mesmo para o operador.

Rollback de código usa um deploy doSHA anterior compatível com o esquema; não reverter dados/migrações automaticamente. Credenciais comprometidas exigem rotação noNeon/DeepSeek e atualização do secretfile, depois redeploy e revogação das antigas. Logs não contêm prompts, credenciais ou resposta bruta de provedores; acessoHTTP não é logado pelo launcher.

Encerramento: primeiro suspenderRender e desabilitar/revogar sua chave de IA; exportar/verificar backups necessários, remover somente o serviço/projeto público identificados e revogar suas roles. Não excluir outros projetosNeon, bancos WSL ou histórico Git. Nenhum DNS personalizado é necessário.
