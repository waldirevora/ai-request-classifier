# Relatório de avaliação | AI Request Classifier

**Status:** avaliação exploratória P15 executada; conclusões limitadas aos dez casos fictícios da P12.
**Data da execução:** 16/10/2026 (referência da conversa; confirmar o registro local se necessário).
**Modelo configurado:** `deepseek-flash` (identificador configurado no script; o relatório não comprova revisão interna exata do provedor).
**Ambiente:** laboratório local, chamadas reais à API DeepSeek; sem gravação no PostgreSQL pelo script de avaliação.

## 1. Objetivo de negócio

Medir quanto as sugestões da LLM se aproximam dos rótulos de referência criados na P12. O classificador fornece categoria, impacto e urgência; a prioridade decorre da matriz determinística do Python. O resultado da IA é uma **sugestão**, sujeita à revisão humana, e não a resolução do chamado.

## 2. Método

- Base: `backend/evaluation/casos_referencia.json` (10 solicitações fictícias e classificações esperadas).
- Comando: `python evaluation/avaliar_ia.py --live` executado a partir de `backend`.
- A avaliação chama `app.ia.classificar_solicitacao()` diretamente; não cria solicitações nem altera decisões no PostgreSQL.
- Acerto por dimensão = casos cujo valor previsto coincide com o rótulo esperado / 10.
- Acerto completo = casos cujas **quatro dimensões** coincidem / 10.
- A execução anterior que teve falhas `ErroClassificacao` por conflito de chave foi diagnosticada e corrigida; **não faz parte** dos resultados desta rodada válida.

## 3. Resultados medidos na rodada completa

| Indicador                       |                                                       Resultado |
| ------------------------------- | --------------------------------------------------------------: |
| Casos avaliados                 |                                                              10 |
| Chamadas bem-sucedidas          |                                                    10/10 (100%) |
| Falhas técnicas                 |                                                            0/10 |
| Acerto da categoria             |                                                      9/10 (90%) |
| Acerto do impacto               |                                                      9/10 (90%) |
| Acerto da urgência              |                                                      7/10 (70%) |
| Acerto da prioridade            |                                                      9/10 (90%) |
| **Acerto completo**             |                                                  **6/10 (60%)** |
| Tokens de entrada               |                                                           3.289 |
| Tokens de saída                 |                                                             551 |
| Tokens totais reportados        |                                                           3.840 |
| Latência média da chamada de IA |                                              1.215 ms (1,215 s) |
| Latência mínima                 |                                                        1.039 ms |
| Latência máxima                 |                                                        1.609 ms |
| Custo monetário                 | Não calculado: tarifa e modalidades de cobrança não verificadas |

As métricas representam esta rodada específica e não demonstram latência fim a fim de frontend/HTTP/banco nem custos de produção.

## 4. Divergências identificadas

| Caso | Dimensões divergentes          |
| ---- | ------------------------------ |
| C03  | Urgência                       |
| C05  | Urgência                       |
| C08  | Categoria                      |
| C09  | Impacto, urgência e prioridade |

Quatro dos dez casos exigem revisão. A **urgência** é a dimensão mais frágil nesta amostra, com três divergências. Não é possível determinar, apenas pelo relatório agregado, se cada divergência resulta de interpretação inadequada, ambiguidade do texto ou rótulo de referência discutível. Antes de modificar o prompt, comparar individualmente a descrição, a saída e o motivo do rótulo esperado com as políticas da P12.

## 5. Evidências complementares

- Prévia: `Casos válidos: 10`, sem chamadas à API.
- Regressão: **46 testes Python aprovados em 5,56 s** com `AI_ENABLED=false`.
- Primeiro teste live após corrigir chave: **1/1 completo**, 329 tokens de entrada, 56 de saída, latência de 1.068 ms. **Não somar** essa observação à rodada completa.
- Fallback técnico havia sido observado na P13 e preservou o cadastro durante falha `http_401`.
- Na P15, `npm ci` e `npm run build` passaram (Vite 6.4.4, 25 módulos, 1,16 s), `npm audit` reportou zero vulnerabilidades conhecidas e `pip check` não encontrou requisitos quebrados. O desenvolvedor confirmou novamente que os testes estão funcionando.

## 6. Limitações e próximos ajustes

1. Apenas 10 casos fictícios; amostra insuficiente para estimar qualidade real ou SLAs.
2. Sem comparação de saídas caso a caso anexada; revisar as quatro divergências e a consistência dos rótulos.
3. Nenhuma repetição da rodada para medir variabilidade e confiabilidade estatística.
4. Sem avaliação sistemática de casos adversariais/prompt injection, privacidade e resistência a ambiguidades.
5. Ausência de autenticação/autorização, identificação verificável do revisor e testes de carga impede tratar o produto como produção.
6. Não inferir custo financeiro sem tarifa atual, regras de cache e modalidades de tokens do provedor.

**Leitura das divergências:** C03 e C05 apresentam prazos na próxima semana, permitindo interpretações diferentes de urgência; C08 envolve fronteira RH/Financeiro; C09 não explicita o alcance da reunião. Os valores individuais previstos não foram apresentados, portanto não se deve atribuir conclusões definitivas sobre o comportamento do modelo. Não alterar rótulos apenas para elevar a taxa.

**Condição final:** testes, build, auditoria npm e varredura de segredos foram concluídos; `requirements-dev.txt` mantém `httpx2` conforme ambiente validado. MIT aprovada. Faltam commit/push da documentação e autorização explícita antes de tornar público o repositório. O custo monetário segue não medido.
