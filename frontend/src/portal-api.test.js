import test from "node:test";
import assert from "node:assert/strict";
import {
  portalApi,
  statusLabels,
  eventLabels,
  reasonLabels,
  slaLabels,
} from "./portal-api.js";

test("portal request sends its context and never retries a failed mutation", async () => {
  const original = global.fetch;
  let count = 0;
  global.fetch = async (path, options) => {
    count++;
    assert.equal(path, "/api/v2/cases");
    assert.equal(options.headers["X-SolicitaFlow-Context"], "lab");
    assert.equal(options.credentials, "same-origin");
    return {
      ok: false,
      status: 403,
      json: async () => ({ detail: "Operação não permitida" }),
    };
  };
  try {
    await assert.rejects(
      portalApi("lab", "/cases", {
        method: "POST",
        body: { mode: "deepseek" },
      }),
      /Operação não permitida/,
    );
    assert.equal(count, 1);
  } finally {
    global.fetch = original;
  }
});

test("pipeline labels distinguish exception and effective resolution", () => {
  assert.equal(statusLabels.excecao, "Revisão necessária");
  assert.equal(statusLabels.resolvida, "Resolvida");
  assert.equal(Object.keys(statusLabels).length, 6);
});

test("workflow history and SLA expose useful Portuguese labels", () => {
  assert.equal(eventLabels.andamento, "Atualização de atendimento");
  assert.equal(slaLabels.em_risco, "Em risco");
  assert.match(reasonLabels.destino_indisponivel, /destino ativo/);
});
