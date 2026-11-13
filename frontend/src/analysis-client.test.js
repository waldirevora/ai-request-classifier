import test from "node:test";
import assert from "node:assert/strict";
import { submissionFor } from "./analysis-client.js";
test("real AI submissions retain the same key after an uncertain network response", () => {
  const draft = {
    titulo: " Pedido fictício ",
    descricao: " Descrição inteiramente fictícia. ",
  };
  const first = submissionFor(draft, null, () => "first");
  assert.equal(first.body.mode, "deepseek");
  assert.equal(
    submissionFor(draft, first, () => "second"),
    first,
  );
  assert.equal(
    submissionFor({ ...draft, titulo: "Outro pedido" }, first, () => "second")
      .body.client_key,
    "second",
  );
});
