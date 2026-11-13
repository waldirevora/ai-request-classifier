# Critérios de classificação | SolicitaFlow

**Revisão documental:** publicação do SolicitaFlow — 13/11/2026. A matriz original foi definida na etapa histórica P12 e permanece inalterada.
**Estado:** integrada ao backend e ao tutorial; parâmetros de laboratório, sem validação de política empresarial real.

## 1. Finalidade

Definir categoria, impacto e urgência com valores verificáveis. A DeepSeek sugere os três campos e uma justificativa; Python calcula a prioridade. Na V2, o backend também confere suficiência, assunto e destino ativo antes de encaminhar. Ambiguidades e falhas exigem revisão humana, preservando a sugestão original. **Classificação não equivale à resolução.** Somente o departamento confirma resolução após atendimento.

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

Verificamos automaticamente:

- O catálogo de categorias e prioridades é consistente.
- A matriz produz resultados previsíveis para as nove combinações impacto × urgência.
- Todos os casos têm identificadores únicos, dados completos e rótulos aceitos pela taxonomia.
- A prioridade esperada é compatível com a matriz.

**Não há avaliação estatística de acurácia publicada.** Os testes de contrato e as demonstrações fictícias não substituem um corpus rotulado e revisado por especialistas. A evolução atual valida esquema, regras, falhas e fluxo. Para avaliar classificações reais, medir acertos por categoria/impacto/urgência e divergências humanas com dados autorizados e orçamento explícito.

## 6. Roteamento e limites

A V2 exige categoria compatível com evidências do texto, descrição suficiente e mapeamento ativo no mesmo ambiente. Não usa escore autodeclarado pelo modelo. Casos com múltiplos assuntos, categoria `outros`, informações insuficientes, destino inválido ou falha da IA vão para exceção. A heurística conservadora precisa de avaliação antes de uso empresarial.

A tabela original tem 22 colunas após as migrações 001–003. O workflow e suas relações são aditivos em `sf_*`; a classificação é confirmada após persistir o pedido. Novos envios da demonstração tentam análise DeepSeek real pelo backend, dentro das cotas. Quando a análise não ocorre ou falha, o pedido é preservado sem sugestão fabricada. Simulação fica restrita a tutoriais, registros históricos identificados e testes automatizados com mocks.

Prioridade não é política completa de SLA nem autorização de resolução. O laboratório usa políticas fictícias de prazo, com revisão humana reservada às exceções. A matriz e os catálogos permanecem inalterados nesta revisão. O serviço está [publicado](https://solicitaflow.onrender.com); [Arquitetura](ARQUITETURA.md), [Segurança](SEGURANCA.md) e [Deploy](DEPLOY_PUBLICO.md) documentam as fronteiras atuais. P12–P15 e os contratos V2 continuam preservados como histórico.
