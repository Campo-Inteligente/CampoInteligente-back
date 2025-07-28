-- =======================
-- TABELA DE ORGANIZAÇÕES
-- =======================
create table if not exists tb_organizacoes (
   id           integer
      generated always as identity
   primary key,
   nome         varchar(255) not null unique,
   cnpj         varchar(18) unique,
   data_criacao timestamptz default current_timestamp
);

-- =========================
-- TABELA DE ADMINISTRADORES
-- =========================
create table if not exists tb_administradores (
   id             integer
      generated always as identity
   primary key,
   organizacao_id integer not null,
   nome           varchar(255) not null,
   email          varchar(255) not null unique,
   senha_hash     varchar(255) not null,
   cargo          varchar(50),
   constraint fk_admin_org foreign key ( organizacao_id )
      references tb_organizacoes ( id )
         on delete cascade
);

-- ========================
-- TABELA DE USUÁRIOS (AGRICULTORES)
-- ========================
create table if not exists tb_usuarios (
   id               integer
      generated always as identity
   primary key,
   organizacao_id   integer not null,
   nome             varchar(255) not null,
   whatsapp_id      varchar(50) unique not null,
   latitude         decimal(10,8),
   longitude        decimal(11,8),
   cidade           varchar(100),
   estado           varchar(2),
   data_cadastro    timestamptz default current_timestamp,
   ultima_atividade timestamptz,
   constraint fk_usuario_org foreign key ( organizacao_id )
      references tb_organizacoes ( id )
         on delete cascade
);

-- ================
-- TABELA DE SAFRAS
-- ================
create table if not exists tb_safras (
   id               integer
      generated always as identity
   primary key,
   agricultor_id    integer not null,
   cultura          varchar(255) not null,
   ano_safra        varchar(10),
   area_plantada_ha decimal(10,2),
   produtividade    decimal(10,2),
   unidade_medida   varchar(20),
   constraint fk_safra_agricultor foreign key ( agricultor_id )
      references tb_usuarios ( id )
         on delete cascade
);

-- ============================
-- TABELA DE PRODUTOS EM ESTOQUE
-- ============================
create table if not exists tb_produtos_estoque (
   id             integer
      generated always as identity
   primary key,
   agricultor_id  integer not null,
   nome           varchar(255) not null,
   tipo_produto   varchar(50) not null,
   unidade_medida varchar(20) not null,
   saldo_atual    decimal(10,2) not null,
   constraint fk_produto_agricultor foreign key ( agricultor_id )
      references tb_usuarios ( id )
         on delete cascade
);

-- =====================================
-- TABELA DE MOVIMENTAÇÕES DE ESTOQUE
-- =====================================
create table if not exists tb_movimentacoes_estoque (
   id                integer
      generated always as identity
   primary key,
   produto_id        integer not null,
   tipo_movimentacao varchar(10) not null check ( tipo_movimentacao in ( 'entrada',
                                                                         'saida' ) ),
   quantidade        decimal(10,2) not null,
   data_movimentacao timestamptz default current_timestamp,
   observacao        varchar(1000),
   constraint fk_movimentacao_produto foreign key ( produto_id )
      references tb_produtos_estoque ( id )
         on delete cascade
);

-- ========================
-- TABELA DE INTERAÇÕES
-- ========================
create table if not exists tb_interacoes (
   id               integer
      generated always as identity
   primary key,
   agricultor_id    integer not null,
   mensagem_usuario varchar(1000),
   resposta_chatbot varchar(1000),
   entidades        jsonb,
   timestamp        timestamptz default current_timestamp,
   constraint fk_interacao_agricultor foreign key ( agricultor_id )
      references tb_usuarios ( id )
         on delete cascade
);

-- =============================
-- TABELA DICIONÁRIO DE INTENÇÕES
-- =============================
create table if not exists tb_intencoes (
   id            integer
      generated always as identity
   primary key,
   nome_intencao varchar(100) not null unique,
   descricao     varchar(500)
);

-- =========================================
-- TABELA DE LIGAÇÃO: INTERAÇÕES X INTENÇÕES
-- =========================================
create table if not exists tb_interacoes_intencoes (
   interacao_id integer not null,
   intencao_id  integer not null,
   primary key ( interacao_id,
                 intencao_id ),
   constraint fk_interacao foreign key ( interacao_id )
      references tb_interacoes ( id )
         on delete cascade,
   constraint fk_intencao foreign key ( intencao_id )
      references tb_intencoes ( id )
         on delete cascade
);

-- ======================================
-- TABELA DE CONTEXTO TEMPORÁRIO DE CONVERSAS
-- ======================================
create table if not exists tb_conversation_contexts (
   whatsapp_id  varchar(50) primary key,
   context      jsonb,
   last_updated timestamptz default current_timestamp
);

-- =============================
-- TABELA DE CONTROLE DE VERSÃO DO SCHEMA
-- =============================
create table if not exists tb_versoes_schema (
   id               integer
      generated always as identity
   primary key,
   data_hora        timestamptz default current_timestamp,
   usuario          varchar(100) not null,
   tipo_operacao    varchar(20) not null check ( tipo_operacao in ( 'CREATE',
                                                                 'ALTER',
                                                                 'DROP',
                                                                 'MIGRATION',
                                                                 'HOTFIX' ) ),
   tabelas_afetadas text not null,
   descricao        text
);

-- ================================
-- VIEW PARA HISTÓRICO DE VERSÕES
-- ================================
create or replace view vw_historico_versoes_schema as
   select id,
          to_char(
             data_hora,
             'YYYY-MM-DD HH24:MI:SS'
          ) as data_hora_fmt,
          usuario,
          tipo_operacao,
          tabelas_afetadas,
          descricao
     from tb_versoes_schema
    order by data_hora desc;

-- ===================
-- ÍNDICES RECOMENDADOS
-- ===================
create index if not exists idx_usuarios_organizacao on
   tb_usuarios (
      organizacao_id
   );
create index if not exists idx_safras_agricultor on
   tb_safras (
      agricultor_id
   );
create index if not exists idx_produtos_agricultor on
   tb_produtos_estoque (
      agricultor_id
   );
create index if not exists idx_movimentacoes_produto_data on
   tb_movimentacoes_estoque (
      produto_id,
      data_movimentacao
   desc );
create index if not exists idx_interacoes_agricultor on
   tb_interacoes (
      agricultor_id
   );

-- VERSÃO: 2025-07-16 09:00 - MARCOSMORAIS
-- VERSÃO: 2025-07-16 10:30 - ABIMAELUANDERSON
-- VERSÃO: 2025-07-16 11:30 - MARCOSMORAIS
-- VERSÃO: 2025-07-16 18:47 - MARCOSMORAIS

-- =============================================
-- TABELAS PADRÃO DO DJANGO PARA AUTENTICAÇÃO
-- =============================================

-- =====================================================
-- TABELAS PADRÃO DO DJANGO PARA AUTENTICAÇÃO
-- PADRÃO CORPORATIVO PERSONALIZADO: PREFIXO "tb_auth_"
-- COMPATÍVEL COM ORM DO DJANGO SE USAR Meta.db_table
-- =====================================================

-- ================================
-- TABELA DE TIPOS DE CONTEÚDO
-- ================================
create table if not exists tb_auth_content_type (
   id        integer
      generated always as identity
   primary key,
   app_label varchar(100) not null,
   model     varchar(100) not null,
   unique ( app_label,
            model )
);

-- ================================
-- TABELA DE PERMISSÕES
-- ================================
create table if not exists tb_auth_permission (
   id              integer
      generated always as identity
   primary key,
   name            varchar(255) not null,
   content_type_id integer not null,
   codename        varchar(100) not null,
   unique ( content_type_id,
            codename ),
   constraint fk_permission_content_type foreign key ( content_type_id )
      references tb_auth_content_type ( id )
         on delete cascade
);

-- ================================
-- TABELA DE GRUPOS
-- ================================
create table if not exists tb_auth_group (
   id   integer
      generated always as identity
   primary key,
   name varchar(150) not null unique
);

-- =======================================
-- TABELA DE PERMISSÕES POR GRUPO
-- =======================================
create table if not exists tb_auth_group_permissions (
   id            integer
      generated always as identity
   primary key,
   group_id      integer not null,
   permission_id integer not null,
   unique ( group_id,
            permission_id ),
   constraint fk_group_perm_group foreign key ( group_id )
      references tb_auth_group ( id )
         on delete cascade,
   constraint fk_group_perm_permission foreign key ( permission_id )
      references tb_auth_permission ( id )
         on delete cascade
);

-- ================================
-- TABELA DE USUÁRIOS
-- ================================
create table if not exists tb_auth_user (
   id           integer
      generated always as identity
   primary key,
   password     varchar(128) not null,
   last_login   timestamptz,
   is_superuser boolean not null,
   username     varchar(150) not null unique,
   first_name   varchar(150) not null,
   last_name    varchar(150) not null,
   email        varchar(254) not null,
   is_staff     boolean not null,
   is_active    boolean not null,
   date_joined  timestamptz not null
);

-- ======================================
-- TABELA DE GRUPOS ATRIBUÍDOS A USUÁRIOS
-- ======================================
create table if not exists tb_auth_user_groups (
   id       integer
      generated always as identity
   primary key,
   user_id  integer not null,
   group_id integer not null,
   unique ( user_id,
            group_id ),
   constraint fk_user_group_user foreign key ( user_id )
      references tb_auth_user ( id )
         on delete cascade,
   constraint fk_user_group_group foreign key ( group_id )
      references tb_auth_group ( id )
         on delete cascade
);

-- ==============================================
-- TABELA DE PERMISSÕES ATRIBUÍDAS AOS USUÁRIOS
-- ==============================================
create table if not exists tb_auth_user_permissions (
   id            integer
      generated always as identity
   primary key,
   user_id       integer not null,
   permission_id integer not null,
   unique ( user_id,
            permission_id ),
   constraint fk_user_perm_user foreign key ( user_id )
      references tb_auth_user ( id )
         on delete cascade,
   constraint fk_user_perm_permission foreign key ( permission_id )
      references tb_auth_permission ( id )
         on delete cascade
);

-- ================================
-- TABELA DE SESSÕES (SESSIONS)
-- ================================
create table if not exists tb_auth_session (
   session_key  varchar(40) primary key,
   session_data text not null,
   expire_date  timestamptz not null
);

-- ================================
-- TABELA DE LOG DE AÇÕES (ADMIN)
-- ================================
create table if not exists tb_auth_admin_log (
   id              integer
      generated always as identity
   primary key,
   action_time     timestamptz not null,
   object_id       text,
   object_repr     varchar(200) not null,
   action_flag     integer not null,
   change_message  text not null,
   content_type_id integer,
   user_id         integer not null,
   constraint fk_adminlog_content_type foreign key ( content_type_id )
      references tb_auth_content_type ( id )
         on delete set null,
   constraint fk_adminlog_user foreign key ( user_id )
      references tb_auth_user ( id )
         on delete cascade
);

-- ================================
-- ÍNDICES RECOMENDADOS
-- ================================
create index if not exists idx_tb_auth_permission_codename on
   tb_auth_permission (
      codename
   );

create index if not exists idx_tb_auth_user_username on
   tb_auth_user (
      username
   );

create index if not exists idx_tb_auth_session_expire_date on
   tb_auth_session (
      expire_date
   );
--------------------------------------------------------
-- ✅ Tabelas Criadas no Script tb_auth_
-- Nº Nome da Tabela	               Função
-- 1	tb_auth_content_type	         Armazena tipos de modelos (Django ContentType).
-- 2	tb_auth_permission	         Define permissões (ligadas a um tipo de conteúdo).
-- 3	tb_auth_group	               Grupos de usuários.
-- 4	tb_auth_group_permissions	   Liga grupos a permissões.
-- 5	tb_auth_user	               Usuários do sistema (equivalente ao modelo User padrão).
-- 6	tb_auth_user_groups	         Liga usuários a grupos.
-- 7	tb_auth_user_permissions	   Liga usuários a permissões individuais.
-- 8	tb_auth_session	            Armazena sessões de usuários autenticados.
-- 9	tb_auth_admin_log	            Registro de ações administrativas (log do admin).
-- 10	tb_auth_content_type	         (já listado) usado em permissões e logs.
-- =====================================================
-- AUTOR..: Marcos Morais
-- NOTA...: Padronizado com prefixo "tb_a_
-- VERSÃO.: 2025-07-24 - INCLUÍDA TABELAS PADRÃO DO DJANGO PARA AUTENTICAÇÃO - AUTOR: MARCOS MORAIS