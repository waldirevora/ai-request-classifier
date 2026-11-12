import React, { useState } from "react";
import {
  EXAMPLES,
  IMPACTS,
  URGENCIES,
  PRIORITIES,
  MATRIX,
  label,
  priority,
} from "../domain.js";
import {
  Icon,
  PageTitle,
  Facts,
  PriorityBadge,
  SelectField,
} from "../components/Primitives.jsx";
const STEPS = [
  ["Cadastro", "O contexto vem de você", "plus"],
  ["Inteligência artificial", "Uma sugestão estruturada", "spark"],
  ["Regras de prioridade", "Consistência por definição", "grid"],
  ["Revisão humana", "Uma decisão responsável", "shield"],
];
export default function Journey({ useExample }) {
  const [step, setStep] = useState(0);
  const [exampleIndex, setExampleIndex] = useState(0);
  const [impact, setImpact] = useState("equipe");
  const [urgency, setUrgency] = useState("alta");
  const [corrected, setCorrected] = useState(false);
  const example = EXAMPLES[exampleIndex];
  return (
    <>
      <PageTitle
        id="heading-learn"
        eyebrow="Conheça a jornada"
        title="Da descrição à decisão."
        description="Explore um exemplo fictício e descubra onde entram a IA, as regras e a análise humana."
      />
      <div className="learning-notice">
        <span className="badge info">
          <Icon name="book" size={15} />
          Tutorial interativo
        </span>
        <p>
          Ambiente de aprendizado: nenhuma etapa deste tutorial envia dados à
          DeepSeek ou altera solicitações.
        </p>
      </div>
      <nav className="journey-steps" aria-label="Etapas da jornada">
        {STEPS.map(([title, hint, icon], i) => (
          <button
            key={title}
            className={step === i ? "active" : ""}
            aria-current={step === i ? "step" : undefined}
            onClick={() => setStep(i)}
          >
            <span className="step-number">
              {i < step ? (
                <Icon name="check" size={17} />
              ) : (
                String(i + 1).padStart(2, "0")
              )}
            </span>
            <span>
              <strong>{title}</strong>
              <small>{hint}</small>
            </span>
            <Icon name={icon} />
          </button>
        ))}
      </nav>
      <div className="journey-progress">
        <span>Etapa {step + 1} de 4</span>
        <progress
          value={step + 1}
          max={4}
          aria-label={`Progresso do tutorial: etapa ${step + 1} de 4`}
        />
      </div>
      <section className="card lesson" aria-live="polite">
        <div className="lesson-heading">
          <span className="lesson-icon">
            <Icon name={STEPS[step][2]} size={27} />
          </span>
          <div>
            <p className="eyebrow">
              {String(step + 1).padStart(2, "0")} / {STEPS[step][0]}
            </p>
            <h2>
              {
                [
                  "Uma boa triagem começa com contexto.",
                  "A IA organiza o que foi descrito.",
                  "Prioridade é uma regra, não um palpite.",
                  "Quem conhece o contexto dá a palavra final.",
                ][step]
              }
            </h2>
          </div>
        </div>
        {step === 0 && (
          <div className="lesson-grid">
            <div className="lesson-copy">
              <p>
                Uma solicitação é um registro de uma necessidade ou problema.
                Ela permite que outra pessoa compreenda a situação e faça a
                triagem.
              </p>
              <ul className="check-list">
                <li>
                  <Icon name="check" />
                  Descreva quem foi afetado.
                </li>
                <li>
                  <Icon name="check" />
                  Explique o problema e sua consequência.
                </li>
                <li>
                  <Icon name="check" />
                  Informe prazos e alternativas disponíveis.
                </li>
              </ul>
              <div className="field">
                <label htmlFor="journey-example">
                  Escolha um exemplo fictício
                </label>
                <select
                  id="journey-example"
                  value={exampleIndex}
                  onChange={(e) => setExampleIndex(Number(e.target.value))}
                >
                  {EXAMPLES.map((x, i) => (
                    <option key={x.title} value={i}>
                      {x.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="example-preview">
              <span className="badge neutral">Exemplo fictício</span>
              <h3>{example.title}</h3>
              <p>{example.description}</p>
              <button
                className="text-button"
                onClick={() => useExample(example)}
              >
                Usar este exemplo no cadastro
                <Icon name="arrow" size={17} />
              </button>
              <small>
                O envio só acontece quando você confirmar o formulário.
              </small>
            </div>
          </div>
        )}
        {step === 1 && (
          <div className="lesson-grid">
            <div className="lesson-copy">
              <p>
                A DeepSeek interpreta o título e a descrição e sugere quatro
                informações. A aplicação valida os campos antes de guardar a
                resposta.
              </p>
              <dl className="concept-list">
                <div>
                  <dt>Categoria</dt>
                  <dd>Qual é o assunto principal?</dd>
                </div>
                <div>
                  <dt>Impacto</dt>
                  <dd>Qual é o alcance do problema?</dd>
                </div>
                <div>
                  <dt>Urgência</dt>
                  <dd>Há bloqueio ou prazo relevante?</dd>
                </div>
                <div>
                  <dt>Justificativa</dt>
                  <dd>Quais evidências sustentam a sugestão?</dd>
                </div>
              </dl>
            </div>
            <div className="example-preview">
              <span className="badge info">
                Resultado ilustrativo · não enviado à IA
              </span>
              <h3>Uma possível classificação</h3>
              <Facts
                category={example.category}
                impact={example.impact}
                urgency={example.urgency}
                priority={priority(example.impact, example.urgency)}
              />
              <div className="reason-box">
                <strong>Justificativa ilustrativa</strong>
                <p>{example.reason}</p>
              </div>
              <small>
                A prioridade exibida aqui vem da matriz de regras. A IA pode
                errar; sua sugestão sempre precisa de revisão.
              </small>
            </div>
          </div>
        )}
        {step === 2 && (
          <div className="lesson-grid matrix-lesson">
            <div className="lesson-copy">
              <p>
                A IA sugere impacto e urgência. O Python cruza esses dois
                valores na matriz determinística de prioridade. A mesma
                combinação sempre produz o mesmo resultado.
              </p>
              <div className="matrix-controls">
                <SelectField
                  id="demo-impact"
                  label="Simular impacto"
                  value={impact}
                  onChange={setImpact}
                  options={IMPACTS}
                  help="Individual: uma pessoa. Equipe: um grupo. Empresa: alcance organizacional amplo."
                />
                <SelectField
                  id="demo-urgency"
                  label="Simular urgência"
                  value={urgency}
                  onChange={setUrgency}
                  options={URGENCIES}
                  help="Baixa: pode aguardar. Média: prazo relevante. Alta: bloqueio imediato com consequência."
                />
              </div>
              <div className="matrix-result" role="status">
                <span>
                  {label(IMPACTS, impact)} + urgência{" "}
                  {label(URGENCIES, urgency).toLowerCase()}
                </span>
                <Icon name="arrow" size={18} />
                <PriorityBadge value={priority(impact, urgency)} />
              </div>
              <small className="muted">
                Esta é a matriz atual do MVP, não um compromisso de prazo de
                atendimento.
              </small>
            </div>
            <div className="matrix-wrap">
              <table className="priority-matrix">
                <caption>Matriz de prioridade — impacto × urgência</caption>
                <thead>
                  <tr>
                    <th scope="col">Impacto</th>
                    {URGENCIES.map(([value, name]) => (
                      <th scope="col" key={value}>
                        Urgência
                        <br />
                        {name.toLowerCase()}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {IMPACTS.map(([value, name]) => (
                    <tr key={value}>
                      <th scope="row">{name}</th>
                      {URGENCIES.map(([u]) => (
                        <td
                          key={u}
                          className={
                            impact === value && urgency === u
                              ? "matrix-active"
                              : ""
                          }
                        >
                          {label(PRIORITIES, MATRIX[value][u])}
                          {impact === value && urgency === u && (
                            <span className="sr-only">
                              {" "}
                              — combinação selecionada
                            </span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="matrix-footnote">
                <Icon name="shield" size={17} />A prioridade final também é
                recalculada após a revisão humana.
              </p>
            </div>
          </div>
        )}
        {step === 3 && (
          <div className="lesson-grid">
            <div className="lesson-copy">
              <p>
                O analista confronta a sugestão com o contexto. Pode aceitar os
                valores ou corrigi-los com uma explicação. A sugestão original é
                preservada para comparação.
              </p>
              <div
                className="segmented learning-decision"
                role="group"
                aria-label="Simulação da decisão humana"
              >
                <button
                  aria-pressed={!corrected}
                  onClick={() => setCorrected(false)}
                >
                  Simular aceite
                </button>
                <button
                  aria-pressed={corrected}
                  onClick={() => setCorrected(true)}
                >
                  Simular correção
                </button>
              </div>
              <p>
                {corrected
                  ? "Neste cenário ilustrativo, uma verificação posterior confirma que somente uma pessoa foi afetada e existe alternativa de trabalho. O analista corrige impacto e urgência."
                  : "Neste cenário ilustrativo, o analista confirma as evidências e mantém a sugestão."}
              </p>
              <div className="callout info">
                <Icon name="shield" />
                <p>
                  Classificar não resolve automaticamente o chamado. A revisão
                  registra uma decisão de triagem.
                </p>
              </div>
            </div>
            <div className="example-preview">
              <span className="badge success">
                Decisão ilustrativa · sem salvar dados
              </span>
              <h3>
                {corrected ? "Classificação corrigida" : "Sugestão aceita"}
              </h3>
              <Facts
                category={example.category}
                impact={corrected ? "individual" : example.impact}
                urgency={corrected ? "media" : example.urgency}
                priority={priority(
                  corrected ? "individual" : example.impact,
                  corrected ? "media" : example.urgency,
                )}
              />
              <p className="field-help">
                A prioridade resulta dos valores finais de impacto e urgência.
              </p>
            </div>
          </div>
        )}
      </section>
      <div className="lesson-navigation">
        <button
          className="button secondary"
          disabled={step === 0}
          onClick={() => setStep((v) => v - 1)}
        >
          <Icon name="back" size={17} />
          Anterior
        </button>
        {step < 3 ? (
          <button
            className="button primary"
            onClick={() => setStep((v) => v + 1)}
          >
            Próxima etapa
            <Icon name="arrow" size={17} />
          </button>
        ) : (
          <button
            className="button primary"
            onClick={() => useExample(example)}
          >
            Experimentar no cadastro
            <Icon name="arrow" size={17} />
          </button>
        )}
      </div>
    </>
  );
}
