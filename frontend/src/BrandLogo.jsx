import React from "react";
import "./brand.css";

export default function BrandLogo({
  tagline = "Solicitações inteligentes, do pedido à resolução.",
}) {
  return (
    <span className="sf-brand-identity">
      <span className="sf-brand-logo" role="img" aria-label="SolicitaFlow">
        <img
          className="sf-logo-dark"
          src="/solicitaflow-logo-dark.svg"
          width="980"
          height="240"
          alt=""
          aria-hidden="true"
        />
        <img
          className="sf-logo-light"
          src="/solicitaflow-logo-light.svg"
          width="980"
          height="240"
          alt=""
          aria-hidden="true"
        />
      </span>
      <small>{tagline}</small>
    </span>
  );
}
