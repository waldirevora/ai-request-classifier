export async function portalApi(context, path, options = {}) {
  const response = await fetch(`/api/v2${path}`, {
    ...options,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-SolicitaFlow-Context": context,
      ...options.headers,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    const error = new Error(
      typeof data?.detail === "string"
        ? data.detail
        : "Confira os campos e tente novamente.",
    );
    error.status = response.status;
    throw error;
  }
  return data;
}
export const statusLabels = {
  analisando: "Em análise",
  excecao: "Revisão necessária",
  encaminhada: "Encaminhada",
  em_atendimento: "Em atendimento",
  aguardando_colaborador: "Aguardando colaborador",
  resolvida: "Resolvida",
};

export const eventLabels = {
  cadastrada: "Solicitação cadastrada",
  roteamento_automatico: "Encaminhamento automático validado",
  roteamento_excecao: "Exceção identificada",
  revisao_humana: "Revisão humana registrada",
  sla_definido: "Prazos de SLA definidos",
  assumir: "Atendimento assumido",
  andamento: "Atualização de atendimento",
  aguardar: "Aguardando retorno do colaborador",
  retomar: "Atendimento retomado",
  resolver: "Resolução confirmada pelo departamento",
  risco_sla: "SLA em risco",
  cobranca_sla: "Cobrança de SLA registrada",
  primeira_resposta_atrasada: "Prazo de primeira resposta excedido",
  escalonamento: "Escalonamento para a central",
};
export const reasonLabels = {
  classificacao_indisponivel: "A classificação não está disponível.",
  resposta_invalida: "A resposta não passou na validação.",
  informacao_insuficiente: "Precisamos de mais informações.",
  assunto_ambiguo_ou_nao_confirmado:
    "Há mais de um assunto ou a categoria não foi confirmada pelo texto.",
  instrucao_suspeita: "O texto requer avaliação de segurança.",
  impacto_sem_evidencia: "O alcance do problema precisa ser esclarecido.",
  urgencia_sem_evidencia: "A consequência de esperar precisa ser esclarecida.",
  destino_indisponivel: "Não há destino ativo para esta categoria.",
  categoria_exige_revisao:
    "Esta categoria exige revisão pela política do ambiente.",
};
export const slaLabels = {
  normal: "Dentro do prazo",
  em_risco: "Em risco",
  violado: "Prazo violado",
  concluido: "Concluído dentro do prazo",
  resolvido_em_atraso: "Resolvido após o prazo",
  sem_prazo: "Aguardando definição de prazo",
};
