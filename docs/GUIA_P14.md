# Guia da P14 | React + revisão humana

**Arquivos completos para copiar, com substituição controlada.** O código foi preparado sobre o pacote P13, não sobre um clone da branch atual: faça `git diff` ou compare antes de substituir `main.py` e `triagem.py`. Não altere `routes/solicitacoes.py`, `ia.py` ou `database.py` nesta aula.

## O que muda e por quê

- **React** desenha formulário, fila e histórico. `useState` guarda dados visíveis; `useEffect` carrega dados; `fetch` envia HTTP à nossa FastAPI.
- **Vite** serve o React na porta 5173 e faz proxy de `/api/*` para a FastAPI 8000. Sem chave DeepSeek no frontend; sem necessidade de CORS no dev.
- **Pydantic** valida corpo da revisão. O analista pode **aceitar** uma sugestão existente ou **corrigir** categoria/impacto/urgência + observação. A matriz P12 no backend produz sempre a prioridade final.
- **PostgreSQL** guarda decisão e momento da revisão, preservando os campos de sugestão da IA. `FOR UPDATE` e HTTP 409 evitam revisar um mesmo registro duas vezes.
- **Fallback manual**: quando IA retorna `classificacao_falhou`, é possível corrigir manualmente, sem perder o cadastro.

## Primeiro: verificar caminhos e estado do Git

Na raiz `D:\Projects\ai-request-classifier`, use `git status -sb` (esperado: sem alterações inesperadas). Compare `backend/app/main.py` e `backend/app/triagem.py` com o kit antes de substituir; os outros arquivos backend P13 existentes são preservados.

## 1. SQL (PowerShell, na raiz)

```powershell
$env:Path += ";C:\Program Files\PostgreSQL\18\bin"
psql -U postgres -h 127.0.0.1 -p 5433 -d ai_request_classifier -v ON_ERROR_STOP=1 -f .\backend\sql\003_add_revisao_humana.sql
psql -U postgres -h 127.0.0.1 -p 5433 -d ai_request_classifier_test -v ON_ERROR_STOP=1 -f .\backend\sql\003_add_revisao_humana.sql
```

A migração incrementa colunas e não apaga dados. Execute uma vez; se o script disser que a coluna já existe, confira o estado do banco antes de prosseguir. Os testes executam **TRUNCATE destrutivo no banco `ai_request_classifier_test`**.

## 2. FastAPI e teste automático

Terminal 1:

```powershell
cd D:\Projects\ai-request-classifier\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Terminal 2 (backend):

```powershell
$env:AI_ENABLED = "false"
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:\AI_ENABLED -ErrorAction SilentlyContinue
```

Swagger em `http://127.0.0.1:8000/docs`: novas rotas `GET /revisoes/pendentes`, `GET /revisoes/concluidas`, `POST /revisoes/{solicitacao_id}`. Se retornar erro 42703 do PostgreSQL (coluna não existe), migração 003 não foi aplicada ao banco conectado. Não execute testes no banco principal.

## 3. React e testes frontend

Terminal 3:

```powershell
cd D:\Projects\ai-request-classifier\frontend
node --version
npm install
npm run build
npm run dev
```

Abra `http://127.0.0.1:5173`. A interface fala somente com `/api`; o Vite repassa para FastAPI na porta 8000. Nenhuma chave DeepSeek deve aparecer no frontend.

## 4. Cenários manuais

1. Com `AI_ENABLED=true` no backend e chave local válida, cadastre solicitação fictícia. Observe `aguardando_revisao` na fila.
2. **Aceite** a sugestão da IA. Ela deve desaparecer da fila e aparecer em Concluídas; o GET `/solicitacoes/{id}` precisa mostrar `categoria_final`, `prioridade_final`, `decisao_revisao=aceitar`, `revisado_em`.
3. Cadastre outra solicitação e **corrija** os valores, preenchendo uma observação com pelo menos 10 caracteres. O resultado final deverá refletir a correção, com prioridade calculada pela matriz.
4. Teste `AI_ENABLED=false` no backend (reinicie Uvicorn) e cadastre solicitação. Ela terá `pendente_classificacao` e permitirá **classificação manual** na fila.
5. Atualize o navegador; decisões devem continuar persistidas. Repetir a mesma revisão via HTTP deve devolver `409`.

Use dados fictícios; a aplicação ainda **não possui autenticação/controle de acesso**, então mantenha só localhost.

## 5. Git: somente após testes e entendimento

Na raiz:

```powershell
git status -sb
git diff --check
git check-ignore -v --no-index backend/.env
git ls-files -- backend/.env
```

`git ls-files` acima precisa ficar vazio. Após conferir mudanças:

```powershell
git add -- README.md docs/ARQUITETURA.md docs/PLANO_DE_ESTUDOS_E_DICAS.md
git add -- backend/app/main.py backend/app/triagem.py backend/app/schemas_revisao.py backend/app/routes/revisoes.py backend/sql/003_add_revisao_humana.sql backend/tests/test_revisoes.py
git add -- frontend/.gitignore frontend/index.html frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/src/main.jsx frontend/src/api.js frontend/src/App.jsx frontend/src/styles.css
git diff --cached --name-only
git diff --cached --check
```

Somente se tudo estiver correto:

```powershell
git commit -m "feat: adiciona interface React e revisao humana"
git push origin main
git status -sb
git log -1 --oneline
```

**Não versionar** este prompt privado, `backend/.env`, `frontend/node_modules/` ou `frontend/dist/`.

## Exercícios rápidos

A. Por que o React acessa `/api/revisoes/pendentes` em vez de conectar diretamente ao PostgreSQL?

B. O que faz o proxy do Vite e por que isso ajuda durante o desenvolvimento?

C. Por que a prioridade final é calculada em Python e não confiada ao React?

D. Qual a diferença entre `aguardando_revisao` e `revisada`? Como a falha da IA pode ser resolvida manualmente?

## Status

**13/15 etapas concluídas (86,7% das aulas, não das funcionalidades).** P14 em execução até migração/testes/frontend/commit. P15 pendente: avaliação da LLM, testes ponta a ponta, segurança, métricas, README comercial, auditoria, licença e eventual publicação autorizada.
