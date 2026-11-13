export function submissionFor(
  draft,
  previous,
  makeKey = () => crypto.randomUUID(),
) {
  const titulo = draft.titulo.trim(),
    descricao = draft.descricao.trim();
  const payload = JSON.stringify([titulo, descricao]);
  return previous?.payload === payload
    ? previous
    : {
        payload,
        body: { titulo, descricao, mode: "deepseek", client_key: makeKey() },
      };
}
