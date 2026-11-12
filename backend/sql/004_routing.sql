BEGIN;
CREATE TABLE sf_workspaces (
 id uuid PRIMARY KEY, name text NOT NULL, kind text NOT NULL CHECK(kind IN ('local','lab')),
 created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz
);
CREATE UNIQUE INDEX sf_one_local ON sf_workspaces(kind) WHERE kind='local';
CREATE TABLE sf_departments (
 id uuid PRIMARY KEY, workspace_id uuid NOT NULL REFERENCES sf_workspaces,
 name varchar(100) NOT NULL, active boolean NOT NULL DEFAULT true,
 UNIQUE(workspace_id,id), UNIQUE(workspace_id,name)
);
CREATE TABLE sf_routes (
 workspace_id uuid NOT NULL REFERENCES sf_workspaces, category varchar(32) NOT NULL
 CHECK(category IN ('suporte_ti','acessos_permissoes','financeiro','recursos_humanos','outros')),
 department_id uuid NOT NULL, review_required boolean NOT NULL DEFAULT false,
 PRIMARY KEY(workspace_id,category),
 FOREIGN KEY(workspace_id,department_id) REFERENCES sf_departments(workspace_id,id)
);
CREATE TABLE sf_cases (
 id uuid PRIMARY KEY, workspace_id uuid NOT NULL REFERENCES sf_workspaces,
 request_id bigint NOT NULL UNIQUE REFERENCES solicitacoes(id), client_key uuid NOT NULL,
 state varchar(32) NOT NULL DEFAULT 'analisando'
 CHECK(state IN ('analisando','excecao','encaminhada','em_atendimento','aguardando_colaborador','resolvida')),
 department_id uuid, source varchar(16) NOT NULL CHECK(source IN ('simulacao','deepseek')),
 category varchar(32), impact varchar(16), urgency varchar(16), priority varchar(8),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(workspace_id,id), UNIQUE(workspace_id,client_key),
 FOREIGN KEY(workspace_id,department_id) REFERENCES sf_departments(workspace_id,id)
);
CREATE INDEX sf_cases_queue ON sf_cases(workspace_id,state,department_id);
CREATE TABLE sf_routing_decisions (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 workspace_id uuid NOT NULL, case_id uuid NOT NULL, step varchar(16) NOT NULL,
 outcome varchar(16) NOT NULL CHECK(outcome IN ('automatico','manual','excecao')),
 reasons jsonb NOT NULL, department_id uuid, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(case_id,step), FOREIGN KEY(workspace_id,case_id) REFERENCES sf_cases(workspace_id,id),
 FOREIGN KEY(workspace_id,department_id) REFERENCES sf_departments(workspace_id,id)
);
CREATE UNIQUE INDEX sf_route_once ON sf_routing_decisions(case_id) WHERE outcome IN ('automatico','manual');
CREATE TABLE sf_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 workspace_id uuid NOT NULL, case_id uuid NOT NULL, actor_id uuid, type varchar(50) NOT NULL,
 payload jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(workspace_id,case_id) REFERENCES sf_cases(workspace_id,id)
);
CREATE INDEX sf_events_history ON sf_events(workspace_id,case_id,id);
COMMIT;
