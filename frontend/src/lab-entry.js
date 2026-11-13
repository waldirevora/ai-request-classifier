import { portalApi } from "./portal-api.js";

function entryLock(action) {
  return globalThis.navigator?.locks
    ? navigator.locks.request("solicitaflow-lab-entry", action)
    : action();
}

// One in-flight entry across all buttons. No background effect creates a workspace.
export function makeLabEntry(client = portalApi, now = () => Date.now()) {
  let pending = null;
  let limitedError = null;
  return function enter() {
    if (pending) return pending;
    pending = entryLock(async () => {
      try {
        return { who: await client("lab", "/session"), resumed: true };
      } catch (error) {
        if (error.status !== 401) throw error;
      }
      // A valid session can always resume, even during the creation cooldown.
      if (limitedError?.retryAt > now()) throw limitedError;
      try {
        return {
          who: await client("lab", "/lab/start", { method: "POST" }),
          resumed: false,
        };
      } catch (error) {
        if (error.status === 429) limitedError = error;
        throw error;
      }
    }).finally(() => {
      pending = null;
    });
    return pending;
  };
}

export const enterLaboratory = makeLabEntry();

export function nextLabStep(who, records, selected) {
  const current = selected || records[0];
  if (who.role === "central")
    return records.some((r) => r.state === "excecao")
      ? "Abra a solicitação com revisão necessária e esclareça o destino. Depois confira SLA e relatórios."
      : "Consulte SLA e relatórios para acompanhar os departamentos, prazos e resoluções.";
  if (who.role === "departamento") {
    if (!current)
      return "Escolha o departamento que recebeu o pedido. Sua fila aparecerá logo abaixo.";
    if (current.state === "encaminhada")
      return "Abra o pedido, descreva sua primeira ação e assuma o atendimento.";
    if (current.state === "resolvida")
      return "Volte ao Colaborador para conferir a resposta e à Central para consultar o relatório.";
    return "Registre o andamento. Avance 6 horas e depois mais 8 para observar os alertas. Por fim, confirme a resolução.";
  }
  if (!current)
    return "Comece pelo Exemplo de TI: confira o exemplo fictício e envie sua primeira solicitação.";
  if (current.state === "excecao")
    return "O pedido precisa de esclarecimento. Entre como Central Operacional para revisar a exceção.";
  if (current.state === "resolvida")
    return "Abra seu pedido para ler a resposta. Depois entre na Central Operacional e veja o relatório.";
  return "Seu pedido está salvo. Entre como Departamento para assumir e acompanhar o atendimento.";
}
