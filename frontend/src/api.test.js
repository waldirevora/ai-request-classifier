import test, { afterEach } from "node:test";
import assert from "node:assert/strict";
import { api, ApiError } from "./api.js";
const original = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = original;
});
test("falha de envio não dispara repetição automática", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    throw new TypeError("offline");
  };
  await assert.rejects(
    api.criar({ titulo: "Fictício", descricao: "Descrição fictícia." }),
    (e) => e instanceof ApiError && /triagem/.test(e.message),
  );
  assert.equal(calls, 1);
});
test("422 produz erros de campo em português sem expor mensagens internas", async () => {
  globalThis.fetch = async () =>
    new Response(
      JSON.stringify({
        detail: [
          { loc: ["body", "titulo"], msg: "internal validation message" },
        ],
      }),
      { status: 422 },
    );
  await assert.rejects(
    api.criar({}),
    (e) =>
      e.status === 422 &&
      Boolean(e.fieldErrors.titulo) &&
      !e.message.includes("internal"),
  );
});
test("conflito conserva a mensagem de negócio fornecida pela API", async () => {
  globalThis.fetch = async () =>
    new Response(JSON.stringify({ detail: "Solicitação já revisada" }), {
      status: 409,
    });
  await assert.rejects(
    api.revisar(1, { decisao: "aceitar" }),
    (e) => e.status === 409 && e.message === "Solicitação já revisada",
  );
});
test("configuração consulta somente o endpoint seguro de metadados", async () => {
  globalThis.fetch = async (url) => {
    assert.equal(url, "/api/configuracao");
    return new Response(
      JSON.stringify({
        ai_enabled: false,
        ai_configured: true,
        ai_model: "deepseek-flash",
      }),
    );
  };
  assert.equal((await api.configuracao()).ai_enabled, false);
});
test("resposta de sucesso inválida informa incerteza em vez de confirmar cadastro", async () => {
  globalThis.fetch = async () =>
    new Response("<html>erro de proxy</html>", { status: 200 });
  await assert.rejects(api.criar({}), (e) =>
    /resposta inesperada/.test(e.message),
  );
});
