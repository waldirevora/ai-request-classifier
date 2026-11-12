import React from "react";
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
export function LabGuide({
  who,
  actors,
  switchActor,
  advance,
  fill,
  busy,
  clock,
}) {
  return (
    <section className="sf-lab-banner" aria-label="Jornada do laboratório">
      <div className="sf-lab-title">
        <div>
          <p className="eyebrow">EMPRESA HORIZONTE · FICTÍCIA</p>
          <h2>Explore o fluxo de ponta a ponta.</h2>
          <p>
            Dados isolados por visitante. Simulação determinística, sem chamadas
            ou custos de API.
          </p>
        </div>
        <span className="badge">
          {clock
            ? new Date(clock).toLocaleString("pt-BR")
            : "Relógio exclusivo deste laboratório"}
        </span>
      </div>
      <ol className="sf-lab-steps">
        <li>
          <strong>1. Colaborador</strong>
          <span>Cadastre e acompanhe.</span>
        </li>
        <li>
          <strong>2. Departamento</strong>
          <span>Assuma e registre andamento.</span>
        </li>
        <li>
          <strong>3. Relógio</strong>
          <span>Simule risco e atraso de SLA.</span>
        </li>
        <li>
          <strong>4. Resolução</strong>
          <span>Responda e confira o histórico.</span>
        </li>
      </ol>
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
      <p className="field-help">
        Comece pelo cenário automático. Após assumir no departamento Tecnologia,
        avance 6 horas para risco e mais 8 horas para atraso e escalonamento.
        Registre a resolução, volte à colaboradora e depois consulte a central.
        No cenário ambíguo, a central esclarece o destino.
      </p>
    </section>
  );
}
