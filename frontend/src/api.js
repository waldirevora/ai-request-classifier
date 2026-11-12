export class ApiError extends Error {
  constructor(message, status = null, fieldErrors = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}
async function requisicao(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new ApiError(
      options.method === "POST"
        ? "Não foi possível confirmar o envio. Consulte a triagem antes de tentar novamente."
        : "Não foi possível conectar à API. Verifique o serviço local e tente novamente.",
    );
  }
  if (response.status === 204) return null;
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const fieldErrors = {};
    if (Array.isArray(detail))
      for (const issue of detail) {
        const key = issue.loc?.at(-1);
        if (["titulo", "descricao", "observacao"].includes(key))
          fieldErrors[key] =
            key === "titulo"
              ? "Use um título com 3 a 120 caracteres."
              : key === "descricao"
                ? "Use uma descrição com 10 a 2.000 caracteres."
                : "Revise a explicação da decisão.";
      }
    throw new ApiError(
      typeof detail === "string"
        ? detail
        : response.status === 422
          ? "Revise os campos indicados e tente novamente."
          : response.status >= 500
            ? "O serviço não concluiu a operação. Verifique a conexão e consulte a triagem antes de repetir um envio."
            : `A operação não foi concluída (HTTP ${response.status}).`,
      response.status,
      fieldErrors,
    );
  }
  if (!body)
    throw new ApiError(
      "O serviço enviou uma resposta inesperada. Consulte a triagem antes de repetir um envio.",
    );
  return body;
}
export const api = {
  configuracao: () => requisicao("/configuracao"),
  listar: () => requisicao("/solicitacoes"),
  pendentes: () => requisicao("/revisoes/pendentes"),
  concluidas: () => requisicao("/revisoes/concluidas"),
  criar: (dados) =>
    requisicao("/solicitacoes", {
      method: "POST",
      body: JSON.stringify(dados),
    }),
  revisar: (id, dados) =>
    requisicao(`/revisoes/${id}`, {
      method: "POST",
      body: JSON.stringify(dados),
    }),
};
