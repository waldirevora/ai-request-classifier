import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  MATRIX,
  priority,
  validateRequest,
  validateReview,
  filterRequests,
  hasSuggestion,
  isPending,
} from "./domain.js";

test("as nove prioridades educativas correspondem à matriz Python oficial", () => {
  const path = fileURLToPath(
    new URL("../../backend/app/classificacao.py", import.meta.url),
  );
  const code =
    "import runpy,json,sys;n=runpy.run_path(sys.argv[1]);print(json.dumps({i.value:{u.value:n['calcular_prioridade'](i,u).value for u in n['Urgencia']} for i in n['Impacto']}))";
  const actual = JSON.parse(
    execFileSync(process.env.PYTHON || "python3", ["-c", code, path], {
      encoding: "utf8",
    }),
  );
  assert.deepEqual(MATRIX, actual);
});
test("prévia não inventa prioridade para valores ausentes", () => {
  assert.equal(priority(null, "alta"), null);
  assert.equal(priority("empresa", null), null);
});
test("cadastro rejeita espaços e comprimentos fora dos limites do contrato", () => {
  for (const title of ["", "   ", "ab", "x".repeat(121)])
    assert.ok(validateRequest(title, "Descrição válida.").titulo);
  for (const description of ["", "         ", "curta", "x".repeat(2001)])
    assert.ok(validateRequest("Título", description).descricao);
});
test("cadastro aceita os limites e considera o texto aparado", () => {
  assert.deepEqual(validateRequest(" abc ", " 1234567890 "), {});
  assert.deepEqual(validateRequest("x".repeat(120), "x".repeat(2000)), {});
});
test("correção exige motivo e os valores reais dos catálogos", () => {
  const draft = {
    decisao: "corrigir",
    categoria: "suporte_ti",
    impacto: "individual",
    urgencia: "alta",
    observacao: "Motivo fictício válido.",
  };
  assert.deepEqual(validateReview(draft), {});
  assert.ok(validateReview({ ...draft, observacao: "         " }).observacao);
  assert.ok(validateReview({ ...draft, categoria: "inventada" }).categoria);
  assert.ok(
    validateReview({ ...draft, observacao: "x".repeat(501) }).observacao,
  );
  assert.deepEqual(validateReview({ decisao: "aceitar" }), {});
});
test("fila separa revisadas e pendentes e pesquisa títulos com acentos", () => {
  const records = [
    { id: 1, titulo: "Permissão financeira", status: "pendente_classificacao" },
    { id: 2, titulo: "Outro", status: "revisada" },
    { id: 3, titulo: "Permissão adicional", status: "classificacao_falhou" },
  ];
  assert.deepEqual(
    filterRequests(records, "pendentes", "all", "permissao").map((r) => r.id),
    [1, 3],
  );
  assert.deepEqual(
    filterRequests(records, "pendentes", "classificacao_falhou", "").map(
      (r) => r.id,
    ),
    [3],
  );
  assert.deepEqual(
    filterRequests(records, "revisadas", "all", "").map((r) => r.id),
    [2],
  );
});
test("situação sozinha não é tratada como resposta da IA", () => {
  assert.equal(hasSuggestion({ status: "aguardando_revisao" }), false);
  assert.equal(
    hasSuggestion({
      categoria_sugerida: "financeiro",
      impacto_sugerido: "individual",
      urgencia_sugerida: "baixa",
      prioridade_sugerida: "baixa",
    }),
    true,
  );
  assert.equal(isPending({ status: "revisada" }), false);
});
