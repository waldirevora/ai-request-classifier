> Estado atual: **V2.6 com IA real controlada**. As seções históricas abaixo descrevem
> a recuperação do ambiente. Para orçamento, modo demonstrativo e testes seguros,
> consulte [V2_6.md](V2_6.md). Não use o roteiro antigo contra o backend real.

# Guia operacional SolicitaFlow

## Instalação recuperada

Diretório ativo: `/home/waldir/projects/ai-request-classifier` no Ubuntu/WSL.
Python 3.12 no `backend/.venv`; Node 24 em
`~/.local/opt/ai-request-classifier/node/bin`. PostgreSQL 18.6 usa a instalação
local já existente em `127.0.0.1:5432`. Estes caminhos históricos são intencionais.
Não usar o ambiente virtual ou node_modules da cópia Windows.

O controlador novo `scripts/local_services.py` administra exclusivamente os
processos da aplicação. Não instala, inicia ou encerra PostgreSQL, WSL ou Docker.

```bash
cd ~/projects/ai-request-classifier
backend/.venv/bin/python scripts/local_services.py start
backend/.venv/bin/python scripts/local_services.py status
backend/.venv/bin/python scripts/local_services.py restart-backend
```

Os endereços são http://localhost:5173 e http://localhost:8000/docs. O proxy Vite
`/api` aponta para `127.0.0.1:8000`; o navegador não recebe credenciais de banco ou IA.
Serviços ficam vinculados a `127.0.0.1`, para uso local, sem publicação.

Os PIDs e logs ficam em `~/.local/share/ai-request-classifier/`:
`backend.pid`, `frontend.pid`, `sla.pid` e os respectivos `.log`.
Antes de sinalizar um PID, o controlador confere diretório e comando do processo.
Scheduler verifica prazos a cada 60 segundos e não chama IA.

```bash
# Encerra somente backend, frontend e scheduler; mantém PostgreSQL.
backend/.venv/bin/python scripts/local_services.py stop
```

Sessões destacadas sobrevivem ao fechamento do terminal, enquanto o WSL e os
processos permanecerem ativos. Encerrar o WSL encerra também os serviços.

## Variáveis e precedência

`backend/.env` e `.env.test` são privados, ignorados pelo Git e não devem ser
copiados para comandos, relatórios ou capturas. A aplicação chama
`load_dotenv(..., override=False)`: variáveis herdadas prevalecem quando uvicorn
é iniciado diretamente. O controlador novo constrói o ambiente a partir do arquivo
local, removendo previamente variáveis herdadas PG/AI/DeepSeek/SF.

Principal: banco `ai_request_classifier`, role `ai_classifier_app`.
Testes: banco `ai_request_classifier_test`, role `ai_classifier_test`.
Role proprietária do principal: `ai_classifier_owner` sem login.
Aplicação não tem TRUNCATE; usuário de testes não tem CONNECT no principal.

O controlador força `SF_SECURE_LEGACY=true`. A IA V2 exige `AI_ENABLED=true`,
`SF_REAL_AI_ENABLED=true` e chave presente. O segundo controle é false por padrão.
Todos os formulários novos da V2.6 usam DeepSeek real dentro dos limites. Cota ou indisponibilidade preserva o pedido como exceção sem sugestão inventada.
Testes sempre recebem IA desabilitada e chave fictícia, com transporte bloqueado.
Não modificar a DeepSeek ou habilitar chamadas pagas para executar o laboratório.

## Contas e laboratório

O botão **Explorar demonstração gratuita** retoma uma sessão válida ou inicia um ambiente fictício independente quando necessário. Trocar
personagens não autentica usuários reais. O cabeçalho identifica o modo de simulação.
Cada ambiente admite até 20 pedidos e expira em 24 horas. A análise da V2.6 usa API real, sujeita ao orçamento global.
Recarregar, retomar ou **Recomeçar roteiro** preserva pedidos, relógio e workspace sem consumir cota de criação. Sessões expiradas não são recuperadas; uma nova entrada explícita cria outro ambiente, sujeita ao limite e ao Retry-After. Veja [V2.5](V2_5.md).

Contas fictícias locais usam senhas geradas. Na instalação recuperada, o arquivo
privado é `~/.local/share/ai-request-classifier/solicitaflow-v2/local-accounts.json`
(permissão 0600). Consulte-o somente em um editor local, sem enviar seu conteúdo.
Usuários: `colaborador`, `central`, `suporte_ti`, `acessos_permissoes`, `financeiro`,
`recursos_humanos`. O arquivo não faz parte do repositório.

`scripts/seed_local.py` provisiona as contas uma única vez em uma instalação nova.
Recusa sobrescrever um ambiente ou arquivo de credenciais existente. Não executar
novamente para tentar recuperar senhas: não altera credenciais já criadas.

A central local pode abrir **Triagem clássica**, que preserva as quatro abas do MVP.
Pedidos V2 ficam nos portais próprios. A triagem clássica pode consumir créditos
quando a IA legada estiver ativa; sua operação é restrita à central local confiável.

## Testes seguros

```bash
backend/.venv/bin/python scripts/local_services.py test
export PATH="$HOME/.local/opt/ai-request-classifier/node/bin:$PATH"
cd frontend
npm ci
npm test
npm run build
```

Preflight comprova DB/role de teste, PostgreSQL 18, porta 5432, TRUNCATE permitido
somente ali e impossibilidade de conectar ao principal. Fixtures limpam apenas as
tabelas conhecidas no banco de testes; não usam CASCADE no principal. O ledger de
migrações é preservado. O snapshot de solicitações principal deve permanecer igual.

Para repetir o teste de navegador com as ferramentas já instaladas:

```bash
cd ~/projects/ai-request-classifier
~/.local/share/ai-request-classifier/browser-venv/bin/python scripts/browser_lab.py \
  --output /tmp/solicitaflow-captures \
  --axe ~/.local/share/ai-request-classifier/ux-redesign/tools/node_modules/axe-core/axe.min.js
```

Esse teste só funciona com um backend explicitamente identificado como QA. Use o controlador scripts/qa_local.py descrito em V2_6.md; o serviço principal não aceita regressão automatizada paga. No CI, utiliza o Chrome do runner
com o mesmo sandbox. Não usar `--no-sandbox` para contornar falhas.

## Migrações

001, 002 e 003 pertencem ao MVP e já estão aplicadas nesta instalação. Não reaplicar
sem conferir o catálogo. A V2 aplicou 004, 005 e 006, registradas em
`sf_schema_versions` com checksum. A tabela original continua com 22 colunas.

Para conferir por uma conexão administrativa local autorizada, somente leitura:

```sql
SELECT current_database(), current_user, current_setting('server_version'),
       current_setting('port');
SELECT version, sha256, applied_at FROM sf_schema_versions ORDER BY version;
SELECT count(*) FROM information_schema.columns
WHERE table_schema='public' AND table_name='solicitacoes';
```

O runner aditivo é `scripts/migrate_v2.py`. Exemplo para uma instalação em que
libpq já tenha uma conexão administrativa segura configurada, sem senha no comando:

```bash
PGDATABASE=ai_request_classifier backend/.venv/bin/python scripts/migrate_v2.py ai_classifier_owner
PGDATABASE=ai_request_classifier_test backend/.venv/bin/python scripts/migrate_v2.py ai_classifier_test
```

Não executar esses comandos com a role limitada da aplicação esperando privilégios
administrativos. O runner não cria bancos, não redefine senhas e não concede acesso.
`scripts/ci_database.py` é exclusivo do serviço efêmero GitHub Actions e recusa
objetos existentes. Nunca usá-lo para provisionar a instalação local.

## Problemas comuns

401: entre novamente ou inicie um laboratório; a sessão pode ter expirado.
403: confira perfil e contexto; trocar aba não concede autorização.
404: recurso ausente ou fora do escopo do perfil/ambiente.
409: estado mudou ou atendimento já assumido; atualize a lista.
422: confira campos ou mapeamento categoria/departamento.
429: cota do laboratório, de login ou da IA controlada atingida.
Sem conexão: confira PostgreSQL existente e `local_services.py status`; não reinstale.
