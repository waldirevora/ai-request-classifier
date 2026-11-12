import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api.js";
import {
  CATEGORIES,
  IMPACTS,
  URGENCIES,
  PRIORITIES,
  STATUSES,
  PENDING,
  isPending,
  hasSuggestion,
  priority,
  label,
  dateTime,
  filterRequests,
  validateReview,
} from "../domain.js";
import {
  Icon,
  PageTitle,
  StatusBadge,
  PriorityBadge,
  EmptyState,
  Facts,
  SelectField,
} from "../components/Primitives.jsx";

function ReviewForm({ record, onSaved, onBusy }) {
  const canAccept =
    record.status === "aguardando_revisao" && hasSuggestion(record);
  const [draft, setDraft] = useState({
    decisao: canAccept ? "aceitar" : "corrigir",
    categoria: record.categoria_sugerida || "outros",
    impacto: record.impacto_sugerido || "individual",
    urgencia: record.urgencia_sugerida || "baixa",
    observacao: "",
  });
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState({});
  const [failure, setFailure] = useState("");
  const change = (field, value) => {
    setDraft((d) => ({ ...d, [field]: value }));
    setErrors({});
    setFailure("");
  };
  const predicted =
    draft.decisao === "aceitar"
      ? record.prioridade_sugerida
      : priority(draft.impacto, draft.urgencia);
  async function submit(e) {
    e.preventDefault();
    if (busy) return;
    const invalid = validateReview(draft);
    setErrors(invalid);
    setFailure("");
    if (Object.keys(invalid).length) {
      document.getElementById(`review-note-${record.id}`)?.focus();
      return;
    }
    setBusy(true);
    onBusy(true);
    try {
      const payload =
        draft.decisao === "aceitar"
          ? { decisao: "aceitar", observacao: draft.observacao.trim() || null }
          : { ...draft, observacao: draft.observacao.trim() };
      const updated = await api.revisar(record.id, payload);
      await onSaved(updated);
    } catch (error) {
      setFailure(error.message);
      setErrors(error.fieldErrors || {});
    } finally {
      setBusy(false);
      onBusy(false);
    }
  }
  return (
    <section
      className="detail-card decision-card"
      aria-labelledby={`decision-heading-${record.id}`}
    >
      <div className="section-kicker">
        <Icon name="shield" />
        <span>Decisão humana</span>
      </div>
      <h3 id={`decision-heading-${record.id}`}>
        {canAccept ? "O que você decide?" : "Classifique esta solicitação"}
      </h3>
      <p className="muted">
        {canAccept
          ? "Confira a sugestão e o contexto original antes de registrar sua decisão."
          : "A análise manual está disponível mesmo sem uma resposta da IA."}
      </p>
      <form onSubmit={submit} noValidate aria-busy={busy}>
        <fieldset disabled={busy} className="form-stack">
          <legend className="sr-only">
            Revisão da solicitação {record.id}
          </legend>
          {canAccept && (
            <div className="decision-options">
              <label
                className={`decision-option ${draft.decisao === "aceitar" ? "chosen" : ""}`}
              >
                <input
                  type="radio"
                  name={`decision-${record.id}`}
                  value="aceitar"
                  checked={draft.decisao === "aceitar"}
                  onChange={() => change("decisao", "aceitar")}
                />
                <span>
                  <strong>Aceitar sugestão</strong>
                  <small>Manter a classificação proposta pela IA.</small>
                </span>
              </label>
              <label
                className={`decision-option ${draft.decisao === "corrigir" ? "chosen" : ""}`}
              >
                <input
                  type="radio"
                  name={`decision-${record.id}`}
                  value="corrigir"
                  checked={draft.decisao === "corrigir"}
                  onChange={() => change("decisao", "corrigir")}
                />
                <span>
                  <strong>Corrigir sugestão</strong>
                  <small>
                    Registrar sua própria análise e explicar o motivo.
                  </small>
                </span>
              </label>
            </div>
          )}
          {draft.decisao === "corrigir" && (
            <div className="review-fields">
              <div className="full">
                <SelectField
                  id={`review-category-${record.id}`}
                  label="Categoria"
                  value={draft.categoria}
                  onChange={(v) => change("categoria", v)}
                  options={CATEGORIES}
                  help="O assunto principal do pedido."
                />
              </div>
              <SelectField
                id={`review-impact-${record.id}`}
                label="Impacto"
                value={draft.impacto}
                onChange={(v) => change("impacto", v)}
                options={IMPACTS}
                help="Quem ou qual parte da operação foi afetada?"
              />
              <SelectField
                id={`review-urgency-${record.id}`}
                label="Urgência"
                value={draft.urgencia}
                onChange={(v) => change("urgencia", v)}
                options={URGENCIES}
                help="Há bloqueio imediato ou prazo relevante?"
              />
            </div>
          )}
          <div className="field">
            <label htmlFor={`review-note-${record.id}`}>
              {draft.decisao === "corrigir"
                ? "Motivo da decisão"
                : "Comentário adicional (opcional)"}
            </label>
            <textarea
              id={`review-note-${record.id}`}
              value={draft.observacao}
              onChange={(e) => change("observacao", e.target.value)}
              rows={3}
              maxLength={500}
              required={draft.decisao === "corrigir"}
              aria-invalid={Boolean(errors.observacao)}
              aria-describedby={`review-note-help-${record.id}${errors.observacao ? ` review-note-error-${record.id}` : ""}`}
              placeholder={
                draft.decisao === "corrigir"
                  ? "Explique o contexto que sustenta sua classificação."
                  : "Registre algum contexto adicional, se necessário."
              }
            />
            <small className="field-help" id={`review-note-help-${record.id}`}>
              {draft.decisao === "corrigir"
                ? "Use de 10 a 500 caracteres. A justificativa original da IA será preservada."
                : "Até 500 caracteres."}
            </small>
            {errors.observacao && (
              <p className="field-error" id={`review-note-error-${record.id}`}>
                {errors.observacao}
              </p>
            )}
          </div>
          <div className="priority-preview">
            <div>
              <span className="eyebrow">Prioridade prevista</span>
              <p>
                {draft.decisao === "aceitar"
                  ? "Classificação sugerida, sujeita à confirmação ao salvar."
                  : `${label(IMPACTS, draft.impacto)} + urgência ${label(URGENCIES, draft.urgencia).toLowerCase()}.`}
              </p>
            </div>
            <PriorityBadge value={predicted} />
          </div>
          <p className="field-help">
            A prioridade final é recalculada no servidor pela matriz de regras.
          </p>
          <button
            className="button primary submit-button"
            type="submit"
            disabled={busy}
          >
            {busy ? "Salvando decisão…" : "Concluir revisão"}
            <Icon name="check" />
          </button>
        </fieldset>
        {failure && (
          <div className="callout error" role="alert">
            <p>
              {failure} Se outra pessoa já revisou este registro, atualize os
              dados antes de continuar.
            </p>
          </div>
        )}
      </form>
    </section>
  );
}

function Detail({ record, onSaved, onBusy, back }) {
  const heading = useRef(null);
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, [record.id, record.status]);
  return (
    <div className="detail-column">
      <button className="text-button mobile-back" onClick={back}>
        <Icon name="back" size={17} />
        Voltar para a lista
      </button>
      <section className="detail-card original-card">
        <div className="detail-top">
          <span className="eyebrow">
            Solicitação #{String(record.id).padStart(3, "0")}
          </span>
          <StatusBadge status={record.status} />
        </div>
        <h2 ref={heading} tabIndex={-1}>
          {record.titulo}
        </h2>
        <p className="section-label">Dados originais</p>
        <p className="request-description">{record.descricao}</p>
        <p className="detail-date">
          Cadastrada em {dateTime(record.criado_em)}
        </p>
      </section>
      <section
        className="detail-card suggestion-card"
        aria-labelledby={`suggestion-heading-${record.id}`}
      >
        <div className="section-kicker">
          <Icon name="spark" />
          <span>Sugestão da IA</span>
        </div>
        <h3 id={`suggestion-heading-${record.id}`}>
          {hasSuggestion(record)
            ? "Uma proposta para sua análise"
            : "Sem sugestão registrada"}
        </h3>
        {hasSuggestion(record) ? (
          <>
            <Facts
              category={record.categoria_sugerida}
              impact={record.impacto_sugerido}
              urgency={record.urgencia_sugerida}
              priority={record.prioridade_sugerida}
            />
            <div className="reason-box">
              <strong>Justificativa da IA</strong>
              <p>
                {record.justificativa_ia || "Justificativa não disponível."}
              </p>
            </div>
            <details className="context-details">
              <summary>
                Entender a prioridade e os dados da classificação
              </summary>
              <p>
                {label(IMPACTS, record.impacto_sugerido)} + urgência{" "}
                {label(URGENCIES, record.urgencia_sugerida).toLowerCase()}{" "}
                resulta em prioridade{" "}
                {label(PRIORITIES, record.prioridade_sugerida).toLowerCase()}. O
                Python aplica a matriz; a IA sugere impacto e urgência.
              </p>
              <dl className="technical-facts">
                <div>
                  <dt>Modelo</dt>
                  <dd>{record.modelo_ia || "Não registrado"}</dd>
                </div>
                <div>
                  <dt>Tokens de entrada / saída</dt>
                  <dd>
                    {record.tokens_entrada ?? "—"} /{" "}
                    {record.tokens_saida ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt>Tempo da IA</dt>
                  <dd>
                    {record.latencia_ia_ms != null
                      ? `${record.latencia_ia_ms} ms`
                      : "Não registrado"}
                  </dd>
                </div>
              </dl>
            </details>
          </>
        ) : (
          <div
            className={`callout ${record.status === "classificacao_falhou" ? "warning" : "info"}`}
          >
            <Icon name="review" />
            <p>
              {record.status === "classificacao_falhou"
                ? "A classificação automática não foi concluída. O cadastro foi preservado e pode ser analisado manualmente."
                : "Não há uma resposta de IA salva para este registro. Nenhuma classificação foi preenchida automaticamente."}
            </p>
          </div>
        )}
      </section>
      {isPending(record) ? (
        <ReviewForm
          key={record.id}
          record={record}
          onSaved={onSaved}
          onBusy={onBusy}
        />
      ) : record.status === "revisada" ? (
        <section className="detail-card final-card">
          <div className="section-kicker">
            <Icon name="shield" />
            <span>Decisão humana</span>
          </div>
          <div className="detail-top">
            <h3>Classificação final registrada</h3>
            <span className="badge success">
              <Icon name="check" size={14} />
              {record.decisao_revisao === "aceitar"
                ? "Sugestão aceita"
                : "Classificação corrigida"}
            </span>
          </div>
          <Facts
            category={record.categoria_final}
            impact={record.impacto_final}
            urgency={record.urgencia_final}
            priority={record.prioridade_final}
          />
          <div className="reason-box">
            <strong>Motivo / comentário</strong>
            <p>
              {record.observacao_revisao ||
                "Nenhum comentário adicional registrado."}
            </p>
          </div>
          <p className="detail-date">
            Revisada em {dateTime(record.revisado_em)}
          </p>
        </section>
      ) : null}
    </div>
  );
}

export default function Triage({
  records,
  loading,
  unavailable,
  refresh,
  refreshing,
  view,
  setView,
  onReviewed,
  navigate,
}) {
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const list = useMemo(
    () => filterRequests(records, view.scope, view.status, view.search),
    [records, view.scope, view.status, view.search],
  );
  const selected = records.find((r) => r.id === view.id);
  const updateView = (next) => {
    setView((v) => ({ ...v, ...next }));
    setNotice("");
  };
  async function saved(record) {
    await onReviewed(record);
    setView({ scope: "revisadas", status: "all", search: "", id: record.id });
    setNotice("Decisão salva. A solicitação está em Revisadas.");
  }
  const back = () => {
    const id = view.id;
    updateView({ id: null });
    requestAnimationFrame(() =>
      document.getElementById(`queue-${id}`)?.focus(),
    );
  };
  return (
    <>
      <PageTitle
        id="heading-triage"
        eyebrow="Contexto, análise e decisão"
        title="Triagem e revisão"
        description="Compare os dados originais, a sugestão da IA e a decisão final em um só lugar."
      >
        <button
          className="button secondary"
          onClick={refresh}
          disabled={refreshing || saving}
        >
          <Icon name="refresh" size={17} />
          {refreshing ? "Atualizando…" : "Atualizar dados"}
        </button>
      </PageTitle>
      <div className="triage-toolbar">
        <div className="segmented" role="group" aria-label="Fila de trabalho">
          <button
            aria-pressed={view.scope === "pendentes"}
            disabled={saving}
            onClick={() =>
              updateView({ scope: "pendentes", status: "all", id: null })
            }
          >
            Pendentes
            <span>{unavailable ? "—" : records.filter(isPending).length}</span>
          </button>
          <button
            aria-pressed={view.scope === "revisadas"}
            disabled={saving}
            onClick={() =>
              updateView({ scope: "revisadas", status: "all", id: null })
            }
          >
            Revisadas
            <span>
              {unavailable
                ? "—"
                : records.filter((r) => r.status === "revisada").length}
            </span>
          </button>
        </div>
        <div className="triage-filters">
          <div className="search-field">
            <Icon name="search" size={18} />
            <label className="sr-only" htmlFor="queue-search">
              Buscar por título ou número
            </label>
            <input
              id="queue-search"
              type="search"
              placeholder="Buscar por título ou número"
              value={view.search}
              disabled={saving}
              onChange={(e) => updateView({ search: e.target.value, id: null })}
            />
          </div>
          <div className="filter-field">
            <label className="sr-only" htmlFor="queue-status">
              Filtrar por situação
            </label>
            <select
              id="queue-status"
              value={view.status}
              disabled={saving}
              onChange={(e) => updateView({ status: e.target.value, id: null })}
            >
              <option value="all">Todas as situações</option>
              {(view.scope === "revisadas" ? ["revisada"] : PENDING).map(
                (status) => (
                  <option key={status} value={status}>
                    {STATUSES[status].label}
                  </option>
                ),
              )}
            </select>
          </div>
        </div>
      </div>
      {notice && (
        <div className="callout success review-notice" role="status">
          <Icon name="check" />
          <p>{notice}</p>
        </div>
      )}
      <div className={`review-workspace ${selected ? "has-selection" : ""}`}>
        <section
          className="card queue-panel"
          aria-label="Lista de solicitações"
        >
          <div className="queue-heading">
            <strong>
              {view.scope === "revisadas"
                ? "Decisões registradas"
                : "Aguardando sua análise"}
            </strong>
            <span>
              {unavailable
                ? "Conexão indisponível"
                : `${list.length} ${list.length === 1 ? "registro" : "registros"}`}
            </span>
          </div>
          {loading ? (
            <p className="loading-state" role="status">
              Carregando fila…
            </p>
          ) : unavailable ? (
            <EmptyState
              title="Fila indisponível no momento"
              action={
                <button
                  className="button secondary"
                  onClick={refresh}
                  disabled={refreshing}
                >
                  Atualizar fila
                </button>
              }
            >
              Não foi possível confirmar os registros do servidor.
            </EmptyState>
          ) : list.length === 0 ? (
            <EmptyState
              title="Nenhum registro nesta visualização"
              action={
                view.search || view.status !== "all" ? (
                  <button
                    className="button secondary"
                    onClick={() =>
                      updateView({ search: "", status: "all", id: null })
                    }
                  >
                    Limpar filtros
                  </button>
                ) : (
                  <button
                    className="button secondary"
                    onClick={() => navigate("new", true)}
                  >
                    Nova solicitação
                  </button>
                )
              }
            >
              Altere os filtros ou cadastre uma solicitação fictícia.
            </EmptyState>
          ) : (
            <ul className="queue-list">
              {list.map((r) => (
                <li key={r.id}>
                  <button
                    id={`queue-${r.id}`}
                    className={`queue-item ${view.id === r.id ? "selected" : ""}`}
                    aria-pressed={view.id === r.id}
                    aria-label={`Solicitação #${r.id}: ${r.titulo}. ${STATUSES[r.status]?.label || ""}`}
                    disabled={saving}
                    onClick={() => updateView({ id: r.id })}
                  >
                    <div className="queue-meta">
                      <span>#{String(r.id).padStart(3, "0")}</span>
                      <PriorityBadge
                        value={r.prioridade_final || r.prioridade_sugerida}
                      />
                    </div>
                    <strong>{r.titulo}</strong>
                    <StatusBadge status={r.status} />
                    <small>
                      {dateTime(
                        r.status === "revisada" ? r.revisado_em : r.criado_em,
                      )}
                    </small>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
        {selected ? (
          <Detail
            record={selected}
            onSaved={saved}
            onBusy={setSaving}
            back={back}
          />
        ) : (
          <section className="card selection-placeholder">
            <EmptyState title="Escolha uma solicitação">
              Selecione um registro na lista para consultar o contexto, analisar
              a sugestão e registrar sua decisão.
            </EmptyState>
            <div className="selection-principle">
              <Icon name="shield" />
              <p>
                A IA sugere.
                <br />
                <strong>A decisão final é humana.</strong>
              </p>
            </div>
          </section>
        )}
      </div>
    </>
  );
}
