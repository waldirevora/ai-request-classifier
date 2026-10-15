CREATE TABLE IF NOT EXISTS solicitacoes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    titulo VARCHAR(120) NOT NULL,

    descricao TEXT NOT NULL,

    status VARCHAR(40) NOT NULL
        DEFAULT 'pendente_classificacao',

    criado_em TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_solicitacoes_titulo
        CHECK (char_length(btrim(titulo)) BETWEEN 3 AND 120),

    CONSTRAINT ck_solicitacoes_descricao
        CHECK (char_length(btrim(descricao)) BETWEEN 10 AND 2000)
);
