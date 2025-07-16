-- =======================
-- TABELA DE ORGANIZAÇÕES
-- =======================
CREATE TABLE IF NOT EXISTS tb_organizacoes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(255) NOT NULL UNIQUE,
    cnpj VARCHAR(18) UNIQUE,
    data_criacao TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- TABELA DE ADMINISTRADORES
-- =========================
CREATE TABLE IF NOT EXISTS tb_administradores (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organizacao_id INTEGER NOT NULL,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    cargo VARCHAR(50),
    data_cadastro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ativo CHAR(1) DEFAULT 'S' CHECK (ativo IN ('S', 'N')),
    CONSTRAINT fk_admin_org FOREIGN KEY (organizacao_id)
        REFERENCES tb_organizacoes (id) ON DELETE CASCADE
);

-- ========================
-- TABELA DE USUÁRIOS (AGRICULTORES)
-- ========================
CREATE TABLE IF NOT EXISTS tb_usuarios (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organizacao_id INTEGER NOT NULL,
    nome VARCHAR(255) NOT NULL,
    whatsapp_id VARCHAR(50) UNIQUE NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    data_cadastro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ultima_atividade TIMESTAMPTZ,
    ativo CHAR(1) DEFAULT 'S' CHECK (ativo IN ('S', 'N')),
    CONSTRAINT fk_usuario_org FOREIGN KEY (organizacao_id)
        REFERENCES tb_organizacoes (id) ON DELETE CASCADE
);

-- ================
-- TABELA DE SAFRAS
-- ================
CREATE TABLE IF NOT EXISTS tb_safras (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    agricultor_id INTEGER NOT NULL,
    cultura VARCHAR(255) NOT NULL,
    ano_safra VARCHAR(10),
    area_plantada_ha DECIMAL(10, 2),
    produtividade DECIMAL(10, 2),
    unidade_medida VARCHAR(20),
    CONSTRAINT fk_safra_agricultor FOREIGN KEY (agricultor_id)
        REFERENCES tb_usuarios (id) ON DELETE CASCADE
);

-- ============================
-- TABELA DE PRODUTOS EM ESTOQUE
-- ============================
CREATE TABLE IF NOT EXISTS tb_produtos_estoque (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    agricultor_id INTEGER NOT NULL,
    nome VARCHAR(255) NOT NULL,
    tipo_produto VARCHAR(50) NOT NULL,
    unidade_medida VARCHAR(20) NOT NULL,
    saldo_atual DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_produto_agricultor FOREIGN KEY (agricultor_id)
        REFERENCES tb_usuarios (id) ON DELETE CASCADE
);

-- =====================================
-- TABELA DE MOVIMENTAÇÕES DE ESTOQUE
-- =====================================
CREATE TABLE IF NOT EXISTS tb_movimentacoes_estoque (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    produto_id INTEGER NOT NULL,
    tipo_movimentacao VARCHAR(10) NOT NULL CHECK (tipo_movimentacao IN ('entrada', 'saida')),
    quantidade DECIMAL(10, 2) NOT NULL,
    data_movimentacao TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    observacao VARCHAR(1000),
    CONSTRAINT fk_movimentacao_produto FOREIGN KEY (produto_id)
        REFERENCES tb_produtos_estoque (id) ON DELETE CASCADE
);

-- ========================
-- TABELA DE INTERAÇÕES
-- ========================
CREATE TABLE IF NOT EXISTS tb_interacoes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    agricultor_id INTEGER NOT NULL,
    mensagem_usuario VARCHAR(1000),
    resposta_chatbot VARCHAR(1000),
    entidades JSONB,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_interacao_agricultor FOREIGN KEY (agricultor_id)
        REFERENCES tb_usuarios (id) ON DELETE CASCADE
);

-- =============================
-- TABELA DICIONÁRIO DE INTENÇÕES
-- =============================
CREATE TABLE IF NOT EXISTS tb_intencoes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome_intencao VARCHAR(100) NOT NULL UNIQUE,
    descricao VARCHAR(500)
);

-- =========================================
-- TABELA DE LIGAÇÃO: INTERAÇÕES X INTENÇÕES
-- =========================================
CREATE TABLE IF NOT EXISTS tb_interacoes_intencoes (
    interacao_id INTEGER NOT NULL,
    intencao_id INTEGER NOT NULL,
    PRIMARY KEY (interacao_id, intencao_id),
    CONSTRAINT fk_interacao FOREIGN KEY (interacao_id)
        REFERENCES tb_interacoes (id) ON DELETE CASCADE,
    CONSTRAINT fk_intencao FOREIGN KEY (intencao_id)
        REFERENCES tb_intencoes (id) ON DELETE CASCADE
);

-- ======================================
-- TABELA DE CONTEXTO TEMPORÁRIO DE CONVERSAS
-- ======================================
CREATE TABLE IF NOT EXISTS tb_conversation_contexts (
    whatsapp_id VARCHAR(50) PRIMARY KEY,
    context JSONB,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===================
-- ÍNDICES RECOMENDADOS
-- ===================
CREATE INDEX IF NOT EXISTS idx_usuarios_organizacao ON tb_usuarios (organizacao_id);
CREATE INDEX IF NOT EXISTS idx_safras_agricultor ON tb_safras (agricultor_id);
CREATE INDEX IF NOT EXISTS idx_produtos_agricultor ON tb_produtos_estoque (agricultor_id);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto_data ON tb_movimentacoes_estoque (produto_id, data_movimentacao DESC);
CREATE INDEX IF NOT EXISTS idx_interacoes_agricultor ON tb_interacoes (agricultor_id);

-- VERSÃO: 2025-07-16 09:00 - MARCOSMORAIS
-- VERSÃO: 2025-07-16 10:30 - ABIMAELUANDERSON
-- VERSÃO: 2025-07-16 11:30 - MARCOSMORAIS
