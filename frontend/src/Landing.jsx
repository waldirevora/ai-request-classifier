import React from "react";
const steps = [
  [
    "O colaborador registra",
    "Uma necessidade de RH, Financeiro ou TI ganha um pedido com contexto.",
  ],
  [
    "A IA analisa",
    "A DeepSeek interpreta a descrição e sugere categoria, impacto, urgência e justificativa.",
  ],
  [
    "As regras validam",
    "Python calcula a prioridade e verifica o destino. Dúvidas seguem para a Central de Exceções.",
  ],
  [
    "O departamento atende",
    "O responsável assume o pedido e mantém o andamento visível.",
  ],
  [
    "O prazo é acompanhado",
    "Regras de SLA identificam risco e atraso, registrando alertas internos.",
  ],
  [
    "A resolução fica registrada",
    "O colaborador recebe a resposta. Os gestores consultam histórico e indicadores.",
  ],
];
export function FirstSteps() {
  return (
    <ol className="sf-first-steps" aria-label="Seus primeiros passos">
      {[
        "Inicie sem login",
        "Descreva um pedido fictício",
        "Acompanhe a análise real da IA",
        "Atue como departamento",
        "Confira resolução e relatório",
      ].map((text, i) => (
        <li key={text}>
          <span aria-hidden="true">{i + 1}</span>
          {text}
        </li>
      ))}
    </ol>
  );
}
export function HeroPreview() {
  return (
    <aside
      className="sf-business-preview"
      aria-label="Exemplo de processo empresarial"
    >
      <p className="eyebrow">UMA NECESSIDADE. UM CAMINHO VISÍVEL.</p>
      <div className="sf-example-message">
        <span>Colaborador · exemplo fictício</span>
        <strong>“Precisamos verificar uma nota fiscal.”</strong>
      </div>
      <div className="sf-preview-connector" aria-hidden="true">
        ↓
      </div>
      <div className="sf-preview-analysis">
        <strong>IA interpreta. Regras verificam.</strong>
        <span>Assunto · prioridade · destino</span>
      </div>
      <div className="sf-preview-connector" aria-hidden="true">
        ↓
      </div>
      <div className="sf-preview-departments">
        <span>Pessoas</span>
        <strong>Financeiro</strong>
        <span>TI</span>
      </div>
      <div className="sf-preview-connector" aria-hidden="true">
        ↓
      </div>
      <div className="sf-example-message">
        <strong>Atendimento acompanhado até a resposta</strong>
        <span>Responsável · prazo · histórico</span>
      </div>
      <p className="field-help">
        Ilustração da jornada. A análise real acontece quando você envia um
        pedido na demonstração.
      </p>
    </aside>
  );
}
export default function Landing({ onExplore, busy, contactUrl }) {
  return (
    <div className="sf-landing">
      <section
        className="sf-product-section sf-section-stack"
        aria-labelledby="business-problem"
      >
        <div className="sf-section-intro">
          <p className="eyebrow">QUANDO O PEDIDO SE PERDE, O PROCESSO PARA</p>
          <h2 id="business-problem">Reconhece alguma dessas situações?</h2>
          <p>
            Um pedido chega por mensagem, outro fica no e-mail e a planilha nem
            sempre conta a história toda.
          </p>
        </div>
        <div className="sf-journey-grid">
          {[
            [
              "RH: “Como está meu pedido?”",
              "Solicitações de férias e benefícios ficam dispersas, sem uma visão clara do andamento.",
            ],
            [
              "Financeiro: “Quem deve atender?”",
              "Notas fiscais e reembolsos circulam entre pessoas, com encaminhamentos manuais e retrabalho.",
            ],
            [
              "TI: “Era para quando?”",
              "Demandas esquecidas, prioridades pouco claras e gestores sem indicadores consolidados.",
            ],
          ].map(([title, text]) => (
            <article className="card sf-problem-card" key={title}>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>
      <section
        className="sf-product-section sf-section-stack"
        aria-labelledby="business-change"
      >
        <div className="sf-section-intro">
          <p className="eyebrow">DO FRAGMENTADO AO ACOMPANHÁVEL</p>
          <h2 id="business-change">
            Veja o que muda no caminho de uma solicitação.
          </h2>
        </div>
        <div className="sf-transformation">
          <article>
            <h3>Um processo fragmentado</h3>
            <ul>
              <li>Mensagens em canais diferentes</li>
              <li>Destino escolhido a cada novo pedido</li>
              <li>Cobranças informais para saber o andamento</li>
              <li>Histórico difícil de reunir</li>
            </ul>
          </article>
          <article>
            <h3>Um fluxo organizado</h3>
            <ul>
              <li>Pedido registrado em um lugar</li>
              <li>IA e regras apoiando o encaminhamento</li>
              <li>Responsável, prazo e andamento visíveis</li>
              <li>Resposta e indicadores disponíveis para consulta</li>
            </ul>
          </article>
        </div>
      </section>
      <section
        className="sf-product-section sf-section-stack"
        id="como-funciona"
        aria-labelledby="flow-journey"
      >
        <div className="sf-section-intro">
          <p className="eyebrow">INTELIGÊNCIA COM CRITÉRIO</p>
          <h2 id="flow-journey">Como funciona na prática?</h2>
          <p>A IA interpreta. As regras validam. O departamento resolve.</p>
        </div>
        <ol className="sf-journey-grid">
          {steps.map(([title, text], i) => (
            <li className="card" key={title}>
              <span className="sf-step-number" aria-hidden="true">
                0{i + 1}
              </span>
              <h3>{title}</h3>
              <p>{text}</p>
            </li>
          ))}
        </ol>
        <p className="field-help">
          Na demonstração, a análise DeepSeek é real. Empresa, departamentos,
          atendimento e passagem do tempo são fictícios. Se uma chamada for
          impedida por limite ou falhar, isso será informado e o pedido seguirá
          para exceção sem uma resposta inventada.
        </p>
      </section>
      <section
        className="sf-product-section sf-section-stack"
        aria-labelledby="flow-audience"
      >
        <div className="sf-section-intro">
          <p className="eyebrow">
            VISIBILIDADE PARA QUEM PEDE E PARA QUEM ATENDE
          </p>
          <h2 id="flow-audience">Cada pessoa encontra seu próximo passo.</h2>
        </div>
        <div className="sf-audience-grid">
          {[
            [
              "Colaboradores",
              "Acompanhe seus pedidos com transparência, do registro à resposta.",
            ],
            [
              "Departamentos",
              "Receba demandas organizadas, identifique prioridades e registre o atendimento.",
            ],
            [
              "Gestores",
              "Acompanhe o fluxo, identifique gargalos e consulte prazos e indicadores.",
            ],
          ].map(([title, text]) => (
            <article className="card" key={title}>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="sf-product-section sf-section-stack">
        <details className="sf-tech-explainer">
          <summary>Por trás da solução</summary>
          <p>
            Uma demonstração prática de engenharia de IA, automação e
            desenvolvimento de soluções corporativas.
          </p>
          <div className="sf-difference-grid">
            {[
              [
                "DeepSeek",
                "Interpreta o pedido e devolve uma sugestão estruturada.",
              ],
              [
                "Python e FastAPI",
                "Aplicam regras determinísticas e coordenam cada etapa pela API.",
              ],
              [
                "PostgreSQL",
                "Preserva pedidos, decisões, reservas de uso e histórico.",
              ],
              [
                "React",
                "Apresenta a jornada de forma responsiva, com temas e feedback.",
              ],
              [
                "Automação de SLA",
                "Acompanha prazos e registra eventos sem gastar tokens em verificações periódicas.",
              ],
              [
                "Segurança e testes",
                "Sessões isoladas, autorização, limites de uso e testes com mocks.",
              ],
            ].map(([title, text]) => (
              <article key={title}>
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              </article>
            ))}
          </div>
        </details>
      </section>
      <section className="sf-demo-cta" aria-labelledby="business-close">
        <p className="eyebrow">UMA SOLUÇÃO QUE PODE SER PERSONALIZADA</p>
        <h2 id="business-close">
          Imagine esse processo adaptado à sua empresa.
        </h2>
        <p>
          Cada empresa possui departamentos, regras e fluxos próprios. O
          SolicitaFlow demonstra como inteligência artificial e automação podem
          ser adaptadas para organizar processos internos e acompanhar
          resultados.
        </p>
        <p>
          Este é um portfólio demonstrativo de uma implementação personalizada,
          sem contratação de um serviço por assinatura.
        </p>
        <div className="sf-hero-actions sf-centered-actions">
          <button
            className="button primary"
            disabled={busy}
            onClick={onExplore}
          >
            {busy ? "Preparando demonstração…" : "Iniciar demonstração"}
          </button>
          {contactUrl && (
            <a
              className="button secondary"
              href={contactUrl}
              rel="noopener noreferrer"
            >
              Conversar sobre uma implementação
            </a>
          )}
        </div>
      </section>
      <section
        className="sf-product-section sf-section-stack sf-faq-section"
        aria-labelledby="flow-faq"
      >
        <div className="sf-section-intro">
          <h2 id="flow-faq">Antes de experimentar</h2>
        </div>
        <div className="sf-faq">
          {[
            [
              "A inteligência artificial resolve as solicitações?",
              "Não. Ela sugere a classificação. Regras validam o encaminhamento e o departamento fictício registra o atendimento e a resolução.",
            ],
            [
              "Quando a revisão humana é necessária?",
              "Quando há ambiguidade, dados insuficientes, destino não confiável ou falha na análise. O pedido permanece salvo na Central de Exceções.",
            ],
            [
              "Preciso informar dados pessoais?",
              "Não. A sessão é anônima e isolada. Use apenas informações inventadas, sem nomes, documentos ou dados da sua empresa.",
            ],
            [
              "O que é real e o que é demonstrativo?",
              "A análise DeepSeek é real quando autorizada pelos limites. Empresa, personagens, atendimento, relógio e SLA são demonstrativos. Não há resposta simulada apresentada como IA real.",
            ],
            [
              "E se a IA estiver indisponível ou a cota terminar?",
              "O pedido aceito continua registrado. A tela informa que a análise não ocorreu ou não foi concluída e o caso segue para exceção.",
            ],
            [
              "Isso pode funcionar com os processos da minha empresa?",
              "A demonstração ilustra uma base que pode ser personalizada. Departamentos, integrações, regras, identidade e políticas exigem levantamento e implementação específicos.",
            ],
          ].map(([question, answer]) => (
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
