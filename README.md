# SolicitaFlow

**Solicitações inteligentes, do pedido à resolução.**

Plataforma de laboratório para gestão de solicitações corporativas: classificação
assistida, encaminhamento validado, atendimento por departamentos, SLA e relatórios.
Evolução do **AI Request Classifier**, preservando o mesmo histórico Git e banco.

[![Verify SolicitaFlow](https://github.com/waldirevora/solicitaflow/actions/workflows/verify.yml/badge.svg)](https://github.com/waldirevora/solicitaflow/actions/workflows/verify.yml)

## Experimente localmente

Com os serviços existentes no Ubuntu/WSL em execução, abra
**http://localhost:5173** e selecione **Explorar laboratório**. Não precisa de senha,
cadastro real ou créditos de IA. Cada visitante recebe um ambiente fictício isolado.

1. Como colaboradora fictícia, envie o **Cenário automático**.
2. Troque para **Tecnologia**, abra o pedido e assuma o atendimento.
3. Registre andamento e avance 6 horas: observe o risco de SLA.
4. Avance mais 8 horas: observe cobrança e escalonamento.
5. Registre a resolução efetiva pelo departamento.
6. Volte à colaboradora para conferir a resposta.
7. Entre como central para consultar pipeline, histórico e relatórios.
8. Experimente o **Cenário ambíguo** e revise a exceção na central.

A troca de personagens só funciona nesse laboratório. Contas locais têm login
próprio e autorização no backend. Simulação é identificada; não é uma chamada real
à DeepSeek. O produto permanece **restrito ao ambiente local**, sem deploy público.

## O que está implementado

| Entrega | Resultado |
| --- | --- |
| UX anterior | Quatro abas clássicas, tutorial e temas Automático/Claro/Escuro |
| V2.1 | Departamentos, destino validado, encaminhamento automático e exceções |
| V2.2 | Portal do Colaborador, Portal do Departamento e Central Operacional |
| V2.3 | Responsável, pipeline, primeira resposta, resolução, SLA e alertas internos |
| V2.4 | Jornada fictícia isolada, relógio virtual, revisão humana e relatório |

A IA sugere categoria, impacto e urgência. Python calcula a prioridade pela matriz
determinística existente. Assuntos inequívocos seguem ao destino ativo; incertezas
e falhas ficam na fila de exceções. A sugestão original é preservada.

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
- [Contrato V2](docs/V2.md): roteamento, autorização, pipeline, SLA e limites.
- [Arquitetura](docs/ARQUITETURA.md): componentes, dados e evolução do MVP.
- [Critérios de classificação](docs/CRITERIOS_CLASSIFICACAO.md): matriz e catálogos.
- [Segurança e evidências](docs/ENTREGA_V2.md): verificações e pendências.

Nunca versione `.env`, `.env.test`, senhas, chaves, dumps ou backups. Não publique
a API local diretamente na internet. Render + Neon continuam uma etapa futura.
