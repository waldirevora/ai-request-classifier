import React, { useEffect, useState } from "react";
import { useTheme } from "./useTheme.js";
import {
  portalApi,
  statusLabels,
  eventLabels,
  reasonLabels,
} from "./portal-api.js";
import App from "./App.jsx";
import { LabGuide } from "./LabGuide.jsx";
import { WorkPanel, OperationalReports } from "./Operations.jsx";
import ProcessEducation from "./ProcessEducation.jsx";
import "./portals.css";

const categories = {
  suporte_ti: "Suporte de TI",
  acessos_permissoes: "Acessos e permissões",
  financeiro: "Financeiro",
  recursos_humanos: "Pessoas",
  outros: "Outros",
};
const format = (value) =>
  value ? new Date(value).toLocaleString("pt-BR") : "Ainda não registrado";

export default function Portals() {
  const [theme, chooseTheme] = useTheme();
  const [context, setContext] = useState(() => {
    try {
      return sessionStorage.getItem("sf-context") || "local";
    } catch {
      return "local";
    }
  });
  const [who, setWho] = useState(null);
  const [actors, setActors] = useState([]);
  const [clock, setClock] = useState(null);
  const [ready, setReady] = useState(false);
  const [page, setPage] = useState("portal");
  const [classic, setClassic] = useState(false);
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("all");
  const [draft, setDraft] = useState({ titulo: "", descricao: "" });
  const [login, setLogin] = useState({ username: "", password: "" });
  const [review, setReview] = useState({
    category: "suporte_ti",
    impact: "equipe",
    urgency: "media",
    department_id: "",
    reason: "",
  });
  const call = (path, options) => portalApi(context, path, options);
  async function refresh(person = who) {
    if (!person) return;
    const [rows, deps] = await Promise.all([
      call("/cases"),
      call("/departments"),
    ]);
    setItems(rows);
    setDepartments(deps);
    if (person.role === "central") setRoutes(await call("/routes"));
  }
  useEffect(() => {
    let active = true;
    setReady(false);
    setSelected(null);
    portalApi(context, "/session")
      .then(async (person) => {
        if (!active) return;
        setWho(person);
        await refresh(person);
      })
      .catch((e) => {
        if (active) {
          setWho(null);
          if (e.status !== 401) setError(e.message);
        }
      })
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, [context]);
  async function run(action) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  function changeContext(next) {
    try {
      sessionStorage.setItem("sf-context", next);
    } catch {
      /* Current tab only. */
    }
    setContext(next);
    setPage("portal");
    setSelected(null);
    setError("");
    setFilter("all");
  }
  useEffect(() => {
    if (who?.kind !== "lab") {
      setActors([]);
      setClock(null);
      return;
    }
    let active = true;
    Promise.all([call("/lab/actors"), call("/lab/clock")])
      .then(([a, c]) => {
        if (active) {
          setActors(a);
          setClock(c.effective_now);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [who?.id]);
  async function startLab() {
    await run(async () => {
      const person = await portalApi("lab", "/lab/start", { method: "POST" });
      changeContext("lab");
      setWho(person);
      setReady(true);
      if (context === "lab") await refresh(person);
    });
  }
  async function switchActor(username) {
    await run(async () => {
      const person = await call("/lab/switch", {
        method: "POST",
        body: { username },
      });
      setWho(person);
      setSelected(null);
      setPage("portal");
      setFilter("all");
      await refresh(person);
    });
  }
  async function advance(hours) {
    await run(async () => {
      const result = await call("/lab/advance", {
        method: "POST",
        body: { hours },
      });
      setClock(result.effective_now);
      setNotice(
        `Tempo simulado avançou ${hours} horas. ${result.notifications_created} alertas internos registrados. Consulte a central para acompanhar.`,
      );
      if (selected) setSelected(await call(`/cases/${selected.id}`));
      await refresh();
    });
  }
  async function open(id) {
    const record = await call(`/cases/${id}`);
    setSelected(record);
    setNotice("");
  }
  async function authenticate(e) {
    e.preventDefault();
    await run(async () => {
      const person = await call("/login", { method: "POST", body: login });
      setWho(person);
      setLogin({ username: "", password: "" });
      await refresh(person);
    });
  }
  async function create(e) {
    e.preventDefault();
    await run(async () => {
      const record = await call("/cases", {
        method: "POST",
        body: { ...draft, client_key: crypto.randomUUID(), mode: "simulacao" },
      });
      setDraft({ titulo: "", descricao: "" });
      await refresh();
      setSelected(record);
      setPage("portal");
      setNotice(
        "Solicitação registrada. Acompanhe o encaminhamento e o histórico abaixo.",
      );
    });
  }
  if (classic)
    return (
      <>
        <button className="classic-return" onClick={() => { chooseTheme(document.documentElement.dataset.themeChoice || "auto"); setClassic(false); }}>
          ← Voltar aos portais SolicitaFlow
        </button>
        <App />
      </>
    );
  const roleLabel = {
    colaborador: "Portal do Colaborador",
    departamento: "Portal do Departamento",
    central: "Central Operacional",
  }[who?.role];
  return (
    <div className="sf-shell">
      <a className="skip-link" href="#portal-content">
        Ir para o conteúdo
      </a>
      <header className="sf-header">
        <a
          href="#"
          className="sf-brand"
          onClick={(e) => {
            e.preventDefault();
            setPage("portal");
          }}
        >
          <span className="brand-icon">SF</span>
          <span>
            <strong>SolicitaFlow</strong>
            <small>Solicitações inteligentes, do pedido à resolução.</small>
          </span>
        </a>
        <div className="sf-tools">
          {context === "lab" ? (
            <button
              className="button secondary"
              onClick={() => changeContext("local")}
            >
              Voltar ao ambiente local
            </button>
          ) : (
            <button
              className="button secondary"
              disabled={busy}
              onClick={startLab}
            >
              Explorar laboratório
            </button>
          )}
          <span className="badge">
            {context === "lab"
              ? "Laboratório · Simulação sem custos"
              : "Ambiente local · Cadastro em simulação"}
          </span>
          <label>
            Tema
            <select
              aria-label="Tema da interface"
              value={theme}
              onChange={(e) => chooseTheme(e.target.value)}
            >
              <option value="auto">Automático</option>
              <option value="light">Claro</option>
              <option value="dark">Escuro</option>
            </select>
          </label>
        </div>
      </header>
      <main id="portal-content" className="sf-main" tabIndex={-1}>
        {error && (
          <div className="callout error" role="alert">
            {error}
            <button className="button secondary" onClick={() => setError("")}>
              Fechar mensagem
            </button>
          </div>
        )}
        {notice && (
          <p className="callout success" role="status">
            {notice}
          </p>
        )}
        {ready && who?.kind === "lab" && (
          <LabGuide
            who={who}
            actors={actors}
            switchActor={switchActor}
            advance={advance}
            fill={(example) => {
              setDraft(example);
              setPage("new");
            }}
            busy={busy}
            clock={clock}
          />
        )}
        {!ready ? (
          <p role="status">Verificando sessão…</p>
        ) : !who ? (
          <section className="sf-welcome">
            <div>
              <p className="eyebrow">INTELIGÊNCIA COM CONTROLE</p>
              <h1>
                Do pedido à resolução.
                <br />
                Cada etapa, visível.
              </h1>
              <p>
                Classificação assistida, destino validado por regras e
                acompanhamento pelo departamento responsável.
              </p>
              <div className="sf-steps">
                01 Cadastro → 02 Classificação → 03 Encaminhamento → 04
                Resolução
              </div>
              <button
                className="button secondary"
                onClick={() => setPage(page === "learn" ? "portal" : "learn")}
              >
                Como funciona
              </button>
            </div>
            {context === "lab" ? (
              <section className="card sf-form">
                <h2>Seu laboratório está disponível.</h2>
                <p>
                  Inicie uma nova sessão fictícia sem senha ou retorne ao
                  ambiente local.
                </p>
                <button
                  className="button primary"
                  onClick={startLab}
                  disabled={busy}
                >
                  Iniciar laboratório
                </button>
              </section>
            ) : (
              <form className="card sf-form" onSubmit={authenticate}>
                <h2>Entrar no ambiente local</h2>
                <p>
                  Use uma das contas fictícias provisionadas localmente. Cada
                  perfil possui permissões próprias.
                </p>
                <label>
                  Usuário
                  <input
                    autoComplete="username"
                    required
                    value={login.username}
                    onChange={(e) =>
                      setLogin({ ...login, username: e.target.value })
                    }
                  />
                </label>
                <label>
                  Senha
                  <input
                    type="password"
                    autoComplete="current-password"
                    required
                    value={login.password}
                    onChange={(e) =>
                      setLogin({ ...login, password: e.target.value })
                    }
                  />
                </label>
                <button className="button primary" disabled={busy}>
                  {busy ? "Entrando…" : "Entrar"}
                </button>
              </form>
            )}
          </section>
        ) : (
          <>
            <div className="sf-page-heading">
              <div>
                <p className="eyebrow">{who.display_name}</p>
                <h1>{roleLabel}</h1>
                <p>
                  {who.role === "colaborador"
                    ? "Seus pedidos, prazos e respostas em um só lugar."
                    : who.role === "departamento"
                      ? "A fila do seu departamento. Assuma, acompanhe e resolva."
                      : "Pipeline, exceções e regras de encaminhamento."}
                </p>
              </div>
              <button
                className="button secondary"
                disabled={busy}
                onClick={() =>
                  run(async () => {
                    await call("/logout", { method: "POST" });
                    setWho(null);
                    setSelected(null);
                  })
                }
              >
                Sair
              </button>
            </div>
            <nav className="sf-tabs" aria-label="Navegação do portal">
              <button
                className={page === "portal" ? "active" : ""}
                onClick={() => setPage("portal")}
              >
                Solicitações
              </button>
              {who.role === "colaborador" && (
                <button
                  className={page === "new" ? "active" : ""}
                  onClick={() => setPage("new")}
                >
                  Nova solicitação
                </button>
              )}
              {who.role === "central" && (
                <button onClick={() => setPage("rules")}>
                  Departamentos e regras
                </button>
              )}
              {who.role === "central" && (
                <button onClick={() => setPage("reports")}>
                  SLA e relatórios
                </button>
              )}
              <button onClick={() => setPage("learn")}>Como funciona</button>
              {who.role === "central" && context === "local" && (
                <button onClick={() => setClassic(true)}>
                  Triagem clássica
                </button>
              )}
              <button disabled={busy} onClick={() => run(() => refresh())}>
                Atualizar
              </button>
            </nav>
            {page === "reports" && who.role === "central" && (
              <OperationalReports call={call} run={run} busy={busy} />
            )}
            {page === "new" && (
              <form className="card sf-form sf-create" onSubmit={create}>
                <p className="eyebrow">NOVA SOLICITAÇÃO</p>
                <h2>Conte o que aconteceu.</h2>
                <p>
                  Descreva quem foi afetado, o problema e a consequência
                  operacional. Use dados fictícios neste ambiente.
                </p>
                <label>
                  Título
                  <input
                    minLength={3}
                    maxLength={120}
                    required
                    value={draft.titulo}
                    onChange={(e) =>
                      setDraft({ ...draft, titulo: e.target.value })
                    }
                  />
                </label>
                <label>
                  Descrição
                  <textarea
                    minLength={10}
                    maxLength={2000}
                    required
                    rows={6}
                    value={draft.descricao}
                    onChange={(e) =>
                      setDraft({ ...draft, descricao: e.target.value })
                    }
                  />
                </label>
                <p className="field-help">
                  Modo determinístico: não envia dados à DeepSeek. A prioridade
                  utiliza a matriz Python.
                </p>
                <button className="button primary" disabled={busy}>
                  {busy ? "Registrando e classificando…" : "Enviar solicitação"}
                </button>
              </form>
            )}
            {page === "portal" && (
              <>
                <div className="sf-metrics">
                  {[
                    ["Pedidos", items.length],
                    [
                      "Em atendimento",
                      items.filter((x) =>
                        [
                          "encaminhada",
                          "em_atendimento",
                          "aguardando_colaborador",
                        ].includes(x.state),
                      ).length,
                    ],
                    [
                      "Exceções",
                      items.filter((x) => x.state === "excecao").length,
                    ],
                    [
                      "Resolvidas",
                      items.filter((x) => x.state === "resolvida").length,
                    ],
                  ].map(([label, count]) => (
                    <div className="card" key={label}>
                      <span>{label}</span>
                      <strong>{count}</strong>
                    </div>
                  ))}
                </div>
                <div
                  className={"sf-workspace" + (selected ? " has-detail" : "")}
                >
                  <section className="card sf-list" hidden={false}>
                    <div className="sf-list-heading">
                      <h2>Solicitações</h2>
                      <label className="sr-only" htmlFor="case-filter">
                        Filtrar por situação
                      </label>
                      <select
                        id="case-filter"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                      >
                        <option value="all">Todas as situações</option>
                        {Object.entries(statusLabels).map(([id, label]) => (
                          <option key={id} value={id}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </div>
                    {items
                      .filter((x) => filter === "all" || x.state === filter)
                      .map((x) => (
                        <button
                          key={x.id}
                          className={
                            "sf-list-item" +
                            (selected?.id === x.id ? " active" : "")
                          }
                          onClick={() => run(() => open(x.id))}
                        >
                          <strong>{x.titulo}</strong>
                          <span>
                            {statusLabels[x.state]} ·{" "}
                            {x.department_name || "Destino em análise"}
                          </span>
                          <small>{format(x.created_at)}</small>
                        </button>
                      ))}
                    {!items.filter(
                      (x) => filter === "all" || x.state === filter,
                    ).length && (
                      <p className="sf-empty">
                        Nenhuma solicitação nesta situação.
                        {who.role === "colaborador"
                          ? " Comece em Nova solicitação."
                          : "Os pedidos encaminhados aparecerão aqui."}
                      </p>
                    )}
                  </section>
                  {selected && (
                    <section className="card sf-detail">
                      <button
                        className="button secondary"
                        onClick={() => setSelected(null)}
                      >
                        ← Voltar à lista
                      </button>
                      <p className="eyebrow">
                        {statusLabels[selected.state]} ·{" "}
                        {selected.source === "simulacao"
                          ? "SIMULAÇÃO"
                          : "DEEPSEEK"}
                      </p>
                      <h2>{selected.request.titulo}</h2>
                      <p className="sf-description">
                        {selected.request.descricao}
                      </p>
                      <p className="field-help">
                        Recebida em {format(selected.created_at)}
                      </p>
                      <div className="sf-result">
                        <h3>
                          {selected.source === "simulacao"
                            ? "Sugestão simulada"
                            : "Sugestão original da IA"}
                        </h3>
                        <dl>
                          <dt>Categoria</dt>
                          <dd>
                            {categories[selected.request.categoria_sugerida] ||
                              "Indisponível"}
                          </dd>
                          <dt>Impacto / urgência</dt>
                          <dd>
                            {selected.request.impacto_sugerido || "—"} /{" "}
                            {selected.request.urgencia_sugerida || "—"}
                          </dd>
                          <dt>Prioridade calculada</dt>
                          <dd>
                            {selected.request.prioridade_sugerida ||
                              "Aguardando informações"}
                          </dd>
                        </dl>
                        <p>
                          {selected.request.justificativa_ia ||
                            "A ausência de classificação não elimina o pedido."}
                        </p>
                      </div>
                      <div className="sf-result">
                        <h3>Resultado do encaminhamento</h3>
                        <p>
                          {selected.department_id
                            ? departments.find(
                                (d) => d.id === selected.department_id,
                              )?.name
                            : "A central precisa esclarecer o destino."}
                        </p>
                        <p>
                          Prioridade vigente:{" "}
                          <strong>{selected.priority || "Não definida"}</strong>
                        </p>
                        {selected.decisions.map((d) => (
                          <p key={d.id}>
                            {d.outcome === "excecao"
                              ? "Exceção"
                              : d.outcome === "manual"
                                ? "Decisão humana"
                                : "Encaminhamento automático"}
                            {d.reasons.length
                              ? `: ${d.reasons.map((reason) => reasonLabels[reason] || reason).join(" · ")}`
                              : " · destino validado pelas regras"}
                          </p>
                        ))}
                      </div>
                      {who.role === "central" &&
                        selected.state === "excecao" && (
                          <form
                            className="sf-form"
                            onSubmit={(e) => {
                              e.preventDefault();
                              run(async () => {
                                const result = await call(
                                  `/cases/${selected.id}/review`,
                                  { method: "POST", body: review },
                                );
                                setSelected(result);
                                await refresh();
                              });
                            }}
                          >
                            <h3>Revisão da exceção</h3>
                            <label>
                              Categoria
                              <select
                                value={review.category}
                                onChange={(e) =>
                                  setReview({
                                    ...review,
                                    category: e.target.value,
                                  })
                                }
                              >
                                {Object.entries(categories).map(
                                  ([id, label]) => (
                                    <option value={id} key={id}>
                                      {label}
                                    </option>
                                  ),
                                )}
                              </select>
                            </label>
                            <label>
                              Departamento
                              <select
                                required
                                value={review.department_id}
                                onChange={(e) =>
                                  setReview({
                                    ...review,
                                    department_id: e.target.value,
                                  })
                                }
                              >
                                <option value="">
                                  Selecione o destino validado
                                </option>
                                {departments.map((d) => (
                                  <option key={d.id} value={d.id}>
                                    {d.name}
                                  </option>
                                ))}
                              </select>
                            </label>
                            <label>
                              Impacto
                              <select
                                value={review.impact}
                                onChange={(e) =>
                                  setReview({
                                    ...review,
                                    impact: e.target.value,
                                  })
                                }
                              >
                                {["individual", "equipe", "empresa"].map(
                                  (x) => (
                                    <option key={x}>{x}</option>
                                  ),
                                )}
                              </select>
                            </label>
                            <label>
                              Urgência
                              <select
                                value={review.urgency}
                                onChange={(e) =>
                                  setReview({
                                    ...review,
                                    urgency: e.target.value,
                                  })
                                }
                              >
                                {["baixa", "media", "alta"].map((x) => (
                                  <option key={x}>{x}</option>
                                ))}
                              </select>
                            </label>
                            <label>
                              Motivo da decisão
                              <textarea
                                required
                                minLength={10}
                                maxLength={500}
                                value={review.reason}
                                onChange={(e) =>
                                  setReview({
                                    ...review,
                                    reason: e.target.value,
                                  })
                                }
                              />
                            </label>
                            <button className="button primary" disabled={busy}>
                              Confirmar revisão e encaminhar
                            </button>
                          </form>
                        )}
                      <WorkPanel
                        record={selected}
                        who={who}
                        call={call}
                        busy={busy}
                        run={run}
                        onChanged={async (next) => {
                          setSelected(next);
                          await refresh();
                        }}
                      />
                      <h3>Histórico auditável</h3>
                      <ol className="sf-timeline">
                        {selected.events.map((e) => (
                          <li key={e.id}>
                            <strong>
                              {eventLabels[e.type] || "Evento de atendimento"}
                            </strong>
                            {e.actor_name && (
                              <p className="field-help">{e.actor_name}</p>
                            )}
                            {(e.payload.message || e.payload.reason) && (
                              <p>{e.payload.message || e.payload.reason}</p>
                            )}
                            <time>
                              {format(e.payload.effective_at || e.created_at)}
                            </time>
                          </li>
                        ))}
                      </ol>
                    </section>
                  )}
                </div>
              </>
            )}
            {page === "rules" && who.role === "central" && (
              <section className="card sf-form">
                <h2>Departamentos e regras</h2>
                <p>
                  Uma categoria possui um único destino ativo. Casos ambíguos
                  seguem para revisão.
                </p>
                <form
                  className="sf-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const form = e.currentTarget;
                    const name = new FormData(form).get("name");
                    run(async () => {
                      await call("/departments", {
                        method: "POST",
                        body: { name },
                      });
                      form.reset();
                      await refresh();
                    });
                  }}
                >
                  <label>
                    Novo departamento
                    <input name="name" required minLength={3} maxLength={100} />
                  </label>
                  <button className="button secondary" disabled={busy}>
                    Cadastrar departamento
                  </button>
                </form>
                {Object.entries(categories)
                  .filter(([id]) => id !== "outros")
                  .map(([cat, label]) => (
                    <label key={cat}>
                      {label}
                      <select
                        value={
                          routes.find((r) => r.category === cat)
                            ?.department_id || ""
                        }
                        onChange={(e) =>
                          run(async () => {
                            await call("/routes", {
                              method: "PUT",
                              body: {
                                category: cat,
                                department_id: e.target.value,
                              },
                            });
                            await refresh();
                          })
                        }
                      >
                        <option value="" disabled>
                          Sem destino
                        </option>
                        {departments.map((d) => (
                          <option value={d.id} key={d.id}>
                            {d.name}
                          </option>
                        ))}
                      </select>
                    </label>
                  ))}
              </section>
            )}
          </>
        )}
        {page === "learn" && (
          <section className="card sf-learning">
            <ProcessEducation />
          </section>
        )}
      </main>
      <footer className="sf-footer">
        SolicitaFlow · Laboratório local · Decisões rastreáveis, dados fictícios
        · Sem publicação na internet
      </footer>
    </div>
  );
}
