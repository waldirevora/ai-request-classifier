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
