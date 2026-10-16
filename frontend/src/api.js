// O navegador envia /api/* para o Vite; o Vite encaminha à FastAPI local.
// Assim não precisamos expor credenciais DeepSeek nem configurar CORS no MVP.
async function requisicao(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new Error('Não foi possível conectar à API. Confira o servidor FastAPI.');
  }

  if (response.status === 204) return null;
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message = typeof detail === 'string' ? detail :
      (response.status === 422 ? 'Revise os campos informados.' : `Erro HTTP ${response.status}`);
    throw new Error(message);
  }
  return body;
}

export const api = {
  listar: () => requisicao('/solicitacoes'),
  pendentes: () => requisicao('/revisoes/pendentes'),
  concluidas: () => requisicao('/revisoes/concluidas'),
  criar: (dados) => requisicao('/solicitacoes', {method: 'POST', body: JSON.stringify(dados)}),
  revisar: (id, dados) => requisicao(`/revisoes/${id}`, {method: 'POST', body: JSON.stringify(dados)}),
};
