-- P13: migração incremental. Não apaga dados existentes.
-- Execute separadamente nos bancos de desenvolvimento e de testes.
BEGIN;
ALTER TABLE public.solicitacoes
  ADD COLUMN IF NOT EXISTS categoria_sugerida VARCHAR(32),
  ADD COLUMN IF NOT EXISTS impacto_sugerido VARCHAR(16),
  ADD COLUMN IF NOT EXISTS urgencia_sugerida VARCHAR(16),
  ADD COLUMN IF NOT EXISTS prioridade_sugerida VARCHAR(8),
  ADD COLUMN IF NOT EXISTS justificativa_ia VARCHAR(500),
  ADD COLUMN IF NOT EXISTS modelo_ia VARCHAR(80),
  ADD COLUMN IF NOT EXISTS tokens_entrada INTEGER,
  ADD COLUMN IF NOT EXISTS tokens_saida INTEGER,
  ADD COLUMN IF NOT EXISTS latencia_ia_ms INTEGER,
  ADD COLUMN IF NOT EXISTS classificado_em TIMESTAMPTZ;
COMMIT;
