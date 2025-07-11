-- Tabela de Organizações (Inquilinos)
CREATE TABLE IF NOT EXISTS Organizacoes (
id SERIAL PRIMARY KEY,
nome VARCHAR(255) UNIQUE NOT NULL,
cnpj VARCHAR(18) UNIQUE,
data_criacao TIMESTAMPTZ DEFAULT NOW()
);
-- Tabela de Administradores (Usuários do Painel)
CREATE TABLE IF NOT EXISTS Administradores (
id SERIAL PRIMARY KEY,
organizacao_id INTEGER NOT NULL REFERENCES Organizacoes(id),
nome VARCHAR(255) NOT NULL,
email VARCHAR(255) UNIQUE NOT NULL,
senha_hash VARCHAR(255) NOT NULL,
cargo VARCHAR(50)
);
-- Tabela de Agricultores (Usuários do Chatbot)
CREATE TABLE IF NOT EXISTS Agricultores (
id SERIAL PRIMARY KEY,
organizacao_id INTEGER NOT NULL REFERENCES Organizacoes(id),
nome VARCHAR(255) NOT NULL,
whatsapp_id VARCHAR(50) UNIQUE NOT NULL,
latitude DECIMAL(10, 8),
longitude DECIMAL(11, 8),
cidade VARCHAR(100),
estado VARCHAR(2),
data_cadastro TIMESTAMPTZ DEFAULT NOW(),
ultima_atividade TIMESTAMPTZ
);
-- Tabela de Safras (Histórico de Produção)
CREATE TABLE IF NOT EXISTS Safras (
id SERIAL PRIMARY KEY,
agricultor_id INTEGER NOT NULL REFERENCES Agricultores(id),
cultura VARCHAR(100) NOT NULL,
ano_safra VARCHAR(10),
area_plantada_ha DECIMAL(10, 2),
produtividade DECIMAL(10, 2),
unidade_medida VARCHAR(20)
);

-- Tabela de Produtos em Estoque (Insumos ou Produção)
CREATE TABLE IF NOT EXISTS Produtos_Estoque (
id SERIAL PRIMARY KEY,
agricultor_id INTEGER NOT NULL REFERENCES Agricultores(id),
nome_produto VARCHAR(255) NOT NULL,
tipo_produto VARCHAR(50) NOT NULL,
unidade_medida VARCHAR(20) NOT NULL,
saldo_atual DECIMAL(10, 2) NOT NULL
);
-- Tabela de Movimentações de Estoque (Entradas e Saídas)
CREATE TABLE IF NOT EXISTS Movimentacoes_Estoque (
id SERIAL PRIMARY KEY,
produto_id INTEGER NOT NULL REFERENCES Produtos_Estoque(id),
tipo_movimentacao VARCHAR(10) NOT NULL,
quantidade DECIMAL(10, 2) NOT NULL,
data_movimentacao TIMESTAMPTZ DEFAULT NOW(),
observacao TEXT
);
-- Tabela de Interações (Log de Conversas)
CREATE TABLE IF NOT EXISTS Interacoes (
id SERIAL PRIMARY KEY,
agricultor_id INTEGER NOT NULL REFERENCES Agricultores(id),
mensagem_usuario TEXT,
resposta_chatbot TEXT,
entidades JSONB,
timestamp TIMESTAMPTZ DEFAULT NOW()
);
-- Tabela Dicionário de Intenções
CREATE TABLE IF NOT EXISTS Intencoes (
id SERIAL PRIMARY KEY,
nome_intencao VARCHAR(100) UNIQUE NOT NULL,
descricao VARCHAR(255)
);
-- Tabela de Ligação (Muitos-para-Muitos entre Interações e Intenções)
CREATE TABLE IF NOT EXISTS Interacoes_Intencoes (
interacao_id INTEGER NOT NULL REFERENCES Interacoes(id) ON DELETE CASCADE,
intencao_id INTEGER NOT NULL REFERENCES Intencoes(id) ON DELETE CASCADE,
PRIMARY KEY (interacao_id, intencao_id)
);
-- Tabela para Estado Temporário da Conversa
CREATE TABLE IF NOT EXISTS conversation_contexts (
whatsapp_id VARCHAR(50) PRIMARY KEY,
context JSONB,
last_updated TIMESTAMPTZ DEFAULT NOW()
);