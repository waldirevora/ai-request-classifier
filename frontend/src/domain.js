export const CATEGORIES = [
  ["suporte_ti", "Suporte de TI"],
  ["acessos_permissoes", "Acessos e permissões"],
  ["financeiro", "Financeiro"],
  ["recursos_humanos", "Recursos Humanos"],
  ["outros", "Outros"],
];
export const IMPACTS = [
  ["individual", "Individual"],
  ["equipe", "Equipe"],
  ["empresa", "Empresa"],
];
export const URGENCIES = [
  ["baixa", "Baixa"],
  ["media", "Média"],
  ["alta", "Alta"],
];
export const PRIORITIES = [
  ["baixa", "Baixa"],
  ["media", "Média"],
  ["alta", "Alta"],
];
// Espelho educativo da regra Python. O teste de contrato compara todas as nove células.
export const MATRIX = {
  individual: { baixa: "baixa", media: "baixa", alta: "media" },
  equipe: { baixa: "baixa", media: "media", alta: "alta" },
  empresa: { baixa: "media", media: "alta", alta: "alta" },
};
export const STATUSES = {
  pendente_classificacao: {
    label: "Sem sugestão",
    tone: "neutral",
    description:
      "Cadastro salvo, ainda sem sugestão de IA. A classificação manual está disponível.",
  },
  aguardando_revisao: {
    label: "Aguardando revisão",
    tone: "info",
    description:
      "A IA respondeu. Uma pessoa precisa aceitar ou corrigir a sugestão.",
  },
  classificacao_falhou: {
    label: "Falha na classificação",
    tone: "warning",
    description:
      "A IA não concluiu a classificação. Os dados estão salvos para análise manual.",
  },
  revisada: {
    label: "Revisada",
    tone: "success",
    description:
      "A decisão humana foi registrada, preservando a sugestão original quando existente.",
  },
};
export const PENDING = [
  "pendente_classificacao",
  "aguardando_revisao",
  "classificacao_falhou",
];
export const EXAMPLES = [
  {
    title: "Equipe sem acesso ao sistema de treinamento",
    description:
      "As seis pessoas de uma equipe fictícia não conseguem abrir o sistema de treinamento desde o início do expediente. As atividades estão bloqueadas e não há alternativa disponível.",
    category: "suporte_ti",
    impact: "equipe",
    urgency: "alta",
    reason:
      "A indisponibilidade afeta uma equipe inteira e impede as atividades no momento.",
  },
  {
    title: "Reembolso de um treinamento fictício",
    description:
      "Uma pessoa fictícia solicita o reembolso de um treinamento. Os documentos estão disponíveis, o prazo é de trinta dias e não há bloqueio das atividades de trabalho.",
    category: "financeiro",
    impact: "individual",
    urgency: "baixa",
    reason:
      "O pedido é financeiro, afeta uma pessoa e possui prazo confortável.",
  },
];
export const label = (options, value) =>
  options.find(([key]) => key === value)?.[1] || "Não informado";
export const priority = (impact, urgency) => MATRIX[impact]?.[urgency] ?? null;
export const isPending = (record) => PENDING.includes(record?.status);
export const hasSuggestion = (record) =>
  Boolean(
    record?.categoria_sugerida &&
    record?.impacto_sugerido &&
    record?.urgencia_sugerida &&
    record?.prioridade_sugerida,
  );
export const dateTime = (value) =>
  value
    ? new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(value))
    : "Não informada";
export function validateRequest(title, description) {
  const errors = {};
  if (title.trim().length < 3 || title.trim().length > 120)
    errors.titulo =
      "Use um título com 3 a 120 caracteres, além dos espaços nas extremidades.";
  if (description.trim().length < 10 || description.trim().length > 2000)
    errors.descricao = "Descreva a situação com 10 a 2.000 caracteres.";
  return errors;
}
export function validateReview(draft) {
  if (draft.decisao === "aceitar") return {};
  const errors = {};
  if (!CATEGORIES.some(([v]) => v === draft.categoria))
    errors.categoria = "Selecione uma categoria válida.";
  if (!IMPACTS.some(([v]) => v === draft.impacto))
    errors.impacto = "Selecione o impacto.";
  if (!URGENCIES.some(([v]) => v === draft.urgencia))
    errors.urgencia = "Selecione a urgência.";
  if (
    (draft.observacao || "").trim().length < 10 ||
    (draft.observacao || "").trim().length > 500
  )
    errors.observacao = "Explique a decisão com 10 a 500 caracteres.";
  return errors;
}
export function filterRequests(records, scope, status, search) {
  const fold = (s) =>
    s
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "")
      .toLocaleLowerCase("pt-BR");
  const query = fold(search.trim());
  return records
    .filter(
      (r) =>
        (scope === "revisadas" ? r.status === "revisada" : isPending(r)) &&
        (status === "all" || r.status === status) &&
        (!query || fold(`${r.id} ${r.titulo}`).includes(query)),
    )
    .sort((a, b) => (scope === "revisadas" ? b.id - a.id : a.id - b.id));
}
