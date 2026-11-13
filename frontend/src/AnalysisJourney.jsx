import React from "react";
export const analysisMessages = {
  consumo_pendente:
    "Uma análise anterior precisa de conferência pelo responsável. Este pedido foi salvo sem uma nova chamada paga.",
  laboratorio_expirado:
    "Este laboratório expirou e a análise não será repetida.",
  ia_desabilitada: "A análise está desabilitada neste ambiente.",
  chave_ausente: "O serviço de IA está sem configuração disponível.",
  modelo_nao_aprovado:
    "O modelo configurado precisa de validação pelo responsável.",
  politica_invalida: "Os limites de uso precisam de revisão pelo responsável.",
  capacidade_ocupada:
    "Outra análise está em andamento. Este pedido foi preservado na fila de exceções.",
  cota_ambiente: "Este ambiente atingiu sua cota de análises.",
  cota_global: "A cota de análises da demonstração foi atingida hoje.",
  orcamento_esgotado: "O orçamento reservado para análises foi atingido.",
  limite_rede: "O limite de análises para esta rede foi atingido.",
  processamento_interrompido:
    "O processamento foi interrompido e não será repetido automaticamente.",
  http_429: "O provedor não aceitou a chamada por limite ou disponibilidade.",
  http_401: "O provedor não autorizou a chamada.",
  http_503:
    "O serviço de IA está temporariamente indisponível. O pedido permanece salvo.",
  http_502: "O serviço de IA está temporariamente indisponível.",
  http_500: "O provedor apresentou uma falha. O pedido permanece salvo.",
  falha_rede:
    "O provedor não respondeu dentro do prazo ou houve uma falha de conexão.",
};
export default function AnalysisJourney({ record, departments, testMode }) {
  const state = record.analysis_status;
  if (record.source === "simulacao")
    return (
      <div className="callout warning">
        <strong>Registro histórico com simulação</strong>
        <p>
          Este pedido foi criado antes da análise real da V2.6. Sua origem foi
          preservada.
        </p>
      </div>
    );
  if (state === "historical")
    return (
      <div className="callout">
        <strong>Registro anterior à trilha da V2.6</strong>
        <p>
          A sugestão original e o histórico foram preservados. Os novos estados
          de análise não se aplicam retroativamente.
        </p>
      </div>
    );
  const done = state === "succeeded",
    pending = ["queued", "running"].includes(state),
    mock = record.request?.modelo_ia?.startsWith("mock-") || testMode;
  const destination = departments.find(
    (d) => d.id === record.department_id,
  )?.name;
  return (
    <section className="sf-analysis-journey" aria-label="Etapas da análise">
      <p className="eyebrow">
        {mock
          ? "RESPOSTA DE TESTE · SEM CHAMADA EXTERNA"
          : "IA REAL · DEEPSEEK"}{" "}
        / ATENDIMENTO DEMONSTRATIVO
      </p>
      <h3>
        {state === "queued"
          ? "Recebemos sua solicitação."
          : state === "running"
            ? "IA analisando a descrição."
            : done
              ? "A inteligência artificial concluiu a análise."
              : state === "blocked"
                ? "Análise não realizada."
                : "Não foi possível concluir a análise."}
      </h3>
      <p>
        {pending
          ? "O pedido está salvo. Estamos verificando os limites e analisando a descrição para identificar o assunto e o departamento adequado."
          : done
            ? "A sugestão foi validada. A prioridade foi calculada pelas regras Python, preservando a justificativa da IA."
            : analysisMessages[record.analysis_code] ||
              "A resposta não pôde ser validada. Nenhuma classificação foi inventada."}
      </p>
      <div className="sf-analysis-stages">
        <span className="complete">1 · Pedido salvo</span>
        <span className={done ? "complete" : pending ? "current" : ""}>
          2 · Análise da IA
        </span>
        <span className={record.department_id ? "complete" : ""}>
          3 · Destino verificado
        </span>
      </div>
      <dl>
        <dt>Quem atuou</dt>
        <dd>
          {done
            ? mock
              ? "Mock dos testes automatizados"
              : "DeepSeek e regras Python"
            : pending
              ? "Sistema de orquestração"
              : "Controle de uso ou integração de IA"}
        </dd>
        <dt>Resultado</dt>
        <dd>
          {pending
            ? "Análise em andamento"
            : record.department_id
              ? `Encaminhamento validado para ${destination || "o departamento responsável"}.`
              : "Pedido registrado na Central de Exceções."}
        </dd>
        <dt>Próximo passo</dt>
        <dd>
          {pending
            ? "Aguarde a atualização desta tela."
            : record.department_id
              ? "Entre como Departamento para iniciar o atendimento fictício."
              : "Entre como Central Operacional para esclarecer o caso."}
        </dd>
      </dl>
      {!pending && !done && (
        <p className="field-help">
          Não há repetição automática da chamada. O pedido continua disponível
          para revisão humana.
        </p>
      )}
    </section>
  );
}
