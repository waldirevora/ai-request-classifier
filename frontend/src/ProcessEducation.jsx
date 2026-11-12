import React, { useState } from "react";
import { MATRIX, IMPACTS, URGENCIES } from "./domain.js";
export default function ProcessEducation() {
  const [impact, setImpact] = useState("equipe");
  const [urgency, setUrgency] = useState("alta");
  return (
    <>
      <p className="eyebrow">COMO FUNCIONA A V2</p>
      <h1>Automação com regras. Pessoas nas exceções.</h1>
      <p>
        A classificação sugere um caminho. O backend confere o assunto, as
        informações e o destino antes de encaminhar.
      </p>
      <ol className="sf-lab-steps">
        <li>
          <strong>1. Cadastro persistente</strong>
          <span>
            O pedido é salvo antes da análise. Uma falha da IA não elimina os
            dados.
          </span>
        </li>
        <li>
          <strong>2. Sugestão estruturada</strong>
          <span>
            Categoria, impacto, urgência e justificativa. O laboratório usa
            simulação identificada.
          </span>
        </li>
        <li>
          <strong>3. Regras e destino</strong>
          <span>
            Python calcula a prioridade. Categoria inequívoca e destino ativo
            permitem encaminhamento automático.
          </span>
        </li>
        <li>
          <strong>4. Atendimento e resolução</strong>
          <span>
            O departamento assume e responde. Casos ambíguos passam pela revisão
            humana da central.
          </span>
        </li>
      </ol>
      <div className="sf-form sf-result">
        <h2>Experimente a matriz de prioridade</h2>
        <p>
          Impacto indica a abrangência do problema. Urgência indica o prazo e a
          consequência de esperar. Esta regra não é inventada pela IA.
        </p>
        <label>
          Impacto educativo
          <select value={impact} onChange={(e) => setImpact(e.target.value)}>
            {IMPACTS.map(([id, title]) => (
              <option key={id} value={id}>
                {title}
              </option>
            ))}
          </select>
        </label>
        <label>
          Urgência educativa
          <select value={urgency} onChange={(e) => setUrgency(e.target.value)}>
            {URGENCIES.map(([id, title]) => (
              <option key={id} value={id}>
                {title}
              </option>
            ))}
          </select>
        </label>
        <output aria-live="polite">
          Prioridade calculada: <strong>{MATRIX[impact][urgency]}</strong>
        </output>
        <div className="sf-table-wrap">
          <table className="sf-table">
            <caption>Matriz oficial utilizada pelo backend</caption>
            <thead>
              <tr>
                <th scope="col">Impacto / urgência</th>
                {URGENCIES.map(([id, title]) => (
                  <th key={id} scope="col">
                    {title}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {IMPACTS.map(([id, title]) => (
                <tr key={id}>
                  <th scope="row">{title}</th>
                  {URGENCIES.map(([u]) => (
                    <td key={u}>{MATRIX[id][u]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <h2>Por que reservar revisão às exceções?</h2>
      <p>
        Informações incompletas, assuntos múltiplos, destino inexistente ou
        falha de classificação exigem intervenção. A central registra a decisão
        e mantém a sugestão original para auditoria.
      </p>
      <h2>O que acontece depois do encaminhamento?</h2>
      <p>
        O departamento registra atendimento e resolução. O colaborador acompanha
        a resposta. A central monitora prazos e relatórios; alertas e
        escalonamentos seguem políticas fictícias configuráveis, sem consumir
        tokens.
      </p>
    </>
  );
}
