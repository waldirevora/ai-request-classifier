BEGIN;
ALTER TABLE sf_workspaces ADD COLUMN clock_hours integer NOT NULL DEFAULT 0 CHECK(clock_hours BETWEEN 0 AND 8760);
ALTER TABLE sf_workspaces ADD CONSTRAINT sf_local_real_clock CHECK(kind='lab' OR clock_hours=0);
CREATE TABLE sf_sla_policies (
 workspace_id uuid NOT NULL REFERENCES sf_workspaces, priority varchar(8) NOT NULL CHECK(priority IN ('baixa','media','alta')),
 first_response_hours integer NOT NULL CHECK(first_response_hours BETWEEN 1 AND 720),
 resolution_hours integer NOT NULL CHECK(resolution_hours BETWEEN 1 AND 720),
 risk_hours integer NOT NULL CHECK(risk_hours BETWEEN 1 AND 48),
 escalation_hours integer NOT NULL CHECK(escalation_hours BETWEEN 1 AND 720),
 PRIMARY KEY(workspace_id,priority), CHECK(first_response_hours<=resolution_hours), CHECK(risk_hours<=resolution_hours)
);
ALTER TABLE sf_cases ADD COLUMN first_response_at timestamptz, ADD COLUMN resolved_at timestamptz,
 ADD COLUMN first_response_due timestamptz, ADD COLUMN resolution_due timestamptz,
 ADD COLUMN resolution text, ADD COLUMN policy_snapshot jsonb;
CREATE TABLE sf_notifications (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 workspace_id uuid NOT NULL, case_id uuid NOT NULL, kind varchar(40) NOT NULL,
 message varchar(500) NOT NULL, created_at timestamptz NOT NULL,
 UNIQUE(case_id,kind), FOREIGN KEY(workspace_id,case_id) REFERENCES sf_cases(workspace_id,id)
);
CREATE INDEX sf_sla_due ON sf_cases(workspace_id,resolution_due) WHERE state<>'resolvida';
COMMIT;
