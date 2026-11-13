# Entrega SolicitaFlow V2 — 12/11/2026

> **Registro histórico.** Este documento preserva o estado, os testes e as decisões
> da etapa em que foi produzido. Menções a operação somente local, publicação futura,
> simulação ou pendências valem para aquela etapa. O serviço atual está publicado;
> consulte [README](../README.md), [deploy e manutenção](DEPLOY_PUBLICO.md) e
> [encerramento do marco](ENCERRAMENTO.md) antes de executar qualquer roteiro antigo.

## Git e preservação

O mesmo repositório foi renomeado para
[waldirevora/solicitaflow](https://github.com/waldirevora/solicitaflow).
O identificador GitHub continua `1416308738`; commits anteriores e PRs permanecem.
A cópia Linux é a instalação ativa. A cópia Windows foi preservada e seu origin
atualizado; seus arquivos não foram sobrescritos com o desenvolvimento Linux.

| Entrega | Commit de implementação | PR |
| --- | --- | --- |
| Redesign anterior | eb4e381 | [#1](https://github.com/waldirevora/solicitaflow/pull/1) |
| Identidade | 9e748d1 | [#2](https://github.com/waldirevora/solicitaflow/pull/2) |
| Roteamento | 6610f60 | [#3](https://github.com/waldirevora/solicitaflow/pull/3) |
| Portais | 2a6a27a | [#4](https://github.com/waldirevora/solicitaflow/pull/4) |
| Workflow e SLA | 74d4846 | [#5](https://github.com/waldirevora/solicitaflow/pull/5) |
| Laboratório | fd4a395 | [#6](https://github.com/waldirevora/solicitaflow/pull/6) |
| Guards de recursos | d6e8cd2 | [#7](https://github.com/waldirevora/solicitaflow/pull/7) |
| CI | e47ef97 + d2ba74d | [#8](https://github.com/waldirevora/solicitaflow/pull/8) |
| Histórico, responsável e SLA visíveis | aeec188 | [#9](https://github.com/waldirevora/solicitaflow/pull/9) |
| Consistência do relógio fictício | f9ab072 | [#10](https://github.com/waldirevora/solicitaflow/pull/10) |

As entregas foram integradas por merge normal, sem force push, reset de histórico,
bypass de proteção ou merges com testes falhando. Antes do CI, os PRs tinham
evidência local explícita; não existiam checks remotos configurados.

Os arquivos locais `backend/.dockerignore`, `backend/Dockerfile` e
`backend/migrate.py` de Railway continuam preservados, fora das entregas.
Não são recomendados para execução: imagem/root/porta precisam de revisão;
o migrador antigo modifica transações e não foi validado para a arquitetura atual.
Nenhum PR artificial foi criado para publicá-los.

## Evidências executadas

- Backend: **71 testes aprovados**, sem chamadas reais à IA. Os 50 testes anteriores
  permanecem; cobertura adicional inclui roteamento, concorrência, falha de provedor,
  cotas, autorização, transições, SLA, relatórios e isolamento do laboratório.
- Frontend: **15 testes aprovados**; contrato da matriz Python continua verificado.
- Build de produção Vite aprovado.
- Chromium local: jornada de 17 passos, dois visitantes isolados, cenário automático
  e ambíguo, resolução e relatório. Também executado cadastro/atendimento por contas locais.
- Temas Claro/Escuro/Automático, com alteração simulada de preferência do sistema e sincronização ao retornar da triagem clássica.
- Larguras 1440, 768 e 390, sem rolagem horizontal indevida no documento.
- Axe WCAG A/AA: zero violações nos estados desktop claro/escuro e mobile escuro
  capturados. Isso não equivale a uma certificação completa de acessibilidade.
- Navegação por teclado/foco foi exercitada; labels e estados são semânticos.
- Windows PowerShell confirmou HTTP 200 no frontend, Swagger e proxy usando localhost.
- Nenhuma chamada paga nova à DeepSeek nesta entrega.

O [CI aprovado](https://github.com/waldirevora/solicitaflow/actions/runs/43317010620)
executou a mesma base sobre PostgreSQL 18 efêmero, preservando um registro anterior
às migrações. A primeira tentativa falhou no sandbox do Chromium do runner; a
correção usa Chrome do runner mantendo `chromium_sandbox=True`. Também mascara
as credenciais efêmeras geradas pelo job. Não usa credenciais locais.

Referências de configuração: [serviços PostgreSQL no GitHub Actions](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers),
[canais de navegador Playwright](https://playwright.dev/python/docs/api/class-browsertype).

## Banco e segurança

Migrações 004, 005 e 006 aplicadas em principal/testes, com transações e checksum.
Cada aplicação comparou snapshot de todas as solicitações antes/depois. A tabela
original mantém suas 22 colunas. PostgreSQL não foi reinstalado ou reconfigurado.
Os testes não alteraram o principal. Nenhuma solicitação preexistente foi removida.

Controles implementados: sessões opacas com hash, scrypt, cookies HttpOnly/Strict,
origens locais nas mutações, autorização por recurso, FKs de ambiente, proteção
do legado, decisão única de roteamento, eventos somente INSERT/SELECT pela app,
limites locais e reserva atômica de IA. Laboratório não acessa IA real.
Senhas/chaves permanecem fora do Git e do frontend.

Limites materiais: HTTP local utiliza cookie sem Secure; identidade corporativa,
retenção/expurgo, recuperação de conta, MFA, limites distribuídos, backup restaurado,
observabilidade e avaliação de classificações exigem entregas adicionais antes
de uma demonstração pública. A triagem clássica, restrita à central local, mantém
a integração DeepSeek anterior; sua criação de pedidos pode consumir créditos.
Os formulários V2 e o laboratório usam simulação sem custos.

## Operação e artefatos locais

Controlador: `scripts/local_services.py`, executado com `backend/.venv/bin/python`.
Comandos `start`, `status`, `restart-backend`, `test`, `stop`. Não gerencia PostgreSQL.
Scheduler: `scripts/check_sla.py --interval 60`, com PID/log em diretório privado.
Para demonstração, abra http://localhost:5173 e use **Explorar laboratório**.

Evidências privadas da execução:
`~/.local/share/ai-request-classifier/solicitaflow-v2/`.
Contém ledger de PRs/commits, comprovação da renomeação, migrações, capturas e
resultados de navegador. A subpasta `captures/` contém estados desktop/mobile;
`ci-captures/` guarda os artefatos do CI. Nenhum dump ou credencial foi versionado.
O arquivo `local-accounts.json` é privado e não deve ser exibido ou compartilhado.

O produto é um laboratório local completo. Não houve deploy público, alteração
de PostgreSQL 16, APT/systemd, Docker ou infraestrutura gerenciada.
