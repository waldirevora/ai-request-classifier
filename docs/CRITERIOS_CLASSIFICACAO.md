# Critérios de classificação | AI Request Classifier

**Versão:** P12 / atualização 3.52 — 15/10/2026
**Estado:** proposta didática, ainda não conectada à API nem validada por especialistas da empresa.

## 1. Finalidade

Definir uma taxonomia pequena e verificável de **categoria**, **impacto**, **urgência** e **prioridade**, antes de integrar uma LLM. Ao classificar automaticamente no futuro, o modelo deverá sugerir valores do catálogo e justificar a decisão; o analista poderá aceitar ou corrigir. **Classificação não equivale à resolução do chamado.**

## 2. Categorias (o assunto da solicitação)

| Código               | Categoria            | Uso típico                                             |
| -------------------- | -------------------- | ------------------------------------------------------ |
| `suporte_ti`         | Suporte de TI        | Hardware, software, equipamentos e falhas técnicas     |
| `acessos_permissoes` | Acessos e permissões | Criação, bloqueio e revisão de acessos a sistemas      |
| `financeiro`         | Financeiro           | Pagamentos, cobranças e reembolsos                     |
| `recursos_humanos`   | Recursos Humanos     | Cadastro, folha de pagamento e benefícios de pessoal   |
| `outros`             | Outros               | Demandas que não se encaixam nas categorias anteriores |

**Regra:** escolher a categoria correspondente ao assunto principal do pedido. Por exemplo, _bloqueio de acesso ao ERP_ é `acessos_permissoes`, mesmo envolvendo um sistema de TI. A categoria `outros` deve ser usada com justificativa, não como solução automática para dúvida.

## 3. Impacto e urgência (dimensões distintas)

| Dimensão | Valor        | Interpretação de referência                                       |
| -------- | ------------ | ----------------------------------------------------------------- |
| Impacto  | `individual` | Afeta predominantemente uma pessoa                                |
| Impacto  | `equipe`     | Afeta um grupo/setor ou operação coletiva                         |
| Impacto  | `empresa`    | Afeta grande parte da organização ou processo empresarial crítico |
| Urgência | `baixa`      | Há tempo suficiente e não existe bloqueio imediato                |
| Urgência | `media`      | Existe prazo próximo ou prejuízo operacional limitado             |
| Urgência | `alta`       | Bloqueio atual ou prazo iminente com consequência relevante       |

**Não usar somente adjetivos** como “urgente”, “grave” ou “importante” sem evidências descritas. A prioridade depende do contexto. Quando faltarem informações sobre impacto ou prazo, a IA deverá declarar a incerteza e a revisão humana poderá solicitar dados adicionais.

## 4. Matriz inicial de prioridade

| Impacto \ Urgência | Baixa   | Média   | Alta    |
| ------------------ | ------- | ------- | ------- |
| Individual         | `baixa` | `baixa` | `media` |
| Equipe             | `baixa` | `media` | `alta`  |
| Empresa            | `media` | `alta`  | `alta`  |

**Exemplo:** uma única pessoa sem acesso, mas com alternativa de trabalho, tende a prioridade baixa; uma equipe inteira impedida de trabalhar agora pode ser alta. A matriz é um **ponto de partida para exercícios**, não uma política de SLA aprovada por uma empresa. Poderá mudar conforme o domínio real.

## 5. Casos de referência e avaliação

Os casos estão em `backend/evaluation/casos_referencia.json` (10 registros sintéticos, IDs `C01`–`C10`). Cada registro contém título, descrição, categoria esperada, impacto, urgência, prioridade e justificativa esperada.

Nesta P12 verificamos automaticamente:

- O catálogo de categorias e prioridades é consistente.
- A matriz produz resultados previsíveis para as nove combinações impacto × urgência.
- Todos os casos têm identificadores únicos, dados completos e rótulos aceitos pela taxonomia.
- A prioridade esperada é compatível com a matriz.

**Não medimos acurácia de IA ainda.** Nenhum modelo está recebendo esses casos. Em aulas futuras, será possível comparar a saída do modelo com rótulos de referência e calcular acertos por categoria/prioridade, além de avaliar a qualidade da justificativa. Para conjuntos maiores, usar dados anonimizados ou sintéticos e revisar divergências humanas.

## 6. Limites, próximos passos e formato do curso

- A API CRUD continuará armazenando somente `titulo`, `descricao`, `status` e `criado_em` além do ID; P12 **não altera banco, payload ou endpoints**.
- Não acrescentar botão de “classificar”: a IA será acionada automaticamente pelo backend em etapa futura, após registrar o chamado.
- Prioridade é uma sugestão de triagem, não autorização automática para executar ou resolver ações.
- P13 reunirá LLM, custo/latência, acionamento automático, persistência e tratamento de falhas. P14 reunirá API de revisão humana, React e integração. P15 cobrirá qualidade, segurança, documentação comercial, demonstração e auditoria/publicação autorizada.
- O GitHub permanece privado até o fim do desenvolvimento e posterior auditoria/autorização.

**Novo formato:** aulas mais breves e completas; quatro etapas P12–P15 até o MVP, com status de pendências ao final de cada aula. Regras da P12 não alteram API nem PostgreSQL.
