import React, { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { EXAMPLES, STATUSES, validateRequest } from "../domain.js";
import { Icon, PageTitle, StatusBadge } from "../components/Primitives.jsx";
export default function NewRequest({
  config,
  onConfigChange,
  onCreated,
  openRecord,
  navigate,
  draft,
  setDraft,
}) {
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const [created, setCreated] = useState(null);
  const titleRef = useRef(null);
  const successRef = useRef(null);
  useEffect(() => {
    if (created) successRef.current?.focus();
  }, [created?.id]);
  useEffect(() => {
    if (draft.titulo || draft.descricao) setCreated(null);
  }, [draft.titulo, draft.descricao]);
  const ai = Boolean(config?.ai_enabled && config?.ai_configured);
  const update = (field, value) => {
    setDraft((d) => ({ ...d, [field]: value }));
    setErrors((e) => ({ ...e, [field]: undefined }));
    setFailure("");
  };
  function useExample(example) {
    setDraft({ titulo: example.title, descricao: example.description });
    setErrors({});
    setCreated(null);
    titleRef.current?.focus();
  }
  async function submit(e) {
    e.preventDefault();
    if (busy || !config) return;
    const invalid = validateRequest(draft.titulo, draft.descricao);
    setErrors(invalid);
    setFailure("");
    if (Object.keys(invalid).length) {
      document
        .getElementById(
          invalid.titulo ? "request-title" : "request-description",
        )
        ?.focus();
      return;
    }
    setBusy(true);
    try {
      const effective = await api.configuracao();
      onConfigChange(effective);
      if (
        effective.ai_enabled !== config.ai_enabled ||
        effective.ai_configured !== config.ai_configured ||
        effective.ai_model !== config.ai_model
      ) {
        setFailure(
          "A configuração da IA mudou. Confira o estado atualizado e o possível consumo de créditos antes de confirmar o envio novamente.",
        );
        return;
      }
      const record = await api.criar({
        titulo: draft.titulo.trim(),
        descricao: draft.descricao.trim(),
      });
      setCreated(record);
      setDraft({ titulo: "", descricao: "" });
      await onCreated(record);
    } catch (error) {
      setErrors(error.fieldErrors || {});
      setFailure(error.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        id="heading-new"
        eyebrow="Dê contexto à sua necessidade"
        title="Nova solicitação"
        description="Uma boa descrição ajuda a IA e o analista a entenderem o que precisa de atenção."
      />
      <div className="new-request-grid">
        <section className="card form-card" aria-labelledby="form-heading">
          {created ? (
            <div className="success-panel" role="status">
              <span className="success-symbol">
                <Icon name="check" size={30} />
              </span>
              <p className="eyebrow">Cadastro confirmado</p>
              <h2 ref={successRef} tabIndex={-1}>
                Solicitação #{created.id} registrada.
              </h2>
              <p>
                Seus dados foram salvos. {STATUSES[created.status]?.description}
              </p>
              <StatusBadge status={created.status} />
              <div className="success-actions">
                <button
                  className="button primary"
                  onClick={() => openRecord(created)}
                >
                  Acompanhar solicitação
                  <Icon name="arrow" />
                </button>
                <button
                  className="button secondary"
                  onClick={() => {
                    setCreated(null);
                    requestAnimationFrame(() => titleRef.current?.focus());
                  }}
                >
                  Cadastrar outra
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="card-heading">
                <div>
                  <h2 id="form-heading">Conte o que aconteceu</h2>
                  <p>
                    Os dois campos são obrigatórios. Utilize somente dados
                    fictícios.
                  </p>
                </div>
                <span className="step-marker">01 / Cadastro</span>
              </div>
              <form onSubmit={submit} noValidate aria-busy={busy}>
                <fieldset disabled={busy} className="form-stack">
                  <legend className="sr-only">Dados da solicitação</legend>
                  <div className="field">
                    <div className="field-label">
                      <label htmlFor="request-title">
                        Título da solicitação
                      </label>
                      <span className="counter">{draft.titulo.length}/120</span>
                    </div>
                    <input
                      ref={titleRef}
                      id="request-title"
                      value={draft.titulo}
                      onChange={(e) => update("titulo", e.target.value)}
                      onBlur={() => {
                        if (draft.titulo)
                          setErrors((v) => ({
                            ...v,
                            titulo: validateRequest(
                              draft.titulo,
                              draft.descricao,
                            ).titulo,
                          }));
                      }}
                      minLength={3}
                      maxLength={120}
                      required
                      placeholder="Ex.: Equipe sem acesso ao sistema de treinamento"
                      aria-invalid={Boolean(errors.titulo)}
                      aria-describedby={`title-help${errors.titulo ? " title-error" : ""}`}
                    />
                    <small className="field-help" id="title-help">
                      Resuma o problema ou pedido em uma frase.
                    </small>
                    {errors.titulo && (
                      <p className="field-error" id="title-error">
                        {errors.titulo}
                      </p>
                    )}
                  </div>
                  <div className="field">
                    <div className="field-label">
                      <label htmlFor="request-description">Descrição</label>
                      <span className="counter">
                        {draft.descricao.length.toLocaleString("pt-BR")}/2.000
                      </span>
                    </div>
                    <textarea
                      id="request-description"
                      value={draft.descricao}
                      onChange={(e) => update("descricao", e.target.value)}
                      minLength={10}
                      maxLength={2000}
                      rows={7}
                      required
                      placeholder="Quem foi afetado? O que aconteceu? Qual é a consequência para o trabalho?"
                      aria-invalid={Boolean(errors.descricao)}
                      aria-describedby={`description-help${errors.descricao ? " description-error" : ""}`}
                    />
                    <small className="field-help" id="description-help">
                      Inclua alcance, prazo e alternativas disponíveis. Evite
                      dados pessoais e senhas.
                    </small>
                    {errors.descricao && (
                      <p className="field-error" id="description-error">
                        {errors.descricao}
                      </p>
                    )}
                  </div>
                  <div className="callout info">
                    <Icon name={ai ? "spark" : "review"} />
                    <p>
                      {!config
                        ? "Verifique a conexão para confirmar o estado da IA antes do envio."
                        : ai
                          ? "A IA está ativa. Enviar esta solicitação pode consumir créditos da DeepSeek. A sugestão passará por revisão humana."
                          : "O cadastro está disponível. Sem IA ativa e configurada, siga com classificação manual pela triagem."}
                    </p>
                  </div>
                  <button
                    className="button primary submit-button"
                    type="submit"
                    disabled={busy || !config}
                  >
                    {busy
                      ? ai
                        ? "Salvando e consultando a IA…"
                        : "Salvando solicitação…"
                      : "Registrar solicitação"}
                    <Icon name="arrow" />
                  </button>
                </fieldset>
                {busy && (
                  <p className="form-feedback" role="status">
                    {ai
                      ? "Seu cadastro é salvo antes da consulta à IA. Aguarde o resultado do envio."
                      : "Aguarde a confirmação do cadastro."}
                  </p>
                )}
                {failure && (
                  <div className="callout error" role="alert">
                    <p>{failure}</p>
                  </div>
                )}
              </form>
            </>
          )}
        </section>
        <aside className="form-aside">
          <section className="card writing-guide">
            <span className="feature-icon">
              <Icon name="book" />
            </span>
            <h2>Contexto faz a diferença.</h2>
            <ol>
              <li>
                <strong>Quem foi afetado?</strong>
                <span>Uma pessoa, uma equipe ou a empresa?</span>
              </li>
              <li>
                <strong>O que está acontecendo?</strong>
                <span>Descreva o problema e quando começou.</span>
              </li>
              <li>
                <strong>Qual a consequência?</strong>
                <span>Há bloqueio, prazo ou alternativa?</span>
              </li>
            </ol>
            <button
              className="text-button"
              onClick={() => navigate("learn", true)}
            >
              Conhecer o fluxo completo
              <Icon name="arrow" size={16} />
            </button>
          </section>
          <section className="card example-card">
            <p className="eyebrow">Precisa de uma ideia?</p>
            <h2>Experimente um exemplo</h2>
            <p>
              Preencha o formulário com dados fictícios. Nada é enviado até você
              confirmar.
            </p>
            {EXAMPLES.map((example) => (
              <button
                className="example-button"
                key={example.title}
                onClick={() => useExample(example)}
                disabled={busy}
              >
                <span>{example.title}</span>
                <Icon name="plus" size={18} />
              </button>
            ))}
          </section>
        </aside>
      </div>
    </>
  );
}
