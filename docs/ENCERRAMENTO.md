# Encerramento do marco de desenvolvimento e implantação

**Marco concluído:** SolicitaFlow publicado em
[https://solicitaflow.onrender.com](https://solicitaflow.onrender.com), com funcionamento
da demonstração confirmado pelo proprietário. O encerramento reconcilia documentos
e Git/GitHub, sem novas funcionalidades, migrações ou mudanças de infraestrutura.
Permanecem apenas responsabilidades operacionais e eventuais entregas futuras
independentes, sujeitas a escopo próprio.

## Baseline e preservação do histórico

| Referência | Significado |
| --- | --- |
| `v2.6.1` → `8acaf71ef36bc74de353a248ddd100318f21a67e` | Tag histórica da entrega visual, PR #14; preservada |
| `aa13db2` | Consolidação pré-deploy; registro histórico em PRE_DEPLOY.md |
| `e8944877d1d208a24cf0061ea5caa3c417f69d87` | Código funcional publicado no Render |
| Commit/PR de encerramento posterior | Somente README e docs; main atualizada sem redeploy |

| Entrega de deploy | Commit de implementação | PR integrado |
| --- | --- | --- |
| Origem HTTPS única, controles e operação | `692a25e` | [#16](https://github.com/waldirevora/solicitaflow/pull/16) |
| Validação TLS na fronteira Neon | `d2c72fe` | [#17](https://github.com/waldirevora/solicitaflow/pull/17) |
| Privilégio mínimo de row-lock e falhas seguras | `2bd19ba` | [#18](https://github.com/waldirevora/solicitaflow/pull/18) |

O [CI aprovado do baseline](https://github.com/waldirevora/solicitaflow/actions/runs/43471847935)
corresponde ao SHA funcional publicado. O CI do PR de encerramento valida novamente
os documentos e a regressão existente. Os checks da main estão no
[workflow Verify SolicitaFlow](https://github.com/waldirevora/solicitaflow/actions/workflows/verify.yml).
Como auto-deploy está desabilitado, a main documental e o runtime têm SHAs distintos
sem divergência de código executável. Não mover a tag histórica para o encerramento.

Branches, cópia Windows e arquivos legados foram preservados. Nenhum force-push,
reset destrutivo ou exclusão de branches faz parte deste marco.

## Evidências comprovadas da publicação

| Área | Resultado registrado |
| --- | --- |
| Backend | 104 testes aprovados, sem consumo real de IA nos testes automatizados |
| Frontend | 32 testes aprovados e build de produção validado |
| CI / migrações | PostgreSQL 18 efêmero, compatibilidade com registro legado, 001–007, rerun/checksums e privilégios |
| Navegador com mocks | Jornada existente de 17 passos e jornada HTTPS compilada de 17 passos; temas, SLA, falhas e isolamento |
| URL pública | HTTPS verificado, acesso sem token operacional, sessão retomada após reload/redeploy e acesso cruzado negado |
| Interface pública | Nove capturas desktop/mobile e nove estados axe sem violações; Claro/Escuro/Automático, teclado e relatório |
| Banco público | PostgreSQL 18.7 na homologação; TLS verificado, 22 colunas originais, 16 tabelas, ownership e roles mínimas |
| Backup/restauração | Backup pré-liberação criptografado, 16 tabelas e 114 registros comparados em banco novo isolado |
| Retenção | Role limitada testada na cópia restaurada: anonimização de dois laboratórios expirados e expurgo de um antigo; origem preservada |

As contagens representam execuções comprovadas, não cobertura integral, certificação
WCAG/pentest ou garantia de desempenho empresarial. A jornada completa na nuvem foi
exercitada por HTTP; a jornada completa de UI foi exercitada com mocks. A validação
visual na URL pública bloqueou novos envios pagos.

As duas classificações reais controladas usaram apenas dados fictícios e retornaram
o modelo `deepseek-flash`: 722 tokens de entrada e 127 de saída. Pedido claro foi
encaminhado à TI; pedido ambíguo foi para revisão. Atendimento, SLA, escalonamento,
resolução e relatório foram validados sem novas chamadas. Reenvios antes/depois de
reinício não duplicaram consumo; a cota preservou um pedido sem nova análise.

A reserva contábil foi US$ 0,005901. Não é o valor faturado. A estimativa máxima dos
tokens, pelos preços peak/cache-miss consultados na publicação, foi US$ 0,000369;
a consulta de saldo não teve precisão para comprovar o custo exato. Não atribuir
uma revisão interna do modelo além do identificador retornado ou generalizar esses
dois casos como avaliação estatística. Não houve nova classificação paga para
encerrar a documentação.

## Documentação e artefatos

O [README](../README.md) é a entrada do portfólio. [Arquitetura](ARQUITETURA.md),
[Guia local](GUIA.md), [Segurança](SEGURANCA.md), [Deploy e manutenção](DEPLOY_PUBLICO.md)
e [Critérios](CRITERIOS_CLASSIFICACAO.md) descrevem o estado atual. Relatos V2–V2.6.1,
pré-deploy, plano de estudos e avaliação exploratória mantêm seu conteúdo histórico
com identificação explícita; seus números e restrições não são defaults de produção.

O relatório detalhado original e as capturas estão no armazenamento privado do
operador: `~/.local/share/ai-request-classifier/public-deploy/`. Eles não são copiados
integralmente ao Git. Credenciais, cookies, dumps, chaves de backup, logs e capturas
privadas permanecem fora do repositório. Referências a ferramentas privadas não
constituem um instalador universal; usar os entry points versionados e os provedores
autenticados conforme o guia de deploy.

## Manutenção após o desenvolvimento concluído

| Responsabilidade legítima | Procedimento |
| --- | --- |
| Disponibilidade e franquias | Acompanhar Render/Neon; respeitar suspensão nativa, cold start e ausência de SLA de produção |
| Crédito e consumo | Conferir ledger/conta DeepSeek; preservar cotas e investigar reservas desconhecidas sem retry automático |
| Backups | Rotina manual, quiescência antes do manifesto/dump, cópias separadas de chave/arquivo e restauração isolada |
| Retenção | Acompanhar limpeza por atividade e política manual dos backups; não prometer expurgo imediato durante ociosidade |
| Segurança e dependências | Revisar incidentes/atualizações em entregas próprias com testes; avaliar consumidores antes de revogar chave compartilhada |
| Releases futuras | Branch/PR/CI, autorização operacional, backup e deploy de SHA aprovado; não confundir merge documental com release |

**Nenhum gatilho periódico do Neon ou keep-alive foi instalado.** Não implementá-lo
como condição para encerrar o marco. O scheduler local não foi transferido ao Render.

Uma orientação textual secundária no cartão da análise pode continuar sugerindo
entrar no departamento após a resolução, embora status e orientação principal já
mostrem a conclusão. É um ajuste futuro de UX, não bloqueante e não implementado
nesta entrega documental. Não há nova funcionalidade pendente como condição de
conclusão deste marco; manutenção não representa reabertura do desenvolvimento.
