import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const script = readFileSync(
  new URL("../public/theme-init.js", import.meta.url),
  "utf8",
);
function initialize(saved, systemDark, storageUnavailable = false) {
  const element = { dataset: {}, style: {} };
  let color,
    reads = [],
    writes = 0;
  vm.runInNewContext(script, {
    document: {
      documentElement: element,
      querySelector: () => ({
        setAttribute: (_, value) => {
          color = value;
        },
      }),
    },
    window: { matchMedia: () => ({ matches: systemDark }) },
    localStorage: {
      getItem: (key) => {
        reads.push(key);
        if (storageUnavailable) throw new Error("blocked");
        return saved;
      },
      setItem: () => {
        writes++;
      },
    },
  });
  return { element, color, reads, writes };
}
for (const [name, saved, systemDark, mode, resolved] of [
  ["primeiro acesso com sistema claro", null, false, "dark", "dark"],
  ["primeiro acesso com sistema escuro", null, true, "dark", "dark"],
  ["preferência Claro preservada", "light", true, "light", "light"],
  ["preferência Escuro preservada", "dark", false, "dark", "dark"],
  ["Automático salvo segue sistema claro", "auto", false, "auto", "light"],
  ["Automático salvo segue sistema escuro", "auto", true, "auto", "dark"],
  ["valor inválido usa Escuro", "unknown", false, "dark", "dark"],
]) {
  test(`tema antes do React: ${name}`, () => {
    const result = initialize(saved, systemDark);
    assert.equal(result.element.dataset.themeChoice, mode);
    assert.equal(result.element.dataset.theme, resolved);
    assert.equal(result.element.style.colorScheme, resolved);
    assert.equal(result.color, resolved === "dark" ? "#0b1422" : "#f3f6fa");
    assert.deepEqual(result.reads, ["arc-theme"]);
    assert.equal(
      result.writes,
      0,
      "carregar não deve sobrescrever a escolha salva",
    );
  });
}
test("tema antes do React: armazenamento bloqueado mantém Escuro", () => {
  const result = initialize(null, false, true);
  assert.equal(result.element.dataset.themeChoice, "dark");
  assert.equal(result.element.dataset.theme, "dark");
  assert.equal(result.color, "#0b1422");
});
