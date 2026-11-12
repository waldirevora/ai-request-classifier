import React, { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { isPending } from "./domain.js";
import { useTheme } from "./useTheme.js";
import { Icon } from "./components/Primitives.jsx";
import Overview from "./pages/Overview.jsx";
import NewRequest from "./pages/NewRequest.jsx";
import Triage from "./pages/Triage.jsx";
import Journey from "./pages/Journey.jsx";

const PAGES = [
  ["overview", "Visão geral", "grid"],
  ["new", "Nova solicitação", "plus"],
  ["triage", "Triagem e revisão", "review"],
  ["learn", "Como funciona", "route"],
];
function initialGuide() {
  try {
    return localStorage.getItem("arc-guide-dismissed") !== "true";
  } catch {
    return true;
  }
}
export default function App() {
  const [page, setPage] = useState("overview");
  const [records, setRecords] = useState([]);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [configError, setConfigError] = useState("");
  const [guide, setGuide] = useState(initialGuide);
  const [draft, setDraft] = useState({ titulo: "", descricao: "" });
  const [view, setView] = useState({
    scope: "pendentes",
    status: "all",
    search: "",
    id: null,
  });
  const [theme, chooseTheme] = useTheme();
  const [mobileNav, setMobileNav] = useState(
    () => window.matchMedia("(max-width: 900px)").matches,
  );
  const requestNumber = useRef(0);
  const navRefs = useRef([]);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const change = () => setMobileNav(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  const refresh = useCallback(async () => {
    const number = ++requestNumber.current;
    setRefreshing(true);
    const [data, settings] = await Promise.allSettled([
      api.listar(),
      api.configuracao(),
    ]);
    if (number !== requestNumber.current) return;
    if (data.status === "fulfilled" && Array.isArray(data.value)) {
      setRecords(data.value);
      setHasLoaded(true);
      setError("");
    } else
      setError(
        data.reason?.message || "Não foi possível carregar as solicitações.",
      );
    if (settings.status === "fulfilled") {
      setConfig(settings.value);
      setConfigError("");
    } else {
      setConfig(null);
      setConfigError(
        "Não foi possível confirmar o estado da IA. Atualize a conexão antes de enviar uma solicitação.",
      );
    }
    setLoading(false);
    setRefreshing(false);
  }, []);
  useEffect(() => {
    refresh();
  }, [refresh]);
  const navigate = (next, focus = false, options = null) => {
    setPage(next);
    if (next === "triage" && options)
      setView({
        scope: options.scope || "pendentes",
        status: options.status || "all",
        search: "",
        id: null,
      });
    if (focus)
      requestAnimationFrame(() =>
        document.getElementById(`heading-${next}`)?.focus(),
      );
  };
  const openRecord = (r) => {
    setView({
      scope: r.status === "revisada" ? "revisadas" : "pendentes",
      status: "all",
      search: "",
      id: r.id,
    });
    navigate("triage");
  };
  const changed = async (record) => {
    setRecords((list) =>
      list.some((r) => r.id === record.id)
        ? list.map((r) => (r.id === record.id ? record : r))
        : [...list, record],
    );
    await refresh();
  };
  const dismissGuide = () => {
    try {
      localStorage.setItem("arc-guide-dismissed", "true");
    } catch {
      /* Sessão atual. */
    }
    setGuide(false);
    document.getElementById("heading-overview")?.focus();
  };
  const example = (x) => {
    setDraft({ titulo: x.title, descricao: x.description });
    navigate("new", true);
  };
  const aiState = !config
    ? "unknown"
    : config.ai_enabled && config.ai_configured
      ? "on"
      : config.ai_enabled
        ? "missing"
        : "off";
  const aiLabel = {
    unknown: "IA: estado indisponível",
    on: "IA ativa",
    missing: "IA sem configuração",
    off: "IA desabilitada",
  }[aiState];
  function navKey(event, index) {
    let next;
    if (["ArrowRight", "ArrowDown"].includes(event.key))
      next = (index + 1) % PAGES.length;
    else if (["ArrowLeft", "ArrowUp"].includes(event.key))
      next = (index + PAGES.length - 1) % PAGES.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = PAGES.length - 1;
    if (next !== undefined) {
      event.preventDefault();
      navigate(PAGES[next][0]);
      navRefs.current[next]?.focus();
    }
  }
  return (
    <>
      <a className="skip-link" href="#main-content">
        Ir para o conteúdo
      </a>
      <div className="app-layout">
        <aside className="sidebar">
          <a
            className="brand"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              navigate("overview", true);
            }}
            aria-label="AI Request Classifier — visão geral"
          >
            <span className="brand-icon">AC</span>
            <span>
              <strong>
                AI Request
                <br /> Classifier
              </strong>
              <small>Contexto para decidir.</small>
            </span>
          </a>
          <p className="nav-label">CENTRAL DE SOLICITAÇÕES</p>
          <nav
            className="main-nav"
            role="tablist"
            aria-label="Áreas da aplicação"
            aria-orientation={mobileNav ? "horizontal" : "vertical"}
          >
            {PAGES.map(([id, title, icon], index) => (
              <button
                ref={(el) => {
                  navRefs.current[index] = el;
                }}
                id={`tab-${id}`}
                role="tab"
                aria-selected={page === id}
                aria-controls={`panel-${id}`}
                tabIndex={page === id ? 0 : -1}
                key={id}
                className={page === id ? "active" : ""}
                onClick={() => navigate(id)}
                onKeyDown={(e) => navKey(e, index)}
              >
                <Icon name={icon} />
                <span>{title}</span>
                {id === "triage" && records.some(isPending) && (
                  <span className="nav-count" aria-hidden="true">
                    {records.filter(isPending).length}
                  </span>
                )}
              </button>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <Icon name="shield" size={23} />
            <strong>Inteligência com critério.</strong>
            <p>A IA sugere. As regras padronizam. Você decide.</p>
            <span>
              <span className="status-dot" />
              Ambiente local
            </span>
          </div>
        </aside>
        <div className="main-shell">
          <header className="topbar">
            <div className="breadcrumb">
              <span>Central</span>
              <span aria-hidden="true">/</span>
              <strong>{PAGES.find(([id]) => id === page)?.[1]}</strong>
            </div>
            <div className="header-controls">
              <span
                className={`ai-indicator ai-${aiState}`}
                title={
                  aiState === "on"
                    ? "Ativa e configurada no serviço local. Novos cadastros podem consumir créditos; a disponibilidade do provedor é verificada no envio."
                    : aiState === "off"
                      ? "Novos cadastros ficam disponíveis para classificação manual."
                      : "Consulte a configuração local do serviço."
                }
              >
                <Icon name="spark" size={15} />
                {aiLabel}
              </span>
              <div className="theme-control">
                <Icon name="sun" size={17} />
                <label className="sr-only" htmlFor="theme-mode">
                  Tema da interface
                </label>
                <select
                  id="theme-mode"
                  value={theme}
                  onChange={(e) => chooseTheme(e.target.value)}
                >
                  <option value="auto">Automático</option>
                  <option value="light">Claro</option>
                  <option value="dark">Escuro</option>
                </select>
              </div>
            </div>
          </header>
          <main id="main-content" tabIndex={-1}>
            <div className="page-container">
              {(error || configError) && (
                <div className="callout error global-error" role="alert">
                  <div>
                    <strong>Vamos restabelecer a conexão.</strong>
                    <p>{error || configError}</p>
                    <p className="field-help">
                      {hasLoaded
                        ? "Os dados já carregados permanecem visíveis."
                        : "Ainda não há dados confirmados do servidor."}
                    </p>
                  </div>
                  <button
                    className="button secondary"
                    disabled={refreshing}
                    onClick={refresh}
                  >
                    {refreshing ? "Verificando…" : "Tentar novamente"}
                  </button>
                </div>
              )}
              <section
                role="tabpanel"
                id="panel-overview"
                aria-labelledby="tab-overview"
                hidden={page !== "overview"}
              >
                <Overview
                  records={records}
                  loading={loading}
                  unavailable={!hasLoaded && Boolean(error)}
                  navigate={navigate}
                  openRecord={openRecord}
                  guide={guide}
                  dismissGuide={dismissGuide}
                />
              </section>
              <section
                role="tabpanel"
                id="panel-new"
                aria-labelledby="tab-new"
                hidden={page !== "new"}
              >
                <NewRequest
                  config={config}
                  onConfigChange={(next) => {
                    setConfig(next);
                    setConfigError("");
                  }}
                  onCreated={changed}
                  openRecord={openRecord}
                  navigate={navigate}
                  draft={draft}
                  setDraft={setDraft}
                />
              </section>
              <section
                role="tabpanel"
                id="panel-triage"
                aria-labelledby="tab-triage"
                hidden={page !== "triage"}
              >
                <Triage
                  records={records}
                  loading={loading}
                  unavailable={!hasLoaded && Boolean(error)}
                  refresh={refresh}
                  refreshing={refreshing}
                  view={view}
                  setView={setView}
                  onReviewed={changed}
                  navigate={navigate}
                />
              </section>
              <section
                role="tabpanel"
                id="panel-learn"
                aria-labelledby="tab-learn"
                hidden={page !== "learn"}
              >
                <Journey useExample={example} />
              </section>
            </div>
          </main>
          <footer className="app-footer">
            <span>AI Request Classifier</span>
            <span>
              Dados fictícios · Uso local controlado · Decisões humanas
            </span>
          </footer>
        </div>
      </div>
    </>
  );
}
