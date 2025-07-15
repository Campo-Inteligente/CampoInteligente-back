-- =======================
-- TABELA DE ORGANIZAÇÕES
-- =======================
CREATE TABLE IF NOT EXISTS tb_organizacoes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    cnpj VARCHAR(18) UNIQUE,
    data_criacao TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- TABELA DE ADMINISTRADORES
-- =========================
CREATE TABLE IF NOT EXISTS tb_administradores (
    id SERIAL PRIMARY KEY,
    organizacao_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    cargo VARCHAR(50),
    CONSTRAINT fk_admin_org FOREIGN KEY (organizacao_id) REFERENCES tb_organizacoes (id) ON DELETE CASCADE
);

-- ===================
-- TABELA DE AGRICULTORES
-- ===================
CREATE TABLE IF NOT EXISTS tb_usuarios (
    id SERIAL PRIMARY KEY,
    organizacao_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    whatsapp_id VARCHAR(50) UNIQUE NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    data_cadastro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ultima_atividade TIMESTAMPTZ,
    CONSTRAINT fk_usuario_org FOREIGN KEY (organizacao_id) REFERENCES tb_organizacoes (id) ON DELETE CASCADE
);

-- ==================
-- TABELA DE SAFRAS
-- ==================
CREATE TABLE IF NOT EXISTS tb_safras (
    id SERIAL PRIMARY KEY,
    agricultor_id INTEGER NOT NULL,
    cultura TEXT NOT NULL,
    ano_safra VARCHAR(10),
    area_plantada_ha DECIMAL(10, 2),
    produtividade DECIMAL(10, 2),
    unidade_medida VARCHAR(20),
    CONSTRAINT fk_safra_agricultor FOREIGN KEY (agricultor_id) REFERENCES tb_usuarios (id) ON DELETE CASCADE
);

-- ============================
-- TABELA DE PRODUTOS EM ESTOQUE
-- ============================
CREATE TABLE IF NOT EXISTS tb_produtos_estoque (
    id SERIAL PRIMARY KEY,
    agricultor_id INTEGER NOT NULL,
    nome_produto TEXT NOT NULL,
    tipo_produto VARCHAR(50) NOT NULL,
    unidade_medida VARCHAR(20) NOT NULL,
    saldo_atual DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_produto_agricultor FOREIGN KEY (agricultor_id) REFERENCES tb_usuarios (id) ON DELETE CASCADE
);

-- ================================
-- TABELA DE MOVIMENTAÇÕES DE ESTOQUE
-- ================================
CREATE TABLE IF NOT EXISTS tb_movimentacoes_estoque (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER NOT NULL,
    tipo_movimentacao VARCHAR(10) NOT NULL CHECK (tipo_movimentacao IN ('entrada', 'saida')),
    quantidade DECIMAL(10, 2) NOT NULL,
    data_movimentacao TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    observacao TEXT,
    CONSTRAINT fk_movimentacao_produto FOREIGN KEY (produto_id) REFERENCES tb_produtos_estoque (id) ON DELETE CASCADE
);

-- ========================
-- TABELA DE INTERAÇÕES
-- ========================
CREATE TABLE IF NOT EXISTS tb_interacoes (
    id SERIAL PRIMARY KEY,
    agricultor_id INTEGER NOT NULL,
    mensagem_usuario TEXT,
    resposta_chatbot TEXT,
    entidades JSONB,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_interacao_agricultor FOREIGN KEY (agricultor_id) REFERENCES tb_usuarios (id) ON DELETE CASCADE
);

-- ===========================
-- TABELA DICIONÁRIO DE INTENÇÕES
-- ===========================
CREATE TABLE IF NOT EXISTS tb_intencoes (
    id SERIAL PRIMARY KEY,
    nome_intencao VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT
);

-- =========================================
-- TABELA DE LIGAÇÃO: INTERAÇÕES X INTENÇÕES
-- =========================================
CREATE TABLE IF NOT EXISTS tb_interacoes_intencoes (
    interacao_id INTEGER NOT NULL,
    intencao_id INTEGER NOT NULL,
    PRIMARY KEY (interacao_id, intencao_id),
    CONSTRAINT fk_interacao FOREIGN KEY (interacao_id) REFERENCES tb_interacoes (id) ON DELETE CASCADE,
    CONSTRAINT fk_intencao FOREIGN KEY (intencao_id) REFERENCES tb_intencoes (id) ON DELETE CASCADE
);

-- ======================================
-- TABELA DE CONTEXTO TEMPORÁRIO DE CONVERSAS
-- ======================================
CREATE TABLE IF NOT EXISTS tb_conversation_contexts (
    whatsapp_id VARCHAR(50) PRIMARY KEY,
    context JSONB,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
