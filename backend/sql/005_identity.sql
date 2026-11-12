BEGIN;
CREATE TABLE sf_accounts (
 id uuid PRIMARY KEY, workspace_id uuid NOT NULL REFERENCES sf_workspaces,
 username varchar(80) NOT NULL, display_name varchar(100) NOT NULL,
 role varchar(24) NOT NULL CHECK(role IN ('colaborador','departamento','central')),
 department_id uuid, password_hash text,
 UNIQUE(workspace_id,id), UNIQUE(workspace_id,username),
 FOREIGN KEY(workspace_id,department_id) REFERENCES sf_departments(workspace_id,id),
 CHECK((role='departamento')=(department_id IS NOT NULL))
);
ALTER TABLE sf_cases ADD COLUMN requester_id uuid, ADD COLUMN responsible_id uuid;
ALTER TABLE sf_cases ADD FOREIGN KEY(workspace_id,requester_id) REFERENCES sf_accounts(workspace_id,id);
ALTER TABLE sf_cases ADD FOREIGN KEY(workspace_id,responsible_id) REFERENCES sf_accounts(workspace_id,id);
CREATE TABLE sf_sessions (
 token_hash char(64) PRIMARY KEY, workspace_id uuid NOT NULL, account_id uuid NOT NULL,
 expires_at timestamptz NOT NULL,
 FOREIGN KEY(workspace_id,account_id) REFERENCES sf_accounts(workspace_id,id)
);
CREATE TABLE sf_rate_windows (
 key char(64) NOT NULL, bucket bigint NOT NULL, count integer NOT NULL DEFAULT 1,
 PRIMARY KEY(key,bucket)
);
CREATE TABLE sf_ai_budgets (
 workspace_id uuid NOT NULL REFERENCES sf_workspaces, day date NOT NULL, used integer NOT NULL,
 PRIMARY KEY(workspace_id,day)
);
COMMIT;
