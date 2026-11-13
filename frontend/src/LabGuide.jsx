import React from "react";
import { nextLabStep } from "./lab-entry.js";
import { FirstSteps } from "./Landing.jsx";

export const LAB_EXAMPLES = {
  clear: {
    titulo: "Servidor indisponível para a equipe",
    descricao:
      "A equipe fictícia está impedida de trabalhar porque o servidor está parado desde o início do expediente. Precisamos restabelecer a operação.",
  },
  ambiguous: {
    titulo: "Dúvida entre tecnologia e financeiro",
    descricao:
      "A equipe fictícia relata uma falha no servidor e também uma fatura de pagamento incorreta. Ainda não está claro qual assunto precisa ser tratado primeiro.",
  },
};
const roles = [
  [
    "colaborador",
    "Colaborador",
    "Cria solicitações, acompanha o destino e confere a resposta.",
  ],
  [
    "departamento",
    "Departamento",
    "Recebe o pedido, assume o atendimento e confirma a resolução.",
  ],
  [
    "central",
    "Central Operacional",
    "Acompanha SLA, esclarece exceções e consulta relatórios.",
  ],
];

export function LabGuide({
  who,
  actors,
  switchActor,
  advance,
  fill,
  busy,
  clock,
  records,
  selected,
  restart,
}) {
  const request =
    selected ||
    records.find((r) => r.department_id && r.state !== "resolvida") ||
    records[0];
  const department =
    actors.find(
      (a) =>
        a.role === "departamento" && a.department_id === request?.department_id,
    ) ||
    actors.find((a) => a.username === "suporte_ti") ||
    actors.find((a) => a.role === "departamento");
  return (
    <section className="sf-lab-banner" aria-label="Jornada do laboratório">
      <div className="sf-lab-title">
        <div>
          <p className="eyebrow">EMPRESA HORIZONTE · DEMONSTRAÇÃO GRATUITA</p>
          <h2>Você está em um ambiente fictício.</h2>
          <p>
            Seu laboratório é separado do de outros visitantes. Use apenas dados
            inventados. A classificação é simulada e não consome créditos de IA.
          </p>
        </div>
        <span className="badge">
          {clock
            ? new Date(clock).toLocaleString("pt-BR")
            : "Relógio da demonstração"}
        </span>
      </div>
      <div
        className="sf-character-cards"
        aria-label="Escolha seu personagem fictício"
      >
        {roles.map(([id, title, text]) => {
          const target =
            id === "departamento"
              ? department?.username
              : actors.find((a) => a.role === id)?.username;
          return (
            <button
              key={id}
              className={
                who.role === id ? "sf-character active" : "sf-character"
              }
              aria-pressed={who.role === id}
              disabled={busy || !target}
              onClick={() => switchActor(target)}
            >
              <span className="sf-role-label">
                {who.role === id ? "Personagem ativo" : "Entrar como"}
              </span>
              <strong>{title}</strong>
              <span>{text}</span>
            </button>
          );
        })}
      </div>
      <div className="sf-next-step">
        <strong>Seu próximo passo</strong>
        <p>{nextLabStep(who, records, selected)}</p>
        <span className="field-help">Você está como {who.display_name}.</span>
      </div>
      <div className="sf-lab-controls">
        <label>
          Personagem fictício
          <select
            aria-label="Personagem fictício"
            value={who.username}
            disabled={busy}
            onChange={(e) => switchActor(e.target.value)}
          >
            {actors.map((a) => (
              <option key={a.username} value={a.username}>
                {a.display_name}
              </option>
            ))}
          </select>
        </label>
        {who.role !== "colaborador" && (
          <>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => advance(6)}
            >
              Avançar 6 horas
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => advance(8)}
            >
              Avançar 8 horas
            </button>
          </>
        )}
        {who.role === "colaborador" && (
          <>
            <button
              className="button primary"
              disabled={busy}
              onClick={() => fill(LAB_EXAMPLES.clear)}
            >
              Cenário automático
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => fill(LAB_EXAMPLES.ambiguous)}
            >
              Cenário ambíguo
            </button>
          </>
        )}
      </div>
      <details className="sf-guide-details">
        <summary>Ver o roteiro e recomeçar a orientação</summary>
        <FirstSteps />
        <p>
          Após assumir no departamento, registre andamento, avance 6 horas para
          ver risco de SLA e mais 8 para atraso e escalonamento. Registre a
          resolução e confira a resposta como Colaborador e os indicadores como
          Central.
        </p>
        <p>
          Recomeçar volta ao personagem Colaborador e ao início do roteiro. Seus
          pedidos e o relógio são mantidos; nenhum laboratório novo é criado.
        </p>
        <button className="button secondary" onClick={restart} disabled={busy}>
          Recomeçar roteiro
        </button>
      </details>
    </section>
  );
}
