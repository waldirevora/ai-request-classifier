import React from "react";
import { STATUSES, isPending, dateTime } from "../domain.js";
import {
  Icon,
  PageTitle,
  StatusBadge,
  PriorityBadge,
  EmptyState,
} from "../components/Primitives.jsx";
export default function Overview({
  records,
  loading,
  unavailable,
  navigate,
  openRecord,
  guide,
  dismissGuide,
}) {
  const pending = records.filter(isPending).length;
  const reviewed = records.filter((r) => r.status === "revisada").length;
  const waiting = records.filter(
    (r) => r.status === "aguardando_revisao",
  ).length;
  const stats = [
    ["Solicitações", records.length, "Tudo o que foi registrado", "grid"],
    ["Pendentes", pending, "Precisam de uma decisão", "clock"],
    ["Aguardando revisão", waiting, "Com sugestão da IA", "spark"],
    ["Revisadas", reviewed, "Decisões registradas", "check"],
  ];
  return (
    <>
      <PageTitle
        id="heading-overview"
        eyebrow="Sua central de trabalho"
        title="Sua operação, com clareza."
        description="Acompanhe as solicitações e transforme contexto em boas decisões."
      >
        <button
          className="button primary"
          onClick={() => navigate("new", true)}
        >
          <Icon name="plus" />
          Nova solicitação
        </button>
      </PageTitle>
      {guide && (
        <div className="first-use">
          <span className="guide-symbol">
            <Icon name="book" />
          </span>
          <div>
            <strong>Primeira vez por aqui?</strong>
            <p>
              Conheça a jornada: cadastro, sugestão, prioridade e decisão
              humana.
            </p>
          </div>
          <button
            className="button subtle"
            onClick={() => navigate("learn", true)}
          >
            Explorar a jornada
            <Icon name="arrow" size={16} />
          </button>
          <button
            className="icon-button"
            aria-label="Dispensar orientação inicial"
            onClick={dismissGuide}
          >
            <Icon name="close" size={17} />
          </button>
        </div>
      )}
      <section
        className="stats-grid"
        aria-label="Resumo das solicitações"
        aria-busy={loading}
      >
        {stats.map(([title, value, hint, icon]) => (
          <article className="stat-card" key={title}>
            <div className="stat-top">
              <span>{title}</span>
              <Icon name={icon} />
            </div>
            <strong>{loading || unavailable ? "—" : value}</strong>
            <small>{hint}</small>
          </article>
        ))}
      </section>
      <div className="dashboard-grid">
        <section className="card recent-card">
          <div className="card-heading">
            <div>
              <h2>Solicitações recentes</h2>
              <p>Do cadastro à decisão, acompanhe cada registro.</p>
            </div>
            <button
              className="text-button"
              onClick={() => navigate("triage", true)}
            >
              Ver triagem
              <Icon name="arrow" size={16} />
            </button>
          </div>
          {loading ? (
            <p className="loading-state" role="status">
              Carregando solicitações…
            </p>
          ) : unavailable ? (
            <EmptyState title="Dados indisponíveis no momento">
              Use Tentar novamente para consultar o servidor. Nenhuma contagem
              foi presumida.
            </EmptyState>
          ) : records.length === 0 ? (
            <EmptyState
              icon="plus"
              title="Sua primeira solicitação começa aqui."
              action={
                <button
                  className="button primary"
                  onClick={() => navigate("new", true)}
                >
                  Cadastrar solicitação
                </button>
              }
            >
              Use um exemplo fictício para conhecer o fluxo.
            </EmptyState>
          ) : (
            <div className="table-container">
              <table className="request-table">
                <caption className="sr-only">
                  Últimas seis solicitações cadastradas
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Solicitação</th>
                    <th scope="col">Situação</th>
                    <th scope="col" className="optional-column">
                      Prioridade
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[...records]
                    .sort((a, b) => b.id - a.id)
                    .slice(0, 6)
                    .map((r) => (
                      <tr key={r.id}>
                        <td>
                          <button
                            className="record-link"
                            onClick={() => openRecord(r)}
                          >
                            <small>#{String(r.id).padStart(3, "0")}</small>
                            <strong>{r.titulo}</strong>
                            <span>{dateTime(r.criado_em)}</span>
                          </button>
                        </td>
                        <td>
                          <StatusBadge status={r.status} />
                        </td>
                        <td className="optional-column">
                          <PriorityBadge
                            value={r.prioridade_final || r.prioridade_sugerida}
                          />
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        <aside className="journey-card">
          <span className="feature-icon">
            <Icon name="route" size={27} />
          </span>
          <p className="eyebrow">Inteligência com responsabilidade</p>
          <h2>
            IA sugere.
            <br />
            Você decide.
          </h2>
          <p>
            A prioridade segue regras claras. A decisão final continua nas mãos
            de uma pessoa.
          </p>
          <ol className="mini-journey">
            {[
              "Descrever o problema",
              "Receber uma sugestão",
              "Aplicar a matriz de prioridade",
              "Revisar e registrar a decisão",
            ].map((t, i) => (
              <li key={t}>
                <span>{i + 1}</span>
                {t}
              </li>
            ))}
          </ol>
          <button
            className="button journey-button"
            onClick={() => navigate("learn", true)}
          >
            Entenda como funciona
            <Icon name="arrow" size={17} />
          </button>
        </aside>
      </div>
      <section className="card situations">
        <div className="card-heading">
          <div>
            <h2>O que significa cada situação?</h2>
            <p>O andamento fica visível, mesmo quando a IA não responde.</p>
          </div>
        </div>
        <div className="status-guide">
          {Object.entries(STATUSES).map(([status, entry]) => (
            <article key={status}>
              <StatusBadge status={status} />
              <p>{entry.description}</p>
              <button
                className="text-button"
                onClick={() =>
                  navigate("triage", true, {
                    scope: status === "revisada" ? "revisadas" : "pendentes",
                    status,
                  })
                }
              >
                {loading || unavailable
                  ? "Consultar fila"
                  : `Ver ${records.filter((r) => r.status === status).length} solicitações`}
                <Icon name="arrow" size={15} />
              </button>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
