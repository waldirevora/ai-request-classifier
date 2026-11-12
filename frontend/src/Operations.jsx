import React, { useEffect, useState } from "react";
const date = (x) =>
  x ? new Date(x).toLocaleString("pt-BR") : "Ainda não registrada";

export function WorkPanel({ record, who, call, busy, run, onChanged }) {
  const [message, setMessage] = useState("");
  useEffect(() => setMessage(""), [record.id]);
  const act = (action) =>
    run(async () => {
      const next = await call(`/cases/${record.id}/transition`, {
        method: "POST",
        body: { action, message },
      });
      setMessage("");
      await onChanged(next);
    });
  const owns = record.responsible_id === who.id;
  return (
    <section className="sf-result">
      <h3>Atendimento e prazos</h3>
      <dl>
        <dt>Primeira resposta até</dt>
        <dd>{date(record.first_response_due)}</dd>
        <dt>Resolução até</dt>
        <dd>{date(record.resolution_due)}</dd>
        <dt>Primeira resposta</dt>
        <dd>{date(record.first_response_at)}</dd>
        <dt>Resolução efetiva</dt>
        <dd>{date(record.resolved_at)}</dd>
      </dl>
      <p>
        Os parâmetros de SLA são fictícios para o laboratório. A contagem usa
        regras determinísticas, sem IA.
      </p>
      {record.resolution && (
        <div className="callout success">
          <strong>Resposta do departamento</strong>
          <p>{record.resolution}</p>
        </div>
      )}
      {who.role === "departamento" && record.state !== "resolvida" && (
        <div className="sf-form">
          {record.responsible_id && (
            <p>
              {owns
                ? "Você é responsável por este atendimento."
                : "Outro integrante já assumiu o atendimento."}
            </p>
          )}
          <label>
            Registro de atendimento
            <textarea
              minLength={10}
              maxLength={1000}
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Descreva a ação realizada ou a resposta ao colaborador."
            />
          </label>
          {record.state === "encaminhada" && (
            <button
              className="button primary"
              disabled={busy || message.trim().length < 10}
              onClick={() => act("assumir")}
            >
              Assumir atendimento
            </button>
          )}
          {owns && record.state === "em_atendimento" && (
            <>
              <button
                className="button secondary"
                disabled={busy || message.trim().length < 10}
                onClick={() => act("andamento")}
              >
                Registrar andamento
              </button>
              <button
                className="button secondary"
                disabled={busy || message.trim().length < 10}
                onClick={() => act("aguardar")}
              >
                Aguardar colaborador
              </button>
            </>
          )}
          {owns && record.state === "aguardando_colaborador" && (
            <button
              className="button secondary"
              disabled={busy || message.trim().length < 10}
              onClick={() => act("retomar")}
            >
              Retomar atendimento
            </button>
          )}
          {owns &&
            ["em_atendimento", "aguardando_colaborador"].includes(
              record.state,
            ) && (
              <button
                className="button primary"
                disabled={busy || message.trim().length < 10}
                onClick={() => act("resolver")}
              >
                Confirmar resolução efetiva
              </button>
            )}
        </div>
      )}
    </section>
  );
}

export function OperationalReports({ call, run, busy }) {
  const [report, setReport] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [policies, setPolicies] = useState([]);
  async function load() {
    const [r, n, p] = await Promise.all([
      call("/reports"),
      call("/notifications"),
      call("/sla/policies"),
    ]);
    setReport(r);
    setAlerts(n);
    setPolicies(p);
  }
  useEffect(() => {
    run(load);
  }, []);
  return (
    <section className="card sf-detail">
      <p className="eyebrow">CENTRAL OPERACIONAL</p>
      <h2>SLAs, cobranças e relatórios</h2>
      <p>
        Agendamento determinístico. Alertas internos, sem envio a contatos
        externos.
      </p>
      <button
        className="button secondary"
        disabled={busy}
        onClick={() =>
          run(async () => {
            await call("/sla/evaluate", { method: "POST" });
            await load();
          })
        }
      >
        Verificar prazos agora
      </button>
      {report && (
        <>
          <p>
            Relógio do ambiente: {date(report.effective_now)} · {report.total}{" "}
            pedidos · {report.exceptions} exceções
          </p>
          <div className="sf-table-wrap">
            <table className="sf-table">
              <caption>Indicadores por departamento</caption>
              <thead>
                <tr>
                  {[
                    "Departamento",
                    "Total",
                    "Resolvidas",
                    "Em risco",
                    "Em atraso",
                    "1ª resposta média (h)",
                    "Resolução média (h)",
                  ].map((x) => (
                    <th key={x} scope="col">
                      {x}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {report.departments.map((d) => (
                  <tr key={d.department}>
                    <th scope="row">{d.department}</th>
                    {[
                      d.total,
                      d.resolved,
                      d.at_risk,
                      d.overdue,
                      d.average_first_response_hours ?? "—",
                      d.average_resolution_hours ?? "—",
                    ].map((v, i) => (
                      <td key={i}>{v}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      <h3>Alertas e cobranças internas</h3>
      {!alerts.length && <p>Nenhum alerta registrado.</p>}
      <ul className="sf-timeline">
        {alerts.map((x) => (
          <li key={x.id}>
            <strong>{x.kind.replaceAll("_", " ")}</strong>
            <p>{x.message}</p>
            <time>{date(x.created_at)}</time>
          </li>
        ))}
      </ul>
      <h3>Política fictícia de laboratório</h3>
      <p>
        Alterações afetam novos encaminhamentos. Cada pedido preserva os prazos
        da política recebida.
      </p>
      {policies.map((policy) => (
        <form
          key={policy.priority}
          className="sf-form sf-policy"
          onSubmit={(e) => {
            e.preventDefault();
            const data = new FormData(e.currentTarget);
            run(async () => {
              await call("/sla/policies", {
                method: "PUT",
                body: {
                  priority: policy.priority,
                  ...Object.fromEntries(
                    [...data.entries()].map(([k, v]) => [k, Number(v)]),
                  ),
                },
              });
              await load();
            });
          }}
        >
          <h4>Prioridade {policy.priority}</h4>
          {[
            ["first_response_hours", "Primeira resposta (horas)", 720],
            ["resolution_hours", "Resolução (horas)", 720],
            ["risk_hours", "Antecedência do alerta (horas)", 48],
            ["escalation_hours", "Escalonar após atraso (horas)", 720],
          ].map(([key, label, max]) => (
            <label key={key}>
              {label}
              <input
                type="number"
                name={key}
                min="1"
                max={max}
                defaultValue={policy[key]}
                required
              />
            </label>
          ))}
          <button className="button secondary" disabled={busy}>
            Salvar política {policy.priority}
          </button>
        </form>
      ))}
    </section>
  );
}
