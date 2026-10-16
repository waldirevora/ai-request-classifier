-- P14: migração incremental e não destrutiva.
-- Pré-requisito: tabelas de 001 e colunas de IA de 002 já criadas.
-- Executar SEPARADAMENTE nos bancos de desenvolvimento e de testes.
BEGIN;
ALTER TABLE public.solicitacoes
  ADD COLUMN IF NOT EXISTS categoria_final VARCHAR(32),
  ADD COLUMN IF NOT EXISTS impacto_final VARCHAR(16),
  ADD COLUMN IF NOT EXISTS urgencia_final VARCHAR(16),
  ADD COLUMN IF NOT EXISTS prioridade_final VARCHAR(8),
  ADD COLUMN IF NOT EXISTS decisao_revisao VARCHAR(16),
  ADD COLUMN IF NOT EXISTS observacao_revisao VARCHAR(500),
  ADD COLUMN IF NOT EXISTS revisado_em TIMESTAMPTZ;
COMMIT;
