--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13 (Debian 15.13-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: tb_administradores; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_administradores (
    id integer NOT NULL,
    organizacao_id integer NOT NULL,
    nome text NOT NULL,
    email text NOT NULL,
    senha_hash text NOT NULL,
    cargo character varying(50),
    ativo character(1) DEFAULT 'S'::bpchar,
    data_cadastro timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tb_administradores_ativo_check CHECK ((ativo = ANY (ARRAY['S'::bpchar, 'N'::bpchar])))
);


ALTER TABLE public.tb_administradores OWNER TO campo_user;

--
-- Name: tb_administradores_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

CREATE SEQUENCE public.tb_administradores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_administradores_id_seq OWNER TO campo_user;

--
-- Name: tb_administradores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: campo_user
--

ALTER SEQUENCE public.tb_administradores_id_seq OWNED BY public.tb_administradores.id;


--
-- Name: tb_auth_group; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.tb_auth_group OWNER TO campo_user;

--
-- Name: tb_auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_auth_group ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_auth_group_permissions; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.tb_auth_group_permissions OWNER TO campo_user;

--
-- Name: tb_auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_auth_group_permissions ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_auth_permission; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.tb_auth_permission OWNER TO campo_user;

--
-- Name: tb_auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_auth_permission ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_auth_user; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.tb_auth_user OWNER TO campo_user;

--
-- Name: tb_auth_user_groups; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_auth_user_groups (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.tb_auth_user_groups OWNER TO campo_user;

--
-- Name: tb_auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_auth_user_groups ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_auth_user ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_auth_user_permissions; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_auth_user_permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.tb_auth_user_permissions OWNER TO campo_user;

--
-- Name: tb_auth_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_auth_user_permissions ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_auth_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_conversation_contexts; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_conversation_contexts (
    whatsapp_id character varying(50) NOT NULL,
    context jsonb,
    last_updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tb_conversation_contexts OWNER TO campo_user;

--
-- Name: tb_django_admin_log; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag integer NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL
);


ALTER TABLE public.tb_django_admin_log OWNER TO campo_user;

--
-- Name: tb_django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_django_admin_log ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_django_content_type; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.tb_django_content_type OWNER TO campo_user;

--
-- Name: tb_django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_django_content_type ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_django_session; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.tb_django_session OWNER TO campo_user;

--
-- Name: tb_intencoes; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_intencoes (
    id integer NOT NULL,
    nome_intencao character varying(100) NOT NULL,
    descricao text
);


ALTER TABLE public.tb_intencoes OWNER TO campo_user;

--
-- Name: tb_intencoes_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

CREATE SEQUENCE public.tb_intencoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_intencoes_id_seq OWNER TO campo_user;

--
-- Name: tb_intencoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: campo_user
--

ALTER SEQUENCE public.tb_intencoes_id_seq OWNED BY public.tb_intencoes.id;


--
-- Name: tb_interacoes; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_interacoes (
    id integer NOT NULL,
    agricultor_id integer NOT NULL,
    mensagem_usuario text,
    resposta_chatbot text,
    entidades jsonb,
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tb_interacoes OWNER TO campo_user;

--
-- Name: tb_interacoes_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

CREATE SEQUENCE public.tb_interacoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_interacoes_id_seq OWNER TO campo_user;

--
-- Name: tb_interacoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: campo_user
--

ALTER SEQUENCE public.tb_interacoes_id_seq OWNED BY public.tb_interacoes.id;


--
-- Name: tb_interacoes_intencoes; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_interacoes_intencoes (
    interacao_id integer NOT NULL,
    intencao_id integer NOT NULL
);


ALTER TABLE public.tb_interacoes_intencoes OWNER TO campo_user;

--
-- Name: tb_movimentacoes_estoque; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_movimentacoes_estoque (
    id integer NOT NULL,
    produto_id integer NOT NULL,
    tipo_movimentacao character varying(10) NOT NULL,
    quantidade numeric(10,2) NOT NULL,
    data_movimentacao timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    observacao text,
    CONSTRAINT tb_movimentacoes_estoque_tipo_movimentacao_check CHECK (((tipo_movimentacao)::text = ANY ((ARRAY['entrada'::character varying, 'saida'::character varying])::text[])))
);


ALTER TABLE public.tb_movimentacoes_estoque OWNER TO campo_user;

--
-- Name: tb_movimentacoes_estoque_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

CREATE SEQUENCE public.tb_movimentacoes_estoque_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_movimentacoes_estoque_id_seq OWNER TO campo_user;

--
-- Name: tb_movimentacoes_estoque_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: campo_user
--

ALTER SEQUENCE public.tb_movimentacoes_estoque_id_seq OWNED BY public.tb_movimentacoes_estoque.id;


--
-- Name: tb_organizacoes; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_organizacoes (
    id integer NOT NULL,
    nome text NOT NULL,
    cnpj character varying(18),
    data_criacao timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tb_organizacoes OWNER TO campo_user;

--
-- Name: tb_organizacoes_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

CREATE SEQUENCE public.tb_organizacoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_organizacoes_id_seq OWNER TO campo_user;

--
-- Name: tb_organizacoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: campo_user
--

ALTER SEQUENCE public.tb_organizacoes_id_seq OWNED BY public.tb_organizacoes.id;


--
-- Name: tb_produtos_estoque; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_produtos_estoque (
    id integer NOT NULL,
    agricultor_id integer NOT NULL,
    nome_produto text NOT NULL,
    tipo_produto character varying(50) NOT NULL,
    unidade_medida character varying(20) NOT NULL,
    saldo_atual numeric(10,2) NOT NULL
);


ALTER TABLE public.tb_produtos_estoque OWNER TO campo_user;

--
-- Name: tb_produtos_estoque_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

CREATE SEQUENCE public.tb_produtos_estoque_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_produtos_estoque_id_seq OWNER TO campo_user;

--
-- Name: tb_produtos_estoque_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: campo_user
--

ALTER SEQUENCE public.tb_produtos_estoque_id_seq OWNED BY public.tb_produtos_estoque.id;


--
-- Name: tb_safras; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_safras (
    id integer NOT NULL,
    agricultor_id integer NOT NULL,
    cultura text NOT NULL,
    ano_safra character varying(10),
    area_plantada_ha numeric(10,2),
    produtividade numeric(10,2),
    unidade_medida character varying(20)
);


ALTER TABLE public.tb_safras OWNER TO campo_user;

--
-- Name: tb_safras_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

CREATE SEQUENCE public.tb_safras_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_safras_id_seq OWNER TO campo_user;

--
-- Name: tb_safras_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: campo_user
--

ALTER SEQUENCE public.tb_safras_id_seq OWNED BY public.tb_safras.id;


--
-- Name: tb_usuarios; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_usuarios (
    id integer NOT NULL,
    organizacao_id integer NOT NULL,
    nome text NOT NULL,
    whatsapp_id character varying(50) NOT NULL,
    latitude numeric(10,8),
    longitude numeric(11,8),
    cidade character varying(100),
    estado character varying(2),
    data_cadastro timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ultima_atividade timestamp with time zone,
    ativo character(1) DEFAULT 'S'::bpchar,
    CONSTRAINT tb_usuarios_ativo_check CHECK ((ativo = ANY (ARRAY['S'::bpchar, 'N'::bpchar])))
);


ALTER TABLE public.tb_usuarios OWNER TO campo_user;

--
-- Name: tb_usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

CREATE SEQUENCE public.tb_usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_usuarios_id_seq OWNER TO campo_user;

--
-- Name: tb_usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: campo_user
--

ALTER SEQUENCE public.tb_usuarios_id_seq OWNED BY public.tb_usuarios.id;


--
-- Name: tb_versoes_schema; Type: TABLE; Schema: public; Owner: campo_user
--

CREATE TABLE public.tb_versoes_schema (
    id integer NOT NULL,
    data_hora timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    usuario character varying(100) NOT NULL,
    tipo_operacao character varying(20) NOT NULL,
    tabelas_afetadas text NOT NULL,
    descricao text,
    CONSTRAINT tb_versoes_schema_tipo_operacao_check CHECK (((tipo_operacao)::text = ANY ((ARRAY['CREATE'::character varying, 'ALTER'::character varying, 'DROP'::character varying, 'MIGRATION'::character varying, 'HOTFIX'::character varying])::text[])))
);


ALTER TABLE public.tb_versoes_schema OWNER TO campo_user;

--
-- Name: tb_versoes_schema_id_seq; Type: SEQUENCE; Schema: public; Owner: campo_user
--

ALTER TABLE public.tb_versoes_schema ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tb_versoes_schema_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tb_administradores id; Type: DEFAULT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_administradores ALTER COLUMN id SET DEFAULT nextval('public.tb_administradores_id_seq'::regclass);


--
-- Name: tb_intencoes id; Type: DEFAULT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_intencoes ALTER COLUMN id SET DEFAULT nextval('public.tb_intencoes_id_seq'::regclass);


--
-- Name: tb_interacoes id; Type: DEFAULT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_interacoes ALTER COLUMN id SET DEFAULT nextval('public.tb_interacoes_id_seq'::regclass);


--
-- Name: tb_movimentacoes_estoque id; Type: DEFAULT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_movimentacoes_estoque ALTER COLUMN id SET DEFAULT nextval('public.tb_movimentacoes_estoque_id_seq'::regclass);


--
-- Name: tb_organizacoes id; Type: DEFAULT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_organizacoes ALTER COLUMN id SET DEFAULT nextval('public.tb_organizacoes_id_seq'::regclass);


--
-- Name: tb_produtos_estoque id; Type: DEFAULT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_produtos_estoque ALTER COLUMN id SET DEFAULT nextval('public.tb_produtos_estoque_id_seq'::regclass);


--
-- Name: tb_safras id; Type: DEFAULT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_safras ALTER COLUMN id SET DEFAULT nextval('public.tb_safras_id_seq'::regclass);


--
-- Name: tb_usuarios id; Type: DEFAULT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_usuarios ALTER COLUMN id SET DEFAULT nextval('public.tb_usuarios_id_seq'::regclass);


--
-- Data for Name: tb_administradores; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_administradores (id, organizacao_id, nome, email, senha_hash, cargo, ativo, data_cadastro) FROM stdin;
6	1	João Victor Oliveira Santos	jv@gmail.com	$2b$10$mkG81SHdZqD6Aae01/z/KObyZd/GZ0MAFNTejDAzvO/njxC26pwii	admin	S	2025-07-22 14:05:45.74+00
5	1	ARTHUR	arthur@gmail.com	$2b$10$ye4awLYp67ANkdJgJlGkjeQXZ/c2xidc/Y/zooqzoSwGdvW.d/zyu	admin	S	2025-07-19 11:33:14.910579+00
\.


--
-- Data for Name: tb_auth_group; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: tb_auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: tb_auth_permission; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_auth_permission (id, name, content_type_id, codename) FROM stdin;
\.


--
-- Data for Name: tb_auth_user; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
\.


--
-- Data for Name: tb_auth_user_groups; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: tb_auth_user_permissions; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_auth_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: tb_conversation_contexts; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_conversation_contexts (whatsapp_id, context, last_updated) FROM stdin;
webchat_00a90f54-75f4-4728-a8c6-6e39c1e9ed5f	{"localizacao": {"pais": "BR", "cidade": "Ipiau"}, "nome_completo": "Juan", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1752798389.442558, "registros_vermifugacao": [], "awaiting_weather_location": false, "conversational_mode_active": true, "awaiting_weather_follow_up_choice": false}	2025-07-18 00:26:32.942339+00
webchat_4423e7b4-71ac-484c-9e67-996fff6730ac	{"nome_completo": "Como Plantar Maconha?", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1753103902.308811, "registros_vermifugacao": [], "conversational_mode_active": true}	2025-07-21 13:18:24.128333+00
webchat_0bcde266-0d08-4ac3-9e0e-e6de712a3de3	{"nome_completo": "No Celular No Celular, O Campo Para Digitação Não Esta Aparecendo Direito", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "last_interaction_time": 1753109161.826312, "registros_vermifugacao": []}	2025-07-21 14:46:01.869246+00
557388518404@s.whatsapp.net	{"municipio": "Jequié", "nome_completo": "Juan Pablo", "registros_animais": [], "registros_estoque": [], "estado_propriedade": "Bahia", "registros_vacinacao": [], "simulacoes_passadas": [], "last_interaction_time": 1752929296.862144, "registros_vermifugacao": [], "conversational_mode_active": true}	2025-07-19 12:48:18.726475+00
webchat_47e959e7-e815-4a7a-8615-3aabc004e5da	{"nome_completo": "Menu", "awaiting_initial_name": false}	2025-07-21 13:26:48.365521+00
557381023484@s.whatsapp.net	{"nome_completo": "Marcos Morais", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "last_interaction_time": 1753009887.951031, "registros_vermifugacao": []}	2025-07-20 11:11:27.971869+00
webchat_9cdd83a8-9348-45bd-aace-3a06be77a41b	{"localizacao": {"pais": "BR", "cidade": "Jequié-Ba"}, "nome_completo": "Arthur", "dados_simulacao": {"cultura": "Soja"}, "etapa_simulacao": "area", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1752872077.471698, "simulacao_safra_ativa": true, "registros_vermifugacao": [], "awaiting_weather_location": false, "awaiting_weather_follow_up_choice": false}	2025-07-18 20:54:37.481285+00
webchat_64a18b99-74f7-4570-8b52-f75af452eb24	{"awaiting_initial_name": true}	2025-07-22 10:51:25.680436+00
webchat_dde75e99-63b0-4ad5-bb45-ddba8f8c8449	{"nome_completo": "Sou Da Cidade De Jaguaquara-Ba", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1753229324.693544, "registros_vermifugacao": []}	2025-07-23 00:08:44.733639+00
webchat_8babeacc-b3fd-41f7-bad2-bb8ac50c22a6	{"nome_completo": "Arthur", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "last_interaction_time": 1753401871.822193, "registros_vermifugacao": []}	2025-07-25 00:04:31.864475+00
webchat_555f6477-0c53-4e3a-ba53-87160b64ac53	{"awaiting_initial_name": true}	2025-07-21 13:58:03.66329+00
webchat_fb2e4de2-1724-4e43-a6a6-96021573c88d	{"localizacao": {"pais": "BR", "cidade": "Jaguaquara"}, "nome_completo": "Arthur", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "last_interaction_time": 1753107156.46786, "registros_vermifugacao": [], "awaiting_weather_location": false, "conversational_mode_active": true, "awaiting_weather_follow_up_choice": false}	2025-07-21 14:12:36.486816+00
webchat_dea43226-34a4-474a-b4d6-ffb126a19c94	{"nome_completo": "Previsão Do Tempo", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1753138020.688319, "registros_vermifugacao": []}	2025-07-21 22:47:00.727224+00
webchat_f734c5dd-4d49-4a17-b1a7-6aebbff29550	{"nome_completo": "Qual O Melhor Clima Para Plantar Café?", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "last_interaction_time": 1753384082.009836, "registros_vermifugacao": [], "conversational_mode_active": true}	2025-07-24 19:08:02.808703+00
webchat_448bfe42-4d2b-4733-8f18-d37e081b1a86	{"localizacao": {"pais": "BR", "cidade": "Jequié"}, "nome_completo": "Fabio", "registration_step": false, "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1753141563.714327, "registros_vermifugacao": [], "awaiting_weather_location": false, "awaiting_weather_follow_up_choice": true}	2025-07-21 23:46:04.235654+00
webchat_613c6c9b-2fe1-481c-8ea7-a1ceb12b7b5a	{"registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "last_interaction_time": 1753302898.023806, "registros_vermifugacao": [], "conversational_mode_active": true}	2025-07-23 20:34:58.042416+00
webchat_26bc05bc-b70f-407e-b7b7-fa6e0477b44f	{"localizacao": {"pais": "BR", "cidade": "Santo Antônio De Jesus"}, "nome_completo": "Cristian", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1753196448.923557, "registros_vermifugacao": [], "awaiting_weather_location": false, "awaiting_weather_follow_up_choice": true}	2025-07-22 15:00:49.336742+00
webchat_4f2cffd9-a376-4f41-bfc2-838794e15da9	{"nome_completo": "Oi", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1753355863.663201, "registros_vermifugacao": []}	2025-07-24 11:17:43.708415+00
webchat_af0477f3-1ac5-43ef-9358-dca07573c46c	{"localizacao": {"pais": "BR", "cidade": "Jequié"}, "nome_completo": "Oi", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "last_interaction_time": 1753232821.371473, "registros_vermifugacao": [], "awaiting_weather_location": false, "awaiting_weather_follow_up_choice": true}	2025-07-23 01:07:01.699722+00
557391330870@s.whatsapp.net	{"nome_completo": "Vinicius", "registros_animais": [], "registros_estoque": [], "registros_vacinacao": [], "simulacoes_passadas": [], "awaiting_initial_name": false, "last_interaction_time": 1753366750.468358, "registros_vermifugacao": [], "conversational_mode_active": true}	2025-07-24 14:19:10.487236+00
\.


--
-- Data for Name: tb_django_admin_log; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: tb_django_content_type; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_django_content_type (id, app_label, model) FROM stdin;
\.


--
-- Data for Name: tb_django_session; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: tb_intencoes; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_intencoes (id, nome_intencao, descricao) FROM stdin;
\.


--
-- Data for Name: tb_interacoes; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_interacoes (id, agricultor_id, mensagem_usuario, resposta_chatbot, entidades, "timestamp") FROM stdin;
\.


--
-- Data for Name: tb_interacoes_intencoes; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_interacoes_intencoes (interacao_id, intencao_id) FROM stdin;
\.


--
-- Data for Name: tb_movimentacoes_estoque; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_movimentacoes_estoque (id, produto_id, tipo_movimentacao, quantidade, data_movimentacao, observacao) FROM stdin;
\.


--
-- Data for Name: tb_organizacoes; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_organizacoes (id, nome, cnpj, data_criacao) FROM stdin;
1	Campo Inteligente	12.345.678/0001-99	2025-07-15 23:49:03.441819+00
\.


--
-- Data for Name: tb_produtos_estoque; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_produtos_estoque (id, agricultor_id, nome_produto, tipo_produto, unidade_medida, saldo_atual) FROM stdin;
\.


--
-- Data for Name: tb_safras; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_safras (id, agricultor_id, cultura, ano_safra, area_plantada_ha, produtividade, unidade_medida) FROM stdin;
\.


--
-- Data for Name: tb_usuarios; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_usuarios (id, organizacao_id, nome, whatsapp_id, latitude, longitude, cidade, estado, data_cadastro, ultima_atividade, ativo) FROM stdin;
2	1	Usuário 1 (Lucas)	5573988000001	\N	\N	Jequié	BA	2025-07-20 10:00:00+00	\N	S
3	1	Usuário 2 (Ana)	5573988000002	\N	\N	Jitaúna	BA	2025-07-21 11:30:00+00	\N	S
4	1	Usuário 3 (Ricardo)	5573988000003	\N	\N	Ipiaú	BA	2025-06-15 09:00:00+00	\N	N
5	1	Usuário 4 (Mariana)	5573988000004	\N	\N	Jequié	BA	2025-05-10 14:00:00+00	\N	S
6	1	Usuário 5 (Bruno)	5573988000005	\N	\N	Jaguaquara	BA	2025-04-01 16:45:00+00	\N	S
7	1	Usuário 6 (Camila)	5573988000006	\N	\N	Itagi	BA	2025-03-25 08:20:00+00	\N	S
8	1	Usuário 7 (Fernando)	5573988000007	\N	\N	Apuarema	BA	2025-02-18 17:00:00+00	\N	N
9	1	Usuário 8 (Patrícia)	5573988000008	\N	\N	Manoel Vitorino	BA	2025-01-30 12:00:00+00	\N	S
10	1	Usuário 9 (Daniel)	5573988000009	\N	\N	Jequié	BA	2024-12-22 13:10:00+00	\N	S
11	1	Usuário 10 (Gabriela)	5573988000010	\N	\N	Lafaiete Coutinho	BA	2024-11-05 15:00:00+00	\N	S
\.


--
-- Data for Name: tb_versoes_schema; Type: TABLE DATA; Schema: public; Owner: campo_user
--

COPY public.tb_versoes_schema (id, data_hora, usuario, tipo_operacao, tabelas_afetadas, descricao) FROM stdin;
1	2025-07-16 18:59:07.138424+00	marcosmorais	CREATE	tb_organizacoes, tb_administradores, tb_usuarios, tb_safras, tb_produtos_estoque, tb_movimentacoes_estoque, tb_interacoes, tb_intencoes, tb_interacoes_intencoes, tb_conversation_contexts, tb_versoes_schema	Criação inicial do schema do sistema incluindo tabelas principais de organização, usuários, interações, estoque e controle de versão.
\.


--
-- Name: tb_administradores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_administradores_id_seq', 6, true);


--
-- Name: tb_auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_auth_group_id_seq', 1, false);


--
-- Name: tb_auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_auth_group_permissions_id_seq', 1, false);


--
-- Name: tb_auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_auth_permission_id_seq', 1, false);


--
-- Name: tb_auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_auth_user_groups_id_seq', 1, false);


--
-- Name: tb_auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_auth_user_id_seq', 1, false);


--
-- Name: tb_auth_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_auth_user_permissions_id_seq', 1, false);


--
-- Name: tb_django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_django_admin_log_id_seq', 1, false);


--
-- Name: tb_django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_django_content_type_id_seq', 1, false);


--
-- Name: tb_intencoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_intencoes_id_seq', 1, false);


--
-- Name: tb_interacoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_interacoes_id_seq', 1, false);


--
-- Name: tb_movimentacoes_estoque_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_movimentacoes_estoque_id_seq', 1, false);


--
-- Name: tb_organizacoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_organizacoes_id_seq', 1, true);


--
-- Name: tb_produtos_estoque_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_produtos_estoque_id_seq', 1, false);


--
-- Name: tb_safras_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_safras_id_seq', 1, false);


--
-- Name: tb_usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_usuarios_id_seq', 11, true);


--
-- Name: tb_versoes_schema_id_seq; Type: SEQUENCE SET; Schema: public; Owner: campo_user
--

SELECT pg_catalog.setval('public.tb_versoes_schema_id_seq', 1, true);


--
-- Name: tb_administradores tb_administradores_email_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_administradores
    ADD CONSTRAINT tb_administradores_email_key UNIQUE (email);


--
-- Name: tb_administradores tb_administradores_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_administradores
    ADD CONSTRAINT tb_administradores_pkey PRIMARY KEY (id);


--
-- Name: tb_auth_group tb_auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_group
    ADD CONSTRAINT tb_auth_group_name_key UNIQUE (name);


--
-- Name: tb_auth_group_permissions tb_auth_group_permissions_group_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_group_permissions
    ADD CONSTRAINT tb_auth_group_permissions_group_id_permission_id_key UNIQUE (group_id, permission_id);


--
-- Name: tb_auth_group_permissions tb_auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_group_permissions
    ADD CONSTRAINT tb_auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: tb_auth_group tb_auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_group
    ADD CONSTRAINT tb_auth_group_pkey PRIMARY KEY (id);


--
-- Name: tb_auth_permission tb_auth_permission_content_type_id_codename_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_permission
    ADD CONSTRAINT tb_auth_permission_content_type_id_codename_key UNIQUE (content_type_id, codename);


--
-- Name: tb_auth_permission tb_auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_permission
    ADD CONSTRAINT tb_auth_permission_pkey PRIMARY KEY (id);


--
-- Name: tb_auth_user_groups tb_auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user_groups
    ADD CONSTRAINT tb_auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: tb_auth_user_groups tb_auth_user_groups_user_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user_groups
    ADD CONSTRAINT tb_auth_user_groups_user_id_group_id_key UNIQUE (user_id, group_id);


--
-- Name: tb_auth_user_permissions tb_auth_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user_permissions
    ADD CONSTRAINT tb_auth_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: tb_auth_user_permissions tb_auth_user_permissions_user_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user_permissions
    ADD CONSTRAINT tb_auth_user_permissions_user_id_permission_id_key UNIQUE (user_id, permission_id);


--
-- Name: tb_auth_user tb_auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user
    ADD CONSTRAINT tb_auth_user_pkey PRIMARY KEY (id);


--
-- Name: tb_auth_user tb_auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user
    ADD CONSTRAINT tb_auth_user_username_key UNIQUE (username);


--
-- Name: tb_conversation_contexts tb_conversation_contexts_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_conversation_contexts
    ADD CONSTRAINT tb_conversation_contexts_pkey PRIMARY KEY (whatsapp_id);


--
-- Name: tb_django_admin_log tb_django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_django_admin_log
    ADD CONSTRAINT tb_django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: tb_django_content_type tb_django_content_type_app_label_model_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_django_content_type
    ADD CONSTRAINT tb_django_content_type_app_label_model_key UNIQUE (app_label, model);


--
-- Name: tb_django_content_type tb_django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_django_content_type
    ADD CONSTRAINT tb_django_content_type_pkey PRIMARY KEY (id);


--
-- Name: tb_django_session tb_django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_django_session
    ADD CONSTRAINT tb_django_session_pkey PRIMARY KEY (session_key);


--
-- Name: tb_intencoes tb_intencoes_nome_intencao_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_intencoes
    ADD CONSTRAINT tb_intencoes_nome_intencao_key UNIQUE (nome_intencao);


--
-- Name: tb_intencoes tb_intencoes_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_intencoes
    ADD CONSTRAINT tb_intencoes_pkey PRIMARY KEY (id);


--
-- Name: tb_interacoes_intencoes tb_interacoes_intencoes_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_interacoes_intencoes
    ADD CONSTRAINT tb_interacoes_intencoes_pkey PRIMARY KEY (interacao_id, intencao_id);


--
-- Name: tb_interacoes tb_interacoes_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_interacoes
    ADD CONSTRAINT tb_interacoes_pkey PRIMARY KEY (id);


--
-- Name: tb_movimentacoes_estoque tb_movimentacoes_estoque_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_movimentacoes_estoque
    ADD CONSTRAINT tb_movimentacoes_estoque_pkey PRIMARY KEY (id);


--
-- Name: tb_organizacoes tb_organizacoes_cnpj_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_organizacoes
    ADD CONSTRAINT tb_organizacoes_cnpj_key UNIQUE (cnpj);


--
-- Name: tb_organizacoes tb_organizacoes_nome_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_organizacoes
    ADD CONSTRAINT tb_organizacoes_nome_key UNIQUE (nome);


--
-- Name: tb_organizacoes tb_organizacoes_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_organizacoes
    ADD CONSTRAINT tb_organizacoes_pkey PRIMARY KEY (id);


--
-- Name: tb_produtos_estoque tb_produtos_estoque_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_produtos_estoque
    ADD CONSTRAINT tb_produtos_estoque_pkey PRIMARY KEY (id);


--
-- Name: tb_safras tb_safras_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_safras
    ADD CONSTRAINT tb_safras_pkey PRIMARY KEY (id);


--
-- Name: tb_usuarios tb_usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_usuarios
    ADD CONSTRAINT tb_usuarios_pkey PRIMARY KEY (id);


--
-- Name: tb_usuarios tb_usuarios_whatsapp_id_key; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_usuarios
    ADD CONSTRAINT tb_usuarios_whatsapp_id_key UNIQUE (whatsapp_id);


--
-- Name: tb_versoes_schema tb_versoes_schema_pkey; Type: CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_versoes_schema
    ADD CONSTRAINT tb_versoes_schema_pkey PRIMARY KEY (id);


--
-- Name: idx_permission_codename; Type: INDEX; Schema: public; Owner: campo_user
--

CREATE INDEX idx_permission_codename ON public.tb_auth_permission USING btree (codename);


--
-- Name: idx_session_expire_date; Type: INDEX; Schema: public; Owner: campo_user
--

CREATE INDEX idx_session_expire_date ON public.tb_django_session USING btree (expire_date);


--
-- Name: idx_user_username; Type: INDEX; Schema: public; Owner: campo_user
--

CREATE INDEX idx_user_username ON public.tb_auth_user USING btree (username);


--
-- Name: tb_administradores fk_admin_org; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_administradores
    ADD CONSTRAINT fk_admin_org FOREIGN KEY (organizacao_id) REFERENCES public.tb_organizacoes(id) ON DELETE CASCADE;


--
-- Name: tb_django_admin_log fk_adminlog_content_type; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_django_admin_log
    ADD CONSTRAINT fk_adminlog_content_type FOREIGN KEY (content_type_id) REFERENCES public.tb_django_content_type(id) ON DELETE SET NULL;


--
-- Name: tb_django_admin_log fk_adminlog_user; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_django_admin_log
    ADD CONSTRAINT fk_adminlog_user FOREIGN KEY (user_id) REFERENCES public.tb_auth_user(id) ON DELETE CASCADE;


--
-- Name: tb_auth_group_permissions fk_group_perm_group; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_group_permissions
    ADD CONSTRAINT fk_group_perm_group FOREIGN KEY (group_id) REFERENCES public.tb_auth_group(id) ON DELETE CASCADE;


--
-- Name: tb_auth_group_permissions fk_group_perm_permission; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_group_permissions
    ADD CONSTRAINT fk_group_perm_permission FOREIGN KEY (permission_id) REFERENCES public.tb_auth_permission(id) ON DELETE CASCADE;


--
-- Name: tb_interacoes_intencoes fk_intencao; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_interacoes_intencoes
    ADD CONSTRAINT fk_intencao FOREIGN KEY (intencao_id) REFERENCES public.tb_intencoes(id) ON DELETE CASCADE;


--
-- Name: tb_interacoes_intencoes fk_interacao; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_interacoes_intencoes
    ADD CONSTRAINT fk_interacao FOREIGN KEY (interacao_id) REFERENCES public.tb_interacoes(id) ON DELETE CASCADE;


--
-- Name: tb_interacoes fk_interacao_agricultor; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_interacoes
    ADD CONSTRAINT fk_interacao_agricultor FOREIGN KEY (agricultor_id) REFERENCES public.tb_usuarios(id) ON DELETE CASCADE;


--
-- Name: tb_movimentacoes_estoque fk_movimentacao_produto; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_movimentacoes_estoque
    ADD CONSTRAINT fk_movimentacao_produto FOREIGN KEY (produto_id) REFERENCES public.tb_produtos_estoque(id) ON DELETE CASCADE;


--
-- Name: tb_auth_permission fk_permission_content_type; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_permission
    ADD CONSTRAINT fk_permission_content_type FOREIGN KEY (content_type_id) REFERENCES public.tb_django_content_type(id) ON DELETE CASCADE;


--
-- Name: tb_produtos_estoque fk_produto_agricultor; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_produtos_estoque
    ADD CONSTRAINT fk_produto_agricultor FOREIGN KEY (agricultor_id) REFERENCES public.tb_usuarios(id) ON DELETE CASCADE;


--
-- Name: tb_safras fk_safra_agricultor; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_safras
    ADD CONSTRAINT fk_safra_agricultor FOREIGN KEY (agricultor_id) REFERENCES public.tb_usuarios(id) ON DELETE CASCADE;


--
-- Name: tb_auth_user_groups fk_user_group_group; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user_groups
    ADD CONSTRAINT fk_user_group_group FOREIGN KEY (group_id) REFERENCES public.tb_auth_group(id) ON DELETE CASCADE;


--
-- Name: tb_auth_user_groups fk_user_group_user; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user_groups
    ADD CONSTRAINT fk_user_group_user FOREIGN KEY (user_id) REFERENCES public.tb_auth_user(id) ON DELETE CASCADE;


--
-- Name: tb_auth_user_permissions fk_user_perm_permission; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user_permissions
    ADD CONSTRAINT fk_user_perm_permission FOREIGN KEY (permission_id) REFERENCES public.tb_auth_permission(id) ON DELETE CASCADE;


--
-- Name: tb_auth_user_permissions fk_user_perm_user; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_auth_user_permissions
    ADD CONSTRAINT fk_user_perm_user FOREIGN KEY (user_id) REFERENCES public.tb_auth_user(id) ON DELETE CASCADE;


--
-- Name: tb_usuarios fk_usuario_org; Type: FK CONSTRAINT; Schema: public; Owner: campo_user
--

ALTER TABLE ONLY public.tb_usuarios
    ADD CONSTRAINT fk_usuario_org FOREIGN KEY (organizacao_id) REFERENCES public.tb_organizacoes(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

