import React, { useEffect, useState, useRef } from "react";
import { useTheme } from "./useTheme.js";
import {
  portalApi,
  statusLabels,
  eventLabels,
  reasonLabels,
} from "./portal-api.js";
import App from "./App.jsx";
import BrandLogo from "./BrandLogo.jsx";
import AnalysisJourney from "./AnalysisJourney.jsx";
import { submissionFor } from "./analysis-client.js";
import Landing, { FirstSteps, HeroPreview } from "./Landing.jsx";
import { enterLaboratory } from "./lab-entry.js";
import { LabGuide } from "./LabGuide.jsx";
import { WorkPanel, OperationalReports } from "./Operations.jsx";
import ProcessEducation from "./ProcessEducation.jsx";
import "./portals.css";
import "./onboarding.css";
import "./commercial.css";

const categories = {
  suporte_ti: "Suporte de TI",
  acessos_permissoes: "Acessos e permissões",
  financeiro: "Financeiro",
  recursos_humanos: "Pessoas",
  outros: "Outros",
};
const format = (value) =>
  value ? new Date(value).toLocaleString("pt-BR") : "Ainda não registrado";

const publicSite = document.documentElement.dataset.publicDemo === "true";

function readContext() {
  if (publicSite) return "lab";
  try {
    const value = sessionStorage.getItem("sf-context");
    return ["local", "lab"].includes(value) ? value : null;
  } catch {
    return null;
  }
}

export default function Portals() {
  const [theme, chooseTheme] = useTheme();
  const [context, setContext] = useState(() => readContext() || "local");
  const discoverLab = useRef(readContext() === null);
  const entryPending = useRef(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [retryAt, setRetryAt] = useState(null);
  const [who, setWho] = useState(null);
  const [technical, setTechnical] = useState(false);
  const technicalLogin = useRef(null);
  useEffect(() => {
    if (technical) technicalLogin.current?.focus();
  }, [technical]);
  const [presentation, setPresentation] = useState(null);
  const publicDemo = publicSite || presentation?.public_demo === true;
  const submission = useRef(null);
  useEffect(() => {
    portalApi("lab", "/presentation")
      .then(setPresentation)
      .catch(() => setPresentation(null));
  }, []);
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
  async function refresh(person = who, scope = context) {
    if (!person) return;
    const [rows, deps] = await Promise.all([
      portalApi(scope, "/cases"),
      portalApi(scope, "/departments"),
    ]);
    setItems(rows);
    setDepartments(deps);
    if (person.role === "central") setRoutes(await portalApi(scope, "/routes"));
  }
  useEffect(() => {
    let active = true;
    let transferred = false;
    setReady(false);
    setSelected(null);
    setSessionExpired(false);
    (async () => {
      try {
        const person = await portalApi(context, "/session");
        if (!active) return;
        setWho(person);
        await refresh(person, context);
      } catch (error) {
        if (!active) return;
        if (
          error.status === 401 &&
          context === "local" &&
          discoverLab.current
        ) {
          discoverLab.current = false;
          try {
            const resumed = await portalApi("lab", "/session");
            if (!active) return;
            transferred = true;
            changeContext("lab");
            setWho(resumed);
            return;
          } catch (discoveryError) {
            if (discoveryError.status !== 401 && active)
              setError(discoveryError.message);
          }
        }
        if (!active) return;
        setWho(null);
        if (
          error.status === 401 &&
          context === "lab" &&
          /expir/i.test(error.message)
        )
          setSessionExpired(true);
        if (error.status !== 401) setError(error.message);
      } finally {
        if (active && !transferred) setReady(true);
      }
    })();
    return () => {
      active = false;
    };
  }, [context]);
  async function run(action) {
    setBusy(true);
    setError("");
    setNotice("");
    setRetryAt(null);
    try {
      await action();
    } catch (e) {
      setError(e.message);
      if (e.status === 429) setRetryAt(e.retryAt);
      if (e.status === 401) {
        setWho(null);
        setSelected(null);
        setItems([]);
        setPage("portal");
        if (context === "lab") setSessionExpired(true);
      }
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
    discoverLab.current = false;
    setWho(null);
    setItems([]);
    setDepartments([]);
    setRoutes([]);
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
    if (entryPending.current) return;
    entryPending.current = true;
    try {
      await run(async () => {
        const { who: person, resumed } = await enterLaboratory();
        changeContext("lab");
        setWho(person);
        setSessionExpired(false);
        await refresh(person, "lab");
        setReady(true);
        setNotice(
          resumed
            ? "Demonstração retomada. Seus pedidos e o relógio foram mantidos."
            : "Sua demonstração está pronta. Comece pelo Exemplo de TI ou descreva um pedido fictício.",
        );
      });
    } finally {
      entryPending.current = false;
    }
  }
  async function activateActor(username) {
    const person = await call("/lab/switch", {
      method: "POST",
      body: { username },
    });
    setWho(person);
    setSelected(null);
    setPage("portal");
    setFilter("all");
    await refresh(person);
  }
  async function switchActor(username) {
    await run(() => activateActor(username));
  }
  async function restartGuide() {
    await run(async () => {
      await activateActor("colaborador");
      setDraft({ titulo: "", descricao: "" });
      setNotice(
        "Roteiro reiniciado com o Colaborador. Pedidos, histórico e relógio foram preservados; nenhum laboratório novo foi criado.",
      );
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
  useEffect(() => {
    if (!selected || !["queued", "running"].includes(selected.analysis_status))
      return;
    let active = true,
      timer,
      count = 0;
    const poll = async () => {
      try {
        const next = await portalApi(context, `/cases/${selected.id}`);
        if (!active) return;
        setSelected((current) => (current?.id === next.id ? next : current));
        if (!["queued", "running"].includes(next.analysis_status)) {
          await refresh();
          return;
        }
        if (++count < 60) timer = setTimeout(poll, 600);
        else
          setNotice(
            "O pedido continua salvo e em processamento. Atualize a tela para acompanhar; não é necessário reenviar.",
          );
      } catch (error) {
        if (active)
          setError(
            "Não foi possível acompanhar a análise. O pedido foi recebido; consulte a lista antes de reenviar.",
          );
      }
    };
    timer = setTimeout(poll, 600);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [selected?.id, selected?.analysis_status, context]);
  async function create(e) {
    e.preventDefault();
    await run(async () => {
      submission.current = submissionFor(draft, submission.current);
      const record = await call("/cases", {
        method: "POST",
        headers: { Prefer: "respond-async" },
        body: submission.current.body,
      });
      if (!record?.id)
        throw new Error(
          "Não foi possível confirmar o envio. Consulte a lista antes de reenviar.",
        );
      submission.current = null;
      setDraft({ titulo: "", descricao: "" });
      setSelected(record);
      setPage("portal");
      setNotice(
        "Recebemos sua solicitação. O pedido foi salvo; agora vamos acompanhar a análise da descrição.",
      );
      await refresh();
    });
  }
  if (classic)
    return (
      <>
        <button
          className="classic-return"
          onClick={() => {
            chooseTheme(document.documentElement.dataset.themeChoice || "auto");
            setClassic(false);
          }}
        >
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
          aria-label="SolicitaFlow — início"
          onClick={(e) => {
            e.preventDefault();
            setPage("portal");
          }}
        >
          <BrandLogo />
        </a>
        <div className="sf-tools">
          {context === "lab" ? (
            <button
              className="button secondary"
              onClick={() => {
                if (publicDemo) {
                  setWho(null);
                  setSelected(null);
                  setPage("portal");
                  setError("");
                } else changeContext("local");
              }}
            >
              {publicDemo
                ? "Voltar à apresentação"
                : "Voltar ao ambiente local"}
            </button>
          ) : (
            <button
              className="button secondary"
              disabled={busy}
              onClick={startLab}
            >
              {busy ? "Preparando demonstração…" : "Iniciar demonstração"}
            </button>
          )}
          <span className="badge">
            {context === "lab"
              ? "IA real · Atendimento demonstrativo"
              : "Solução corporativa personalizada"}
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
        {presentation?.test_mode && (
          <div className="callout warning" role="note">
            Ambiente de testes automatizados: respostas da IA são mocks, sem
            chamadas externas.
          </div>
        )}
        {error && (
          <div className="callout error" role="alert">
            <div>
              <p>{error}</p>
              {retryAt && (
                <p>
                  Você poderá criar uma nova demonstração às{" "}
                  <time dateTime={new Date(retryAt).toISOString()}>
                    {new Date(retryAt).toLocaleTimeString("pt-BR")}
                  </time>
                  . Se houver uma sessão válida neste navegador, a entrada
                  continuará disponível para retomá-la.
                </p>
              )}
            </div>
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
            records={items}
            selected={selected}
            restart={restartGuide}
          />
        )}
        {!ready ? (
          <p role="status">Verificando sessão…</p>
        ) : !who ? (
          <section className="sf-welcome sf-commercial-hero">
            <div>
              <p className="eyebrow">IA E AUTOMAÇÃO PARA PROCESSOS INTERNOS</p>
              <h1>
                Sua empresa recebe solicitações. Mas consegue acompanhar todas
                até a resolução?
              </h1>
              <p>
                Organize solicitações internas, utilize inteligência artificial
                para identificar o departamento responsável e acompanhe prazos,
                atendimentos e resultados em um único fluxo.
              </p>
              <div className="sf-hero-actions">
                <button
                  className="button primary"
                  onClick={startLab}
                  disabled={busy}
                >
                  {busy
                    ? "Preparando demonstração…"
                    : sessionExpired
                      ? "Iniciar nova demonstração"
                      : "Experimentar o SolicitaFlow"}
                </button>
                <a className="button secondary" href="#como-funciona">
                  Entenda como funciona
                </a>
              </div>
              <p className="field-help">
                Sem login · Empresa fictícia · Análise real com limites de uso
              </p>
              <p className="field-help">
                Uma demonstração profissional de uma solução que pode ser
                personalizada para sua empresa.
              </p>
              <FirstSteps />
            </div>
            <HeroPreview />
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
                  A descrição será enviada à DeepSeek pelo backend, dentro dos
                  limites de uso. Utilize somente dados fictícios. A prioridade
                  será calculada por regras Python.
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
                      <AnalysisJourney
                        record={selected}
                        departments={departments}
                        testMode={presentation?.test_mode}
                      />
                      <div className="sf-result">
                        <h3>
                          {selected.source === "simulacao"
                            ? "Sugestão simulada histórica"
                            : !selected.request.categoria_sugerida
                              ? "Nenhuma sugestão de IA disponível"
                              : presentation?.test_mode
                                ? "Sugestão do mock (teste)"
                                : "Sugestão original da DeepSeek"}
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

        {ready && !who && (
          <>
            {sessionExpired && (
              <div className="callout warning" role="status">
                <strong>Sua sessão de demonstração encerrou.</strong>
                <p>
                  Por segurança, não recuperamos o laboratório anterior após
                  expirar. Inicie outra demonstração independente, sujeita aos
                  limites de uso.
                </p>
              </div>
            )}
            <Landing
              onExplore={startLab}
              busy={busy}
              contactUrl={presentation?.contact_url}
            />
            {!publicDemo && (
              <section
                id="local-technical-access"
                className="sf-technical-access"
                aria-label="Acesso local autenticado"
                hidden={!technical}
              >
                {context !== "local" ? (
                  <button
                    className="button secondary"
                    onClick={() => changeContext("local")}
                  >
                    Abrir acesso local
                  </button>
                ) : (
                  <form
                    id="local-login"
                    className="card sf-form"
                    onSubmit={authenticate}
                  >
                    <h2>Acessar portais locais</h2>
                    <label>
                      Usuário
                      <input
                        ref={technicalLogin}
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
                      Entrar
                    </button>
                  </form>
                )}
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
        {publicDemo
          ? "SolicitaFlow · Portfólio B2B · Empresa e atendimento fictícios · IA real sujeita a cotas"
          : "SolicitaFlow · Laboratório local · Decisões rastreáveis, dados fictícios · Sem publicação na internet"}
        {ready && !who && !publicDemo && (
          <button
            type="button"
            className="sf-technical-link"
            aria-controls="local-technical-access"
            aria-expanded={technical}
            onClick={() => setTechnical((open) => !open)}
          >
            Acesso técnico
          </button>
        )}
      </footer>
    </div>
  );
}
