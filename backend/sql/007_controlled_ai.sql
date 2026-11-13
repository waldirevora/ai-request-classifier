BEGIN;
ALTER TABLE sf_cases ADD COLUMN submission_hash char(64),
 ADD COLUMN analysis_status varchar(24) NOT NULL DEFAULT 'historical',
 ADD COLUMN analysis_code varchar(50), ADD COLUMN analysis_started_at timestamptz,
 ADD COLUMN analysis_finished_at timestamptz;
ALTER TABLE sf_cases ADD CONSTRAINT sf_analysis_status CHECK(analysis_status IN ('historical','queued','running','succeeded','failed','blocked'));
CREATE TABLE sf_ai_attempts (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 request_id bigint NOT NULL UNIQUE REFERENCES solicitacoes(id),
 workspace_id uuid NOT NULL REFERENCES sf_workspaces,
 case_id uuid, day date NOT NULL,
 status varchar(16) NOT NULL CHECK(status IN ('reserved','succeeded','failed')),
 reserved_tokens integer NOT NULL CHECK(reserved_tokens>0),
 reserved_usd numeric(12,8) NOT NULL CHECK(reserved_usd>0),
 input_tokens integer, output_tokens integer, model varchar(100), error_code varchar(50),
 created_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
 FOREIGN KEY(workspace_id,case_id) REFERENCES sf_cases(workspace_id,id)
);
CREATE INDEX sf_ai_daily ON sf_ai_attempts(day);
CREATE INDEX sf_ai_workspace ON sf_ai_attempts(workspace_id);
CREATE TABLE sf_legacy_submissions (
 workspace_id uuid NOT NULL REFERENCES sf_workspaces, client_key uuid NOT NULL,
 request_id bigint NOT NULL UNIQUE REFERENCES solicitacoes(id), payload_hash char(64) NOT NULL, analysis_code varchar(50),
 PRIMARY KEY(workspace_id,client_key)
);
COMMIT;
