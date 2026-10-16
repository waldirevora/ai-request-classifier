# GUIA | AI Request Classifier

**Documento oficial:** `docs/GUIA.md` (nome e caminho permanentes; sempre substituir o conteúdo integral).
**Etapa:** P15 em execução. **Projeto privado.**
**Uso:** laboratório local de Engenharia de IA; dados de solicitação fictícios.

## 1. O que o MVP faz

O funcionário cadastra uma solicitação na interface React. A FastAPI valida e persiste o cadastro no PostgreSQL antes de solicitar à DeepSeek uma proposta de categoria, impacto, urgência e justificativa. A matriz de negócio P12 determina a prioridade. Um analista aceita ou corrige a classificação e o PostgreSQL registra o resultado final. Se a IA falhar, o cadastro é preservado e a revisão manual continua disponível. **Classificação não é resolução do chamado.**

## 2. Executar localmente

Pré-requisitos: PostgreSQL Windows no host `127.0.0.1` e porta `5433`, bases `ai_request_classifier` e `ai_request_classifier_test`, SQL 001/002/003 já aplicados, Python em `backend/.venv` e Node.js.

Terminal 1 (backend):

```powershell
cd D:\Projects\ai-request-classifier\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Terminal 2 (React):

```powershell
cd D:\Projects\ai-request-classifier\frontend
npm ci
npm run dev
```

- Frontend: http://127.0.0.1:5173/
- Swagger: http://127.0.0.1:8000/docs
- O proxy Vite encaminha `/api/*` para FastAPI local na porta 8000.
- Chave DeepSeek somente em `backend/.env`, nunca no Git ou no React.

## 3. Verificações automáticas da P15

Na pasta `backend`, os testes usam `ai_request_classifier_test`, cuja tabela de solicitações é **apagada e reiniciada** automaticamente. Nunca aponte os testes para o banco principal.

```powershell
cd D:\Projects\ai-request-classifier\backend
$env:AI_ENABLED = "false"
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:\AI_ENABLED -ErrorAction SilentlyContinue
```

Em outro terminal:

```powershell
cd D:\Projects\ai-request-classifier\frontend
npm ci
npm run build
npm audit
```

P14: **41 testes aprovados** e build validado. P15: **46 testes Python aprovados em 5,56 s**, posteriormente confirmados como funcionando; `pip check` sem conflitos; `npm ci` e `npm run build` aprovados, `npm audit` reportou 0 vulnerabilidades conhecidas. Não repetir testes aprovados sem mudança técnica relevante.

## 4. Avaliação da IA com os dez casos de referência

Esta avaliação chama diretamente `app.ia.classificar_solicitacao()` (sem `POST /solicitacoes`), portanto **não insere nem altera linhas no PostgreSQL**. Compara categoria, impacto, urgência e prioridade com os rótulos de `backend/evaluation/casos_referencia.json`.

Prévia **sem rede e sem custo**:

```powershell
cd D:\Projects\ai-request-classifier\backend
.\.venv\Scripts\python.exe evaluation\avaliar_ia.py
```

Chamada **real, autorizada pelo comando explícito**, com dez solicitações fictícias (pode consumir créditos):

```powershell
.\.venv\Scripts\python.exe evaluation\avaliar_ia.py --live
```

Para amostra menor, por exemplo duas chamadas reais:

```powershell
.\.venv\Scripts\python.exe evaluation\avaliar_ia.py --live --limit 2
```

A chamada ignora o interruptor `AI_ENABLED` do fluxo de cadastro; `--live` aciona diretamente a função de IA e requer `DEEPSEEK_API_KEY` disponível no `backend/.env`. **Não compartilhe a chave.** Em caso de conflito com variável PowerShell: `Remove-Item Env:\DEEPSEEK_API_KEY -ErrorAction SilentlyContinue` no terminal em que rodará a avaliação.

Resultados exibidos: acerto por campo, acerto completo, falhas técnicas, tokens de entrada/saída e latências. **Medição P15 concluída:** 10/10 chamadas bem-sucedidas; categoria 90%, impacto 90%, urgência 70%, prioridade 90%, acerto completo 60%; 3.289 tokens entrada, 551 saída e 1.215 ms de latência média. Divergências C03, C05, C08 e C09. Ver `docs/RELATORIO_AVALIACAO.md`. O denominador inclui falhas. Não calcular custo monetário sem tarifa atual e modalidades de cobrança. Dez casos fictícios não estimam qualidade em produção.

## 5. Dependências Python verificadas

O arquivo `backend/requirements.txt` inclui `fastapi`, `uvicorn`, `pydantic`, `psycopg[binary]` e `python-dotenv`. A inclusão explícita de `pydantic` é intencional. O `backend/requirements-dev.txt` permanece com `-r requirements.txt`, `pytest` e **`httpx2`**, conforme a configuração local testada pelo desenvolvedor; não substituí-lo automaticamente por outra biblioteca. `pip check` retornou `No broken requirements found.`

Uma instalação em máquina diferente deve repetir a instalação, `pip check` e a suíte de testes; a validação atual não representa compatibilidade universal de versões futuras.

## 6. Teste ponta a ponta (manual)

1. Com FastAPI e React em execução, cadastre solicitação fictícia e confirme resposta `201`.
2. Se a IA estiver ativa, verifique `aguardando_revisao` e sugestão completa; se estiver desligada/indisponível, verifique `pendente_classificacao` ou `classificacao_falhou`.
3. Aceite ou corrija a classificação no React. A prioridade final deve seguir a matriz P12.
4. Atualize a página; confira o registro no histórico e em `GET /solicitacoes/{id}`.
5. Repetir a decisão deve retornar `409 Conflict`; valores inválidos devem gerar `422`.
6. Não usar dados reais ou pessoais, nem expor `localhost` por túnel público.

## 7. Auditoria antes de publicar o repositório

Na raiz do projeto:

```powershell
git status -sb
git diff --check
git check-ignore -v --no-index backend/.env frontend/node_modules frontend/dist
git ls-files -- backend/.env
```

O último comando deve ficar vazio. Faça varredura também do **histórico** (Git atual limpo não prova histórico limpo), com ferramenta de detecção de segredos e inspeção dos resultados sem imprimir credenciais. Não publicar arquivos `.env`, chaves, relatórios locais com conteúdo sensível ou o prompt privado de continuidade.

O GitHub pode ficar público **como código-fonte**, mas isso não autoriza implantar a aplicação na internet. Este MVP não oferece login, autorização, identificação de revisores ou controles de produção. Hospedagem pública exigirá controles adicionais.

## 8. Fechamento Git e licença MIT

- **Licença escolhida:** MIT, arquivo completo `LICENSE` na raiz, atribuição `Copyright (c) 2026 waldirevora` (revisar titular, se necessário).
- **Segurança verificada:** Gitleaks examinou 16 commits e cerca de 275 KB em `git --redact --log-opts="--all"`, sem segredos detectados. `.env`, `node_modules` e `dist` ignorados. A varredura não garante ausência de todas as vulnerabilidades.
- **IA avaliada:** 10/10 chamadas bem-sucedidas, 60% de acerto completo; casos C03, C05, C08 e C09 analisados qualitativamente, sem alterar rótulos para elevar a pontuação.
- **Documentos completos:** `README.md`, `docs/ARQUITETURA.md`, `docs/GUIA.md`, `docs/PLANO_DE_ESTUDOS_E_DICAS.md` e `docs/RELATORIO_AVALIACAO.md`.
- **Antes do commit:** verificar `git status -sb`, `git diff --check`, `git diff --cached --name-only`, `git diff --cached --check` e possíveis segredos nos arquivos novos. Usar staging seletivo.
- **Após o push:** conferir `git status -sb` e o hash do último commit. Manter repositório privado até autorização explícita.

## 9. Status

**14/15 etapas concluídas (93,3% por etapas de estudo).** P15 em fechamento: avaliação, testes, dependências, frontend e varredura de segredos concluídos conforme evidências. Falta adicionar a licença e os documentos ao Git, revisar o staging e realizar commit/push. A publicação do código depende de autorização explícita; a aplicação continua restrita a localhost, sem autenticação.
