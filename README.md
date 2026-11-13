# SolicitaFlow

**Solicitações inteligentes, do pedido à resolução.**

Demonstração profissional de uma solução corporativa personalizada com inteligência
artificial, automação e acompanhamento de solicitações. **Não é um SaaS operado
continuamente.** A base evolui do AI Request Classifier, preservando histórico e dados.

A V2.6 usa **DeepSeek real** nos novos envios, com orçamento global e limites no
backend. Empresa, personagens, atendimento e relógio são demonstrativos. Dados
sensíveis não devem ser enviados. Leia o [contrato V2.6](docs/V2_6.md).

[![Verify SolicitaFlow](https://github.com/waldirevora/solicitaflow/actions/workflows/verify.yml/badge.svg)](https://github.com/waldirevora/solicitaflow/actions/workflows/verify.yml)

## Experimente localmente

Com os serviços existentes no Ubuntu/WSL em execução, abra
**http://localhost:5173** e selecione **Experimentar o SolicitaFlow**. Não precisa de login ou cadastro pessoal. As chamadas de IA são reais, limitadas e custeadas pelo responsável pela demonstração. Cada visitante recebe um ambiente fictício isolado. Uma sessão válida é retomada sem nova criação ao recarregar ou entrar novamente.

1. Como colaboradora fictícia, envie o **Exemplo de TI**.
2. Troque para **Tecnologia**, abra o pedido e assuma o atendimento.
3. Registre andamento e avance 6 horas: observe o risco de SLA.
4. Avance mais 8 horas: observe cobrança e escalonamento.
5. Registre a resolução efetiva pelo departamento.
6. Volte à colaboradora para conferir a resposta.
7. Entre como central para consultar pipeline, histórico e relatórios.
8. Experimente o **Exemplo com dois assuntos** e revise a exceção na central.

A troca de personagens só funciona nesse laboratório. Contas locais têm login
próprio e autorização no backend. A análise DeepSeek é real; falhas ou cotas são informadas sem resposta inventada. O produto permanece **restrito ao ambiente local**, sem deploy público.

Leia também [V2.5 — primeiro acesso e laboratório](docs/V2_5.md) para conhecer a retomada, os limites e a nova home educativa.

## O que está implementado

| Entrega | Resultado |
| --- | --- |
| UX anterior | Quatro abas clássicas, tutorial e temas Automático/Claro/Escuro |
| V2.1 | Departamentos, destino validado, encaminhamento automático e exceções |
| V2.2 | Portal do Colaborador, Portal do Departamento e Central Operacional |
| V2.3 | Responsável, pipeline, primeira resposta, resolução, SLA e alertas internos |
| V2.4 | Jornada fictícia isolada, relógio virtual, revisão humana e relatório |
| V2.5 | Onboarding, sessão retomável, home educativa e tipografia acessível |
| V2.6 | Portfólio B2B, IA real, reservas globais de custo e progresso auditável |
| V2.6.1 | Marca própria, favicons, FAQ centralizado e tema inicial Escuro |

A IA sugere categoria, impacto e urgência. Python calcula a prioridade pela matriz
determinística existente. Assuntos inequívocos seguem ao destino ativo; incertezas
e falhas ficam na fila de exceções. A sugestão original é preservada.

## Baseline para a próxima fase

A V2.6.1 corresponde ao merge `8acaf71` (PR #14). A consolidação posterior corrige
exemplos, documentação e a dependência de testes; não é um deploy nem migra o banco.
Veja a [auditoria e os bloqueios de publicação](docs/PRE_DEPLOY.md). A tag `v2.6.1`,
quando presente, identifica o commit da versão, não o baseline posterior de preparação.

Os templates `backend/.env.example` e `backend/.env.test.example` usam porta 5432 e
roles limitadas distintas. Copie-os apenas para uma instalação nova; não sobrescreva
credenciais locais já existentes. Ambos deixam chamadas reais de IA desabilitadas.

## Stack e execução

React 19, Vite 6, Python 3.12, FastAPI, PostgreSQL 18 e integração DeepSeek no backend.
Na instalação recuperada, binários/credenciais locais continuam nos caminhos
históricos; a mudança de marca não renomeia bancos, tabelas ou diretórios.

```bash
cd ~/projects/ai-request-classifier
backend/.venv/bin/python scripts/local_services.py start
backend/.venv/bin/python scripts/local_services.py status
```

O comando valida a conexão existente e inicia somente backend, frontend e scheduler.
Ele **não administra PostgreSQL**. Se o banco estiver parado, falha sem alterar sua
instalação. Processos usam loopback e continuam enquanto o WSL e os processos
permanecerem ativos. Não há promessa de persistência após desligar o WSL.

- Interface: http://localhost:5173
- Swagger: http://localhost:8000/docs
- Saúde via proxy: http://localhost:5173/api/health

Para encerrar somente os três processos da aplicação:

```bash
backend/.venv/bin/python scripts/local_services.py stop
```

## Verificação

```bash
backend/.venv/bin/python scripts/local_services.py test
export PATH="$HOME/.local/opt/ai-request-classifier/node/bin:$PATH"
cd frontend
npm ci
npm test
npm run build
```

O comando de backend confirma identidade, porta, versão, role e isolamento antes
de qualquer limpeza do banco de testes. Também confere que o snapshot do principal
não mudou. Chamadas reais à IA são bloqueadas durante pytest.

O CI executa as migrações sobre PostgreSQL 18 efêmero, preserva um registro legado,
testa rerun/checksums e roda backend, frontend, build e jornada de navegador com axe.
Capturas ficam nos artefatos do workflow, sem credenciais ou dumps.

## Documentação

- [Guia operacional](docs/GUIA.md): ambiente, comandos, contas e testes.
- [Consolidação pré-deploy](docs/PRE_DEPLOY.md): branches, arquivos legados, segurança e viabilidade.
- [V2.6.1](docs/V2_6_1.md): marca, FAQ e preferência inicial Escuro.
- [V2.6 e controle de IA](docs/V2_6.md): experiência comercial, limites e testes.
- [Contrato V2 histórico](docs/V2.md): roteamento, autorização, pipeline, SLA e limites.
- [Arquitetura](docs/ARQUITETURA.md): componentes, dados e evolução do MVP.
- [Critérios de classificação](docs/CRITERIOS_CLASSIFICACAO.md): matriz e catálogos.
- [Segurança e evidências](docs/ENTREGA_V2.md): verificações e pendências.

Nunca versione `.env`, `.env.test`, senhas, chaves, dumps ou backups. Não publique
a API local diretamente na internet. Render + Neon continuam uma etapa futura.

O teste de navegador agora exige backend de QA com mocks e recusa o serviço real.
Use `scripts/qa_local.py start`, `scripts/qa_local.py browser` e
`scripts/qa_local.py stop` com o Python do backend. Isso reinicia somente o banco
**de testes**, não o principal. Não execute pytest e QA de navegador em paralelo.
O contato comercial usa apenas `SF_CONTACT_URL` confirmado pelo proprietário;
nenhum endereço é presumido. Sem esse valor, o botão de contato não é mostrado.

## Demonstração pública controlada

A preparação para uma origem HTTPS única no Render Free e banco separado no Neon Free está descrita em [Deploy público](docs/DEPLOY_PUBLICO.md). O serviço inicia em manutenção, com IA desligada. A instalação local continua independente. Não use Vite como servidor público.
