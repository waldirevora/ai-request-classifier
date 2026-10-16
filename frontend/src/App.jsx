import React, { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api.js";

const CATEGORIAS = [
  ["suporte_ti", "Suporte de TI"],
  ["acessos_permissoes", "Acessos e permissões"],
  ["financeiro", "Financeiro"],
  ["recursos_humanos", "Recursos Humanos"],
  ["outros", "Outros"],
];
const IMPACTOS = [
  ["individual", "Individual"],
  ["equipe", "Equipe"],
  ["empresa", "Empresa"],
];
const URGENCIAS = [
  ["baixa", "Baixa"],
  ["media", "Média"],
  ["alta", "Alta"],
];
const rotulo = (options, value) =>
  options.find(([id]) => id === value)?.[1] || "Não informado";

const labelsStatus = {
  aguardando_revisao: "Aguardando revisão",
  classificacao_falhou: "Falha da IA",
  pendente_classificacao: "IA desabilitada",
  revisada: "Revisada",
};

const formatoData = (value) =>
  value ? new Date(value).toLocaleString("pt-BR") : "—";

function CampoSelect({ label, value, onChange, options }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
      >
        {options.map(([id, descricao]) => (
          <option key={id} value={id}>
            {descricao}
          </option>
        ))}
      </select>
    </label>
  );
}

function NovaSolicitacao({ onCreated }) {
  const [titulo, setTitulo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setFeedback("");
    try {
      const novo = await api.criar({
        titulo: titulo.trim(),
        descricao: descricao.trim(),
      });
      setTitulo("");
      setDescricao("");
      setFeedback(
        `Solicitação #${novo.id} cadastrada. Situação: ${labelsStatus[novo.status] || novo.status}.`,
      );
      await onCreated();
    } catch (error) {
      setFeedback(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel" aria-labelledby="titulo-cadastro">
      <div className="section-header">
        <span className="eyebrow">01 / ENTRADA</span>
        <h2 id="titulo-cadastro">Nova solicitação</h2>
        <p>
          Registre o problema. A IA será acionada automaticamente quando
          habilitada.
        </p>
      </div>
      <form onSubmit={submit} className="stack">
        <label className="field">
          <span>Título</span>
          <input
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            minLength={3}
            maxLength={120}
            placeholder="Ex.: Sistema de pagamentos indisponível"
            required
          />
        </label>
        <label className="field">
          <span>Descrição</span>
          <textarea
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            minLength={10}
            maxLength={2000}
            rows={5}
            placeholder="Quem foi afetado? Qual o impacto e a urgência?"
            required
          />
        </label>
        <button className="button primary" disabled={busy} type="submit">
          {busy ? "Registrando e classificando..." : "Registrar solicitação"}{" "}
          <span aria-hidden="true">↗</span>
        </button>
        {feedback && (
          <p className="message" role="status">
            {feedback}
          </p>
        )}
      </form>
    </section>
  );
}

function PainelRevisao({ registro, onReviewed }) {
  const [modo, setModo] = useState("aceitar");
  const [categoria, setCategoria] = useState("outros");
  const [impacto, setImpacto] = useState("individual");
  const [urgencia, setUrgencia] = useState("baixa");
  const [observacao, setObservacao] = useState("");
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState("");

  useEffect(() => {
    setModo(registro?.status === "aguardando_revisao" ? "aceitar" : "corrigir");
    setCategoria(registro?.categoria_sugerida || "outros");
    setImpacto(registro?.impacto_sugerido || "individual");
    setUrgencia(registro?.urgencia_sugerida || "baixa");
    setObservacao("");
    setErro("");
  }, [
    registro?.id,
    registro?.status,
    registro?.categoria_sugerida,
    registro?.impacto_sugerido,
    registro?.urgencia_sugerida,
  ]);

  if (!registro)
    return (
      <div className="empty-state">Nenhuma solicitação aguardando revisão.</div>
    );
  const podeAceitar = registro.status === "aguardando_revisao";

  async function finalizar() {
    setBusy(true);
    setErro("");
    try {
      const payload =
        modo === "aceitar"
          ? { decisao: "aceitar" }
          : {
              decisao: "corrigir",
              categoria,
              impacto,
              urgencia,
              observacao: observacao.trim(),
            };
      await api.revisar(registro.id, payload);
      await onReviewed();
    } catch (error) {
      setErro(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="review-detail">
      <div className="detail-heading">
        <span className="eyebrow">SOLICITAÇÃO #{registro.id}</span>
        <span
          className={`pill ${registro.status === "aguardando_revisao" ? "ready" : "warning"}`}
        >
          {labelsStatus[registro.status]}
        </span>
      </div>
      <h3>{registro.titulo}</h3>
      <p className="description">{registro.descricao}</p>
      <p className="muted smaller">
        Cadastrada em {formatoData(registro.criado_em)}
      </p>
      <div className="suggestion-box">
        <span className="eyebrow">SUGESTÃO DA IA</span>
        {podeAceitar ? (
          <>
            <div className="facts">
              <div>
                <small>Categoria</small>
                <strong>
                  {rotulo(CATEGORIAS, registro.categoria_sugerida)}
                </strong>
              </div>
              <div>
                <small>Prioridade</small>
                <strong>{registro.prioridade_sugerida?.toUpperCase()}</strong>
              </div>
              <div>
                <small>Impacto</small>
                <strong>{rotulo(IMPACTOS, registro.impacto_sugerido)}</strong>
              </div>
              <div>
                <small>Urgência</small>
                <strong>{rotulo(URGENCIAS, registro.urgencia_sugerida)}</strong>
              </div>
            </div>
            <p className="reason">
              {registro.justificativa_ia || "Sem justificativa disponível."}
            </p>
            <p className="muted smaller">
              Modelo: {registro.modelo_ia || "não informado"}
            </p>
          </>
        ) : (
          <p className="muted">
            Não existe sugestão válida. Você pode classificar manualmente esta
            solicitação.
          </p>
        )}
      </div>
      <div className="decision">
        <span className="eyebrow">DECISÃO HUMANA</span>
        {podeAceitar && (
          <label className="radio-line">
            <input
              type="radio"
              checked={modo === "aceitar"}
              onChange={() => setModo("aceitar")}
            />{" "}
            Aceitar sugestão da IA
          </label>
        )}
        <label className="radio-line">
          <input
            type="radio"
            checked={modo === "corrigir"}
            onChange={() => setModo("corrigir")}
          />{" "}
          {podeAceitar ? "Corrigir sugestão" : "Classificar manualmente"}
        </label>
        {modo === "corrigir" && (
          <div className="correction-grid">
            <CampoSelect
              label="Categoria correta"
              value={categoria}
              onChange={setCategoria}
              options={CATEGORIAS}
            />
            <CampoSelect
              label="Impacto"
              value={impacto}
              onChange={setImpacto}
              options={IMPACTOS}
            />
            <CampoSelect
              label="Urgência"
              value={urgencia}
              onChange={setUrgencia}
              options={URGENCIAS}
            />
            <label className="field full">
              <span>Motivo da correção (mínimo 10 caracteres)</span>
              <textarea
                value={observacao}
                onChange={(e) => setObservacao(e.target.value)}
                minLength={10}
                maxLength={500}
                rows={3}
                placeholder="Por que essa classificação é mais adequada?"
              />
            </label>
            <p className="muted smaller full">
              A prioridade final será calculada pela matriz da P12 no backend.
            </p>
          </div>
        )}
        <button
          className="button primary"
          disabled={
            busy || (modo === "corrigir" && observacao.trim().length < 10)
          }
          onClick={finalizar}
          type="button"
        >
          {busy ? "Salvando decisão..." : "Concluir revisão"}{" "}
          <span aria-hidden="true">→</span>
        </button>
        {erro && (
          <p className="message error" role="alert">
            {erro}
          </p>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [pendentes, setPendentes] = useState([]);
  const [concluidas, setConcluidas] = useState([]);
  const [solicitacoes, setSolicitacoes] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [aba, setAba] = useState("pendentes");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(true);

  const carregar = useCallback(async () => {
    try {
      const [fila, historico, lista] = await Promise.all([
        api.pendentes(),
        api.concluidas(),
        api.listar(),
      ]);
      setPendentes(fila);
      setConcluidas(historico);
      setSolicitacoes(lista);
      setSelectedId((current) =>
        fila.some((item) => item.id === current)
          ? current
          : (fila[0]?.id ?? null),
      );
      setErro("");
    } catch (error) {
      setErro(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);
  const selecionada = useMemo(
    () => pendentes.find((item) => item.id === selectedId),
    [pendentes, selectedId],
  );

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brandmark">
          <span className="brand-icon">AC</span>
          <div>
            <strong>AI Request Classifier</strong>
            <small>Triagem inteligente · MVP local</small>
          </div>
        </div>
        <span className="top-label">
          <span className="live-dot" /> AMBIENTE DE DESENVOLVIMENTO
        </span>
      </header>
      <main>
        <div className="hero">
          <div>
            <span className="eyebrow">CENTRAL OPERACIONAL / P14</span>
            <h1>
              Solicitações, <em>sob controle.</em>
            </h1>
            <p>IA sugere. Regras padronizam. Pessoas decidem.</p>
          </div>
          <div className="hero-stats">
            <div>
              <strong>{pendentes.length}</strong>
              <span>Pendentes</span>
            </div>
            <div>
              <strong>{concluidas.length}</strong>
              <span>Revisadas</span>
            </div>
          </div>
        </div>
        {erro && (
          <p className="message error global" role="alert">
            {erro}{" "}
            <button className="button small" onClick={carregar}>
              Tentar novamente
            </button>
          </p>
        )}
        <div className="layout">
          <div className="sidebar-column">
            <NovaSolicitacao onCreated={carregar} />
            <section className="panel compact" aria-labelledby="ultimas">
              <div className="section-header">
                <span className="eyebrow">VISÃO GERAL</span>
                <h2 id="ultimas">Solicitações recentes</h2>
              </div>
              {loading ? (
                <p className="muted">Carregando...</p>
              ) : solicitacoes.length === 0 ? (
                <p className="muted">Nenhuma solicitação cadastrada.</p>
              ) : (
                <ul className="recent-list">
                  {[...solicitacoes]
                    .reverse()
                    .slice(0, 6)
                    .map((r) => (
                      <li key={r.id}>
                        <span>
                          <strong>
                            #{r.id} · {r.titulo}
                          </strong>
                          <small>{labelsStatus[r.status] || r.status}</small>
                        </span>
                        <time>{formatoData(r.criado_em)}</time>
                      </li>
                    ))}
                </ul>
              )}
            </section>
          </div>
          <section
            className="panel queue-panel"
            aria-labelledby="titulo-revisao"
          >
            <div className="section-header">
              <span className="eyebrow">02 / DECISÃO</span>
              <h2 id="titulo-revisao">Revisão humana</h2>
              <p>Valide cada sugestão antes de concluir a triagem.</p>
            </div>
            <div
              className="tabs"
              role="tablist"
              aria-label="Situação das revisões"
            >
              <button
                role="tab"
                aria-selected={aba === "pendentes"}
                className={aba === "pendentes" ? "active" : ""}
                onClick={() => setAba("pendentes")}
              >
                Pendentes <span>{pendentes.length}</span>
              </button>
              <button
                role="tab"
                aria-selected={aba === "concluidas"}
                className={aba === "concluidas" ? "active" : ""}
                onClick={() => setAba("concluidas")}
              >
                Concluídas <span>{concluidas.length}</span>
              </button>
              <button
                className="refresh"
                onClick={carregar}
                title="Atualizar dados"
                aria-label="Atualizar dados"
              >
                ↻
              </button>
            </div>
            {aba === "pendentes" ? (
              <div className="review-layout">
                <nav className="queue-list" aria-label="Solicitações pendentes">
                  {pendentes.length === 0 && (
                    <p className="muted empty-list">Nenhuma pendência.</p>
                  )}
                  {pendentes.map((r) => (
                    <button
                      key={r.id}
                      className={`queue-item ${selectedId === r.id ? "selected" : ""}`}
                      onClick={() => setSelectedId(r.id)}
                    >
                      <span className="queue-item-top">
                        <span>#{r.id}</span>
                        <span
                          className={
                            r.status === "aguardando_revisao"
                              ? "dot ready"
                              : "dot warning"
                          }
                        />
                      </span>
                      <strong>{r.titulo}</strong>
                      <small>{labelsStatus[r.status]}</small>
                    </button>
                  ))}
                </nav>
                <PainelRevisao registro={selecionada} onReviewed={carregar} />
              </div>
            ) : (
              <div className="history-list">
                {concluidas.length === 0 && (
                  <p className="muted">Nenhuma revisão concluída.</p>
                )}
                {concluidas.map((r) => (
                  <article className="history-item" key={r.id}>
                    <div>
                      <strong>
                        #{r.id} · {r.titulo}
                      </strong>
                      <p>
                        {rotulo(CATEGORIAS, r.categoria_final)} · prioridade{" "}
                        {r.prioridade_final} ·{" "}
                        {r.decisao_revisao === "aceitar"
                          ? "sugestão aceita"
                          : "corrigida"}
                      </p>
                      {r.observacao_revisao && (
                        <p className="muted">{r.observacao_revisao}</p>
                      )}
                    </div>
                    <time>{formatoData(r.revisado_em)}</time>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
        <footer>
          AI Request Classifier · P14 · Ambiente local sem autenticação. Não
          expor à internet.
        </footer>
      </main>
    </div>
  );
}
