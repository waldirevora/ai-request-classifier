import test from "node:test";
import assert from "node:assert/strict";
import { makeLabEntry, nextLabStep } from "./lab-entry.js";
import { parseRetryAfter, portalApi } from "./portal-api.js";
const unauthorized = () =>
  Object.assign(new Error("Sessão expirada"), { status: 401 });

test("valid session resumes without a workspace creation request", async () => {
  const requests = [];
  const who = { kind: "lab", workspace_id: "own-space" };
  const enter = makeLabEntry(async (_, path) => {
    requests.push(path);
    return who;
  });
  assert.deepEqual(await enter(), { who, resumed: true });
  assert.deepEqual(requests, ["/session"]);
});

test("simultaneous entry buttons share one in-flight request and one creation", async () => {
  const requests = [];
  let release;
  const gate = new Promise((resolve) => {
    release = resolve;
  });
  const enter = makeLabEntry(async (_, path) => {
    requests.push(path);
    if (path === "/session") {
      await gate;
      throw unauthorized();
    }
    return { kind: "lab" };
  });
  const first = enter();
  const second = enter();
  assert.equal(first, second);
  release();
  await Promise.all([first, second]);
  assert.deepEqual(requests, ["/session", "/lab/start"]);
});

test("network failure does not cause an automatic workspace creation", async () => {
  const paths = [];
  const enter = makeLabEntry(async (_, path) => {
    paths.push(path);
    throw new Error("Sem conexão");
  });
  await assert.rejects(enter(), /Sem conexão/);
  assert.deepEqual(paths, ["/session"]);
});

test("creation cooldown still checks for a newly valid session, without posting again", async () => {
  let valid = false;
  let now = 100;
  let creations = 0;
  const limited = Object.assign(new Error("Aguarde para criar outra."), {
    status: 429,
    retryAt: 10000,
  });
  const enter = makeLabEntry(
    async (_, path) => {
      if (path === "/session") {
        if (valid) return { workspace_id: "own" };
        throw unauthorized();
      }
      creations++;
      throw limited;
    },
    () => now,
  );
  await assert.rejects(enter(), (e) => e === limited);
  await assert.rejects(enter(), (e) => e === limited);
  assert.equal(creations, 1);
  valid = true;
  assert.equal((await enter()).resumed, true);
  valid = false;
  now = 10001;
  await assert.rejects(enter(), (e) => e === limited);
  assert.equal(creations, 2);
});

test("Retry-After understands seconds, HTTP dates and invalid values", () => {
  assert.equal(parseRetryAfter("120", 1000), 121000);
  assert.equal(
    parseRetryAfter("Thu, 12 Nov 2026 23:30:00 GMT", 0),
    Date.UTC(2026, 10, 12, 23, 30),
  );
  assert.equal(parseRetryAfter("not-a-date", 1000), null);
  assert.equal(parseRetryAfter(null, 1000), null);
});

test("HTTP 429 preserves the backend explanation and retry deadline without retrying", async () => {
  const previous = global.fetch;
  let calls = 0;
  global.fetch = async () => {
    calls++;
    return {
      ok: false,
      status: 429,
      headers: { get: (name) => (name === "Retry-After" ? "120" : null) },
      json: async () => ({ detail: "Aguarde para criar outra demonstração." }),
    };
  };
  try {
    const before = Date.now();
    await assert.rejects(
      portalApi("lab", "/lab/start", { method: "POST" }),
      (error) =>
        error.status === 429 &&
        error.retryAt >= before + 120000 &&
        /outra demonstração/.test(error.message),
    );
    assert.equal(calls, 1);
  } finally {
    global.fetch = previous;
  }
});

test("connection failure gives a Portuguese explanation and performs no retry", async () => {
  const previous = global.fetch;
  let calls = 0;
  global.fetch = async () => {
    calls++;
    throw new TypeError("Failed to fetch");
  };
  try {
    await assert.rejects(
      portalApi("lab", "/session"),
      /Não foi possível conectar ao SolicitaFlow/,
    );
    assert.equal(calls, 1);
  } finally {
    global.fetch = previous;
  }
});

test("the next step guides each fictional role and exceptional requests", () => {
  assert.match(nextLabStep({ role: "colaborador" }, []), /Cenário automático/);
  assert.match(
    nextLabStep({ role: "colaborador" }, [{ state: "excecao" }]),
    /Central/,
  );
  assert.match(
    nextLabStep({ role: "departamento" }, [{ state: "encaminhada" }]),
    /assuma/,
  );
  assert.match(
    nextLabStep({ role: "departamento" }, [{ state: "resolvida" }]),
    /Colaborador/,
  );
  assert.match(nextLabStep({ role: "central" }, []), /relatórios/);
});
