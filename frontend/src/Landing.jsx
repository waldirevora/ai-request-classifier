import React from "react";

const steps = [
  [
    "Solicite",
    "O colaborador explica o que precisa, quem foi afetado e o que aconteceu.",
  ],
  [
    "A IA entende",
    "A inteligência artificial sugere a classificação. Nesta demonstração, essa análise é simulada.",
  ],
  [
    "O sistema encaminha",
    "As regras verificam o destino dos casos claros. Situações ambíguas passam por revisão humana.",
  ],
  [
    "O departamento atende",
    "O setor responsável recebe a solicitação, assume o atendimento e registra o andamento.",
  ],
  [
    "O prazo é acompanhado",
    "O SLA é o prazo combinado para responder e resolver. O sistema acompanha esse prazo e gera alertas.",
  ],
  [
    "A resolução fica registrada",
    "O colaborador confere a resposta. Os gestores acompanham o histórico e os indicadores.",
  ],
];
const audience = [
  [
    "Colaboradores",
    "Solicite e acompanhe sem depender de mensagens ou cobranças informais.",
    "Um lugar para saber como seu pedido está.",
  ],
  [
    "Departamentos",
    "Organize demandas e mantenha os atendimentos visíveis.",
    "Uma fila com destino, responsável e próximos passos.",
  ],
  [
    "Gestores",
    "Acompanhe produtividade, SLA, atrasos e qualidade do atendimento.",
    "Histórico e indicadores para apoiar suas decisões.",
  ],
];
const differences = [
  ["Destino verificado", "IA e regras trabalham juntas no encaminhamento."],
  [
    "Pessoas nas exceções",
    "Revisão humana quando há dúvida ou falta de informação.",
  ],
  [
    "Atendimento visível",
    "Cada departamento registra seu andamento e a resolução.",
  ],
  [
    "Prazos acompanhados",
    "Alertas de risco, cobrança e escalonamento internos.",
  ],
  ["Histórico e relatórios", "Decisões e etapas registradas para consulta."],
  [
    "Transparência para quem pediu",
    "O colaborador acompanha o destino e a resposta.",
  ],
];
const questions = [
  [
    "A inteligência artificial resolve as solicitações?",
    "Não. A IA sugere a classificação; as regras validam o encaminhamento. O departamento responsável atende e confirma a resolução.",
  ],
  [
    "Quando a revisão humana é necessária?",
    "Quando faltam informações, há mais de um assunto, o destino não é válido ou a classificação falha. A central esclarece o caso antes do encaminhamento.",
  ],
  [
    "Quem acompanha o prazo?",
    "O sistema verifica os prazos automaticamente. O departamento acompanha seu atendimento e a central monitora os indicadores de SLA.",
  ],
  [
    "O que acontece quando um departamento atrasa?",
    "São registrados alertas, cobranças e escalonamento internos conforme a política configurada. Os prazos são fictícios no laboratório e não há envio de mensagens a contatos reais.",
  ],
  [
    "O laboratório utiliza dados reais?",
    "Não. A empresa, os personagens e os exemplos são fictícios. Use apenas dados inventados. Seu laboratório é separado do de outros visitantes.",
  ],
  [
    "A demonstração consome créditos de IA?",
    "Não. O laboratório usa uma simulação determinística, identificada na tela, e não envia solicitações à DeepSeek.",
  ],
];

export function FirstSteps() {
  return (
    <ol className="sf-first-steps" aria-label="Seus primeiros passos">
      {[
        "Escolha como explorar",
        "Crie um pedido fictício",
        "Veja o encaminhamento",
        "Simule atendimento e SLA",
        "Confira resposta e relatório",
      ].map((text, index) => (
        <li key={text}>
          <span aria-hidden="true">{index + 1}</span>
          {text}
        </li>
      ))}
    </ol>
  );
}

export default function Landing({ onExplore, busy }) {
  return (
    <div className="sf-landing">
      <section className="sf-product-section" aria-labelledby="what-is-flow">
        <div className="sf-section-intro">
          <p className="eyebrow">UM PEDIDO. UM CAMINHO CLARO.</p>
          <h2 id="what-is-flow">O que é o SolicitaFlow?</h2>
          <p>
            SolicitaFlow é uma plataforma inteligente que ajuda empresas a
            organizar solicitações internas, encaminhar cada pedido ao
            departamento responsável e acompanhar sua resolução.
          </p>
          <p>
            Do primeiro relato à resposta final, cada pessoa encontra o que
            precisa para seguir em frente.
          </p>
        </div>
        <div className="sf-flow-preview" aria-label="Exemplo de jornada">
          <span>Pedido do colaborador</span>
          <span aria-hidden="true">↓</span>
          <strong>Classificação e destino verificado</strong>
          <span aria-hidden="true">↓</span>
          <span>Atendimento com prazo e responsável</span>
          <span aria-hidden="true">↓</span>
          <strong>Resposta registrada para quem solicitou</strong>
        </div>
      </section>
      <section
        className="sf-product-section sf-section-stack"
        id="como-funciona"
        aria-labelledby="flow-journey"
      >
        <div className="sf-section-intro">
          <p className="eyebrow">DO PEDIDO À RESOLUÇÃO</p>
          <h2 id="flow-journey">Como funciona?</h2>
          <p>
            Seis etapas conectam quem precisa de ajuda a quem pode resolver.
          </p>
        </div>
        <ol className="sf-journey-grid">
          {steps.map(([title, text], index) => (
            <li className="card" key={title}>
              <span className="sf-step-number" aria-hidden="true">
                0{index + 1}
              </span>
              <h3>{title}</h3>
              <p>{text}</p>
            </li>
          ))}
        </ol>
      </section>
      <section
        className="sf-product-section sf-section-stack"
        aria-labelledby="flow-audience"
      >
        <div className="sf-section-intro">
          <p className="eyebrow">CADA PESSOA TEM SEU ESPAÇO</p>
          <h2 id="flow-audience">Para quem foi criado?</h2>
        </div>
        <div className="sf-audience-grid">
          {audience.map(([title, text, benefit]) => (
            <article className="card" key={title}>
              <h3>{title}</h3>
              <p>{text}</p>
              <p className="sf-audience-benefit">{benefit}</p>
            </article>
          ))}
        </div>
      </section>
      <section
        className="sf-product-section sf-section-stack"
        aria-labelledby="flow-difference"
      >
        <div className="sf-section-intro">
          <p className="eyebrow">INTELIGÊNCIA COM CRITÉRIO</p>
          <h2 id="flow-difference">O diferencial está no acompanhamento.</h2>
          <p>
            Automatizar a triagem é o começo. Tornar o atendimento compreensível
            é parte do caminho.
          </p>
        </div>
        <div className="sf-difference-grid">
          {differences.map(([title, text]) => (
            <article key={title}>
              <span className="sf-check" aria-hidden="true">
                ✓
              </span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
      <section className="sf-demo-cta" aria-labelledby="flow-try">
        <p className="eyebrow">EXPERIMENTE NA PRÁTICA</p>
        <h2 id="flow-try">Veja o SolicitaFlow funcionando do início ao fim.</h2>
        <p>
          Entre em uma empresa fictícia, troque de personagem, simule a passagem
          do tempo e acompanhe a resolução de um pedido.
        </p>
        <ul className="sf-demo-promises">
          <li>Sem senha</li>
          <li>Sem dados reais</li>
          <li>Sem consumo de créditos de IA</li>
        </ul>
        <button className="button primary" onClick={onExplore} disabled={busy}>
          {busy ? "Preparando demonstração…" : "Explorar laboratório"}
        </button>
        <p className="field-help">
          Se sua sessão estiver válida, você continua de onde parou.
        </p>
      </section>
      <section
        className="sf-product-section sf-section-stack"
        aria-labelledby="flow-faq"
      >
        <div className="sf-section-intro">
          <p className="eyebrow">PARA EXPLORAR COM TRANQUILIDADE</p>
          <h2 id="flow-faq">Perguntas frequentes</h2>
        </div>
        <div className="sf-faq">
          {questions.map(([question, answer]) => (
            <details key={question}>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}
