import React from "react";
import {
  CATEGORIES,
  IMPACTS,
  URGENCIES,
  PRIORITIES,
  STATUSES,
  label,
} from "../domain.js";
const paths = {
  grid: ["M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"],
  plus: ["M12 5v14M5 12h14"],
  review: [
    "M8 4H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3M9 2h6v4H9zM9 12l3 3 8-8",
  ],
  route: ["M4 5h13a3 3 0 0 1 0 6H7a3 3 0 0 0 0 6h13M17 14l3 3-3 3"],
  arrow: ["M5 12h14M13 6l6 6-6 6"],
  back: ["M19 12H5M11 6l-6 6 6 6"],
  check: ["M5 12l4 4L19 6"],
  clock: ["M12 8v4l3 2", "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0"],
  spark: ["M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3"],
  shield: ["M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3M8 12l3 3 5-6"],
  refresh: [
    "M20 7v5h-5M4 17v-5h5M6 7a7 7 0 0 1 12-2l2 3M4 16l2 3a7 7 0 0 0 12-2",
  ],
  book: ["M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1v15"],
  close: ["M6 6l12 12M6 18L18 6"],
  sun: [
    "M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5",
    "M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  ],
  search: ["M21 21l-5-5", "M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0"],
};
export function Icon({ name, size = 20 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {(paths[name] || paths.spark).map((d, i) => (
        <path key={i} d={d} />
      ))}
    </svg>
  );
}
export function StatusBadge({ status }) {
  const entry = STATUSES[status] || {
    label: "Situação não informada",
    tone: "neutral",
  };
  return (
    <span className={`badge ${entry.tone}`}>
      <span className="status-dot" />
      {entry.label}
    </span>
  );
}
export function PriorityBadge({ value }) {
  return (
    <span className={`priority priority-${value || "none"}`}>
      {value ? label(PRIORITIES, value) : "A definir"}
    </span>
  );
}
export function PageTitle({ id, eyebrow, title, description, children }) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 id={id} tabIndex={-1}>
          {title}
        </h1>
        <p className="page-description">{description}</p>
      </div>
      {children && <div className="heading-actions">{children}</div>}
    </div>
  );
}
export function EmptyState({ icon = "review", title, children, action }) {
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <Icon name={icon} size={28} />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
      {action}
    </div>
  );
}
export function Facts({ category, impact, urgency, priority: value }) {
  return (
    <dl className="facts">
      <div>
        <dt>Categoria</dt>
        <dd>{label(CATEGORIES, category)}</dd>
      </div>
      <div>
        <dt>Prioridade</dt>
        <dd>
          <PriorityBadge value={value} />
        </dd>
      </div>
      <div>
        <dt>Impacto</dt>
        <dd>{label(IMPACTS, impact)}</dd>
      </div>
      <div>
        <dt>Urgência</dt>
        <dd>{label(URGENCIES, urgency)}</dd>
      </div>
    </dl>
  );
}
export function SelectField({
  id,
  label: title,
  value,
  onChange,
  options,
  help,
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{title}</label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-describedby={help ? `${id}-help` : undefined}
      >
        {options.map(([key, name]) => (
          <option key={key} value={key}>
            {name}
          </option>
        ))}
      </select>
      {help && (
        <small id={`${id}-help`} className="field-help">
          {help}
        </small>
      )}
    </div>
  );
}
