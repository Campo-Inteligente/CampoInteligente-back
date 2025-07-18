from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import locale
import os
import requests
import openpyxl
from dotenv import load_dotenv
import openai
import re
import json
import psycopg2
import time
import uuid
import traceback

# ==============================================================================
# --- CONFIGURAÇÃO E INICIALIZAÇÃO ---
# ==============================================================================

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except:
    locale.setlocale(locale.LC_TIME, "")

# Configurando as chaves da API e variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
AUTH_KEY = os.getenv("AUTH_KEY")
BOT_NUMBER = os.getenv("BOT_NUMBER")
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://campointeligente.ddns.com.br:21085")
EVOLUTION_INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME", "campointeligente1")

# Configurações do Banco de Dados PostgreSQL
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5432)

# Constantes
CONVERSATION_TIMEOUT_SECONDS = 180

# Inicialização
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)
CORS(app)

# Definições de Cadastro (Perguntas, Ordem, Campos Obrigatórios)
REGISTRATION_QUESTIONS = {
    "nome_completo": "Qual é seu nome completo? �",
    "cpf": "Qual é seu CPF? (apenas números, por favor) 🔢",
    "rg": "Qual é seu RG? (apenas números, se possível) 🆔",
    "data_nascimento": "Qual sua data de nascimento? (dd/mm/aaaa) 🎂",
    "sexo": "Qual seu sexo? (Masculino ♂️, Feminino ♀️ ou Outro) ⚧️",
    "estado_civil": "Qual seu estado civil? Escolha uma opção:\n1. Casado 💍\n2. Solteiro 🧍\n3. Viúvo 💔\n4. Divorciado 💔",
    "telefone_contato": "Qual seu telefone para contato? (Ex: 11987654321, com DDD e sem espaços ou traços) 📱",
    "email": "Você deseja adicionar um endereço de e-mail ao seu cadastro? 📧\n1. Sim\n2. Não",
    "endereco_tipo": "Seu endereço é rural ou urbano? 🏡🏙️\n1. Rural\n2. Urbano",
    "nome_propriedade": "Qual o nome da propriedade (se houver)? 🚜",
    "comunidade_bairro": "Qual a comunidade ou bairro? 🏘️",
    "municipio": "Qual o município? 📍",
    "estado_propriedade": "Qual o estado? (ex: BA, SP, MG...) 🇧🇷",
    "cep": "Qual o CEP? ✉️",
    "ponto_referencia": "Você deseja adicionar um ponto de referência? 🗺️\n1. Sim\n2. Não",
    "dap_caf": "Possui DAP ou CAF? Se sim, informe o número. 📄",
    "tipo_producao": "Sua produção é de que tipo? 🧑‍🌾🏢\n1. Familiar\n2. Empresarial",
    "producao_organica": "Sua produção é orgânica? (Sim ou Não) ✅❌",
    "utiliza_irrigacao": "Utiliza irrigação? (Sim ou Não) 💧",
    "area_total_propriedade": "Qual a área total da propriedade (em hectares)? 📏",
    "area_cultivada": "Qual a área cultivada (em hectares)? 🌱",
    "culturas_produzidas": "Quais culturas você produz? (Você pode informar várias, ex: milho, feijão, mandioca...) 🌽🥔"
}
REGISTRATION_ORDER = [
    "nome_completo", "cpf", "rg", "data_nascimento", "sexo", "estado_civil", "telefone_contato", "email",
    "endereco_tipo", "nome_propriedade", "comunidade_bairro", "municipio", "estado_propriedade", "cep", "ponto_referencia",
    "dap_caf", "tipo_producao", "producao_organica", "utiliza_irrigacao", "area_total_propriedade", "area_cultivada", "culturas_produzidas"
]
MANDATORY_REGISTRATION_FIELDS = [
    "nome_completo", "cpf", "rg", "data_nascimento", "sexo", "estado_civil", "telefone_contato",
    "endereco_tipo", "nome_propriedade", "comunidade_bairro", "municipio", "estado_propriedade", "cep",
    "dap_caf", "tipo_producao", "producao_organica", "utiliza_irrigacao", "area_total_propriedade", "area_cultivada", "culturas_produzidas"
]
EDITABLE_FIELDS_MAP = {
    "nome": "nome_completo", "nome completo": "nome_completo", "cpf": "cpf", "rg": "rg", "data de nascimento": "data_nascimento",
    "sexo": "sexo", "estado civil": "estado_civil", "telefone": "telefone_contato", "email": "email", "endereço tipo": "endereco_tipo",
    "tipo de endereço": "endereco_tipo", "nome da propriedade": "nome_propriedade", "comunidade": "comunidade_bairro",
    "bairro": "comunidade_bairro", "município": "municipio", "estado da propriedade": "estado_propriedade", "cep": "cep",
    "ponto de referência": "ponto_referencia", "dap ou caf": "dap_caf", "dap": "dap_caf", "caf": "dap_caf",
    "tipo de produção": "tipo_producao", "produção orgânica": "producao_organica", "irrigação": "utiliza_irrigacao",
    "area total": "area_total_propriedade", "área total": "area_total_propriedade", "area cultivada": "area_cultivada",
    "área cultivada": "area_cultivada", "culturas": "culturas_produzidas", "culturas produzidas": "culturas_produzidas"
}

# ==============================================================================
# --- FUNÇÕES DE BANCO DE DADOS E SERVIÇOS EXTERNOS ---
# ==============================================================================

def get_db_connection():
    try:
        conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, sslmode='prefer')
        return conn
    except psycopg2.Error as e:
        print(f"ERRO DE BANCO DE DADOS: Não foi possível conectar ao PostgreSQL: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tb_conversation_contexts (
                        whatsapp_id VARCHAR(50) PRIMARY KEY,
                        context JSONB,
                        last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
            print("INFO: Tabela 'tb_conversation_contexts' verificada/criada com sucesso.")
        except psycopg2.Error as e:
            print(f"ERRO DE BANCO DE DADOS: Erro ao inicializar o banco de dados: {e}")
        finally:
            conn.close()

def load_conversation_context(whatsapp_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT context FROM tb_conversation_contexts WHERE whatsapp_id = %s;", (whatsapp_id,))
                result = cur.fetchone()
                return result[0] if result else {}
        except psycopg2.Error as e:
            print(f"ERRO DE BANCO DE DADOS: Erro ao carregar contexto para {whatsapp_id}: {e}")
            return {}
        finally:
            conn.close()
    return {}

def save_conversation_context(whatsapp_id, context):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                context_json = json.dumps(context)
                cur.execute("""
                    INSERT INTO tb_conversation_contexts (whatsapp_id, context)
                    VALUES (%s, %s)
                    ON CONFLICT (whatsapp_id) DO UPDATE
                    SET context = EXCLUDED.context, last_updated = CURRENT_TIMESTAMP;
                """, (whatsapp_id, context_json))
                conn.commit()
        except psycopg2.Error as e:
            print(f"ERRO DE BANCO DE DADOS: Erro ao salvar contexto para {whatsapp_id}: {e}")
        finally:
            conn.close()

def send_whatsapp_message(numero, mensagem):
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
    payload = {"number": numero, "textMessage": {"text": mensagem}}
    headers = {"Content-Type": "application/json", "apikey": AUTH_KEY}
    try:
        resposta = requests.post(url, json=payload, headers=headers, timeout=10)
        resposta.raise_for_status()
        print(f"INFO: Mensagem enviada com sucesso para {numero}.")
    except requests.RequestException as e:
        print(f"ERRO DE API: Falha ao enviar mensagem para {numero}. Erro: {e}")

def send_typing_indicator(numero):
    url = f"{EVOLUTION_API_URL}/chat/sendPresence/{EVOLUTION_INSTANCE_NAME}"
    payload = {"number": numero, "presence": "composing"}
    headers = {"Content-Type": "application/json", "apikey": AUTH_KEY}
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
        time.sleep(2)
    except requests.RequestException as e:
        print(f"ERRO DE API: Falha ao enviar indicador de digitação: {e}")

def obter_previsao_tempo(cidade, pais):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        d = r.json()
        return {"cidade": cidade, "descricao": d['weather'][0]['description'], "temperatura": d['main']['temp'], "sensacao": d['main']['feels_like'], "umidade": d['main']['humidity'], "vento": d['wind']['speed']}
    except (requests.RequestException, KeyError) as e:
        return {"erro": f"Erro ao obter previsão: {e}"}

def obter_previsao_estendida(cidade, pais):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        d = r.json()
        previsoes_diarias = {}
        for item in d["list"]:
            data = datetime.fromtimestamp(item["dt"], timezone.utc).strftime("%d/%m/%Y")
            if data not in previsoes_diarias:
                previsoes_diarias[data] = {"descricao": item["weather"][0]["description"], "min": item["main"]["temp_min"], "max": item["main"]["temp_max"]}
            else:
                previsoes_diarias[data]["min"] = min(previsoes_diarias[data]["min"], item["main"]["temp_min"])
                previsoes_diarias[data]["max"] = max(previsoes_diarias[data]["max"], item["main"]["temp_max"])
        return {"previsao": [{"data": data, **dados} for data, dados in previsoes_diarias.items()]}
    except (requests.RequestException, KeyError) as e:
        return {"erro": f"Erro ao obter previsão estendida: {e}"}

def obter_localizacao_por_coordenadas(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&accept-language=pt"
    try:
        r = requests.get(url, headers={"User-Agent": "CampoInteligenteApp"}, timeout=10)
        r.raise_for_status()
        d = r.json().get("address", {})
        cidade = d.get("city") or d.get("town") or d.get("village") or d.get("municipality")
        estado = d.get("state")
        pais = d.get("country_code", "br").upper()
        return {"cidade": cidade, "estado": estado, "pais": pais} if cidade else {"erro": "Não foi possível obter uma localização completa."}
    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"erro": f"Erro ao obter localização: {e}"}

# ==============================================================================
# --- FUNÇÕES UTILITÁRIAS E DE LÓGICA ---
# ==============================================================================
def is_user_registered(whatsapp_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                where_clauses = [f"context->>'{field}' IS NOT NULL" for field in MANDATORY_REGISTRATION_FIELDS]
                query = f"SELECT 1 FROM tb_conversation_contexts WHERE whatsapp_id = %s AND {' AND '.join(where_clauses)};"
                cur.execute(query, (whatsapp_id,))
                return cur.fetchone() is not None
        except psycopg2.Error as e:
            print(f"ERRO DE BANCO DE DADOS: Erro ao verificar cadastro: {e}")
            return False
        finally:
            conn.close()
    return False

def get_season(now):
    """Determina a estação do ano para o Hemisfério Sul."""
    doy = now.timetuple().tm_yday
    # Mar 20 / Jun 20 / Sep 22 / Dec 21
    spring_start = datetime(now.year, 9, 22).timetuple().tm_yday
    summer_start = datetime(now.year, 12, 21).timetuple().tm_yday
    autumn_start = datetime(now.year, 3, 20).timetuple().tm_yday
    winter_start = datetime(now.year, 6, 20).timetuple().tm_yday

    if autumn_start <= doy < winter_start:
        return "Outono"
    elif winter_start <= doy < spring_start:
        return "Inverno"
    elif spring_start <= doy < summer_start:
        return "Primavera"
    else: # Summer
        return "Verão"

def is_valid_cpf(cpf): return re.fullmatch(r'\d{11}', re.sub(r'\D', '', cpf)) is not None
def is_valid_rg(rg): return 5 <= len(re.sub(r'[\W_]', '', rg)) <= 15
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False
def is_valid_email(email): return re.fullmatch(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def reset_all_flow_flags(contexto):
    flags = [
        "awaiting_initial_name", "awaiting_continuation_choice", "awaiting_weather_follow_up_choice", 
        "awaiting_menu_return_prompt", "awaiting_weather_location", "awaiting_post_completion_response", 
        "conversational_mode_active", "registration_step", "editing_registration", "awaiting_field_to_edit",
        "current_editing_field", "awaiting_email_choice", "email_choice_made", "awaiting_email_value_input",
        "awaiting_ponto_referencia_choice", "ponto_referencia_choice_made", "awaiting_ponto_referencia_value_input",
        "simulacao_safra_ativa", "etapa_simulacao", "awaiting_safra_finalizacao", "simulacao_sub_fluxo",
        "gerar_relatorio_simulacao_ativo", "gestao_rebanho_ativo", "gestao_rebanho_sub_fluxo",
        "gerar_relatorio_rebanho_ativo", "vacinacao_vermifugacao_ativo", "vacinacao_vermifugacao_opcao",
        "registro_vacinacao_etapa", "consulta_vacinacao_ativa", "awaiting_animal_id_consulta_vac",
        "registro_vermifugacao_etapa", "consulta_vermifugacao_ativa", "awaiting_animal_id_consulta_verm",
        "lembretes_vacinacao_ativa", "awaiting_lembretes_contato", "cadastro_animal_ativo", "registro_animal_etapa",
        "controle_reprodutivo_ativo", "historico_pesagens_ativo", "controle_estoque_ativo", "controle_estoque_sub_fluxo",
        "gerar_relatorio_estoque_ativo", "registro_entrada_estoque_ativo", "registro_entrada_estoque_etapa",
        "registro_saida_estoque_ativo", "registro_saida_estoque_etapa", "consulta_estoque_ativa"
    ]
    for flag in flags:
        if flag in contexto:
            contexto[flag] = False
    
    data_keys = [
        "dados_simulacao", "dados_vacinacao_registro", "dados_vermifugacao_registro", "dados_animal_registro",
        "dados_entrada_estoque_registro", "dados_saida_estoque_registro"
    ]
    for key in data_keys:
        if key in contexto:
            contexto[key] = {}
        
    return contexto

def get_next_registration_question_key(contexto):
    current_question_key = contexto.get("registration_step")
    current_index = REGISTRATION_ORDER.index(current_question_key) if current_question_key in REGISTRATION_ORDER else -1

    if contexto.get("awaiting_email_value_input"): return "email"
    if contexto.get("awaiting_ponto_referencia_value_input"): return "ponto_referencia"

    for i in range(current_index + 1, len(REGISTRATION_ORDER)):
        key = REGISTRATION_ORDER[i]
        if key in contexto and contexto.get(key) not in [None, "", "Não informado"]:
            continue
        if key == "email":
            if not contexto.get("email_choice_made"):
                contexto["awaiting_email_choice"] = True
                return "email_choice"
            elif contexto.get("email_choice_made") == "sim" and not contexto.get("email"):
                contexto["awaiting_email_value_input"] = True
                return "email"
        elif key == "ponto_referencia":
            if not contexto.get("ponto_referencia_choice_made"):
                contexto["awaiting_ponto_referencia_choice"] = True
                return "ponto_referencia_choice"
            elif contexto.get("ponto_referencia_choice_made") == "sim" and not contexto.get("ponto_referencia"):
                contexto["awaiting_ponto_referencia_value_input"] = True
                return "ponto_referencia"
        else:
            return key
    return None

def format_weather_response(cidade, pais):
    clima_atual = obter_previsao_tempo(cidade, pais)
    if "erro" in clima_atual:
        return f"Ops! 😔 Não consegui a previsão para {cidade}. Por favor, verifique o nome da cidade e tente novamente."

    desc_emojis = {
        "céu limpo": "☀️", "poucas nuvens": "🌤️", "nuvens dispersas": "☁️",
        "nuvens quebradas": "☁️", "chuva leve": "🌧️", "chuva moderada": "🌧️",
        "chuva forte": "⛈️", "trovoada": "⚡⛈️", "neve": "🌨️", "névoa": "🌫️",
        "garoa": "🌦️", "chuva e garoa": "🌧️", "tempestade": "🌪️",
        "chuva de granizo": "🧊🌧️", "nublado": "☁️", "overcast clouds": "☁️"
    }
    
    descricao_clima = clima_atual.get('descricao', '').lower()
    emoji = next((emoji for key, emoji in desc_emojis.items() if key in descricao_clima), "🌡️")
    
    resposta = (
        f"Previsão para {clima_atual.get('cidade', cidade).title()}:\n"
        f"{emoji} {descricao_clima.capitalize()}\n"
        f"Temperatura: {clima_atual.get('temperatura', 0):.1f}°C (Sensação: {clima_atual.get('sensacao', 0):.1f}°C)\n"
        f"Umidade: {clima_atual.get('umidade', 0)}%\n\n"
        "Quer outra consulta ou voltar ao menu?"
    )
    return resposta

def simular_safra(dados):
    cultura = dados.get("cultura", "").lower()
    produtividade_base = 3000
    if "soja" in cultura: produtividade_base = 3200
    elif "milho" in cultura: produtividade_base = 6000
    elif "trigo" in cultura: produtividade_base = 2500
    elif "café" in cultura: produtividade_base = 1500
    
    if "argiloso" in dados.get("tipo_solo", "").lower(): produtividade_base *= 1.05
    elif "arenoso" in dados.get("tipo_solo", "").lower(): produtividade_base *= 0.95

    condicoes = dados.get("condicoes_climaticas", "").lower()
    if "chuva moderada" in condicoes or "clima ideal" in condicoes: produtividade_base *= 1.10
    elif "seca" in condicoes: produtividade_base *= 0.70
    elif "excesso de chuva" in condicoes: produtividade_base *= 0.85
    
    return {"produtividade_media": round(produtividade_base)}

def formatar_resultado_simulacao(dados, resultado):
    area = dados.get("area", 0)
    produtividade_media = resultado.get("produtividade_media", 0)
    producao_total_kg = area * produtividade_media
    producao_total_toneladas = producao_total_kg / 1000
    
    return (f"🌾 Simulação de Safra - Resultado ✅\n\n"
            f"Cultura: {dados.get('cultura', 'N/A').capitalize()}\n"
            f"Área: {area} hectares\n"
            f"Solo: {dados.get('tipo_solo', 'N/A').capitalize()}\n"
            f"Clima: {dados.get('condicoes_climaticas', 'N/A').capitalize()}\n\n"
            f"Estimativa de Produção:\n"
            f"-> Produtividade média: {produtividade_media:,.0f} kg/ha\n"
            f"-> Produção total: {producao_total_toneladas:,.1f} toneladas\n\n"
            f"Deseja realizar outra simulação ou finalizar?")

def get_main_menu(participant_number):
    """Função auxiliar para gerar o texto do menu principal, formatado corretamente."""
    cadastro_opcao_texto = "Atualizar meu cadastro" if is_user_registered(participant_number) else "Fazer meu cadastro"
    
    # Construindo a string manualmente para garantir as quebras de linha
    menu_string = "Como posso te ajudar agora?\n\n"
    menu_string += "1. Ver a Previsão do Tempo ☁️\n"
    menu_string += "2. Bater um papo com a Iagro 🤖\n"
    menu_string += "3. Gerenciar meu Estoque 📦\n"
    menu_string += "4. Cuidar do meu Rebanho 🐄\n"
    menu_string += "5. Fazer Simulação de Safra 🌾\n"
    menu_string += f"6. {cadastro_opcao_texto} 📝\n"
    menu_string += "7. Alertas de Pragas e Doenças 🐛\n"
    menu_string += "8. Análise de Mercado 📈\n"
    menu_string += "9. Saber minha Localização 📍\n"
    menu_string += "10. Outras Informações 💡"
    
    return menu_string

# ==============================================================================
# --- CÉREBRO PRINCIPAL DA CONVERSA (CORE LOGIC) ---
# ==============================================================================

def process_message(participant_number, mensagem_bruta, location_message=None, push_name="Usuário"):
    """
    Função central que processa todas as mensagens recebidas.
    Este é o "cérebro" do chatbot. Contém TODA a lógica de conversação.
    Retorna a string de resposta a ser enviada ao usuário.
    """
    contexto = load_conversation_context(participant_number)
    mensagem_recebida = mensagem_bruta.lower().strip()

    # Se o contexto está totalmente vazio, é um usuário novo. Peça o nome.
    if not contexto:
        contexto['awaiting_initial_name'] = True
        save_conversation_context(participant_number, contexto)
        return "Olá! Sou a Iagro, sua assistente virtual para o campo. Para começarmos, como posso te chamar? 😊"

    # Se estivermos aguardando o nome, salve-o.
    if contexto.get('awaiting_initial_name'):
        nome = mensagem_bruta.strip().title()
        contexto['nome_completo'] = nome
        contexto['awaiting_initial_name'] = False
        reset_all_flow_flags(contexto)
        resposta = f"Prazer em te conhecer, {nome}! 👋\n\n{get_main_menu(participant_number)}"
        save_conversation_context(participant_number, contexto)
        return resposta

    nome = contexto.get("nome_completo", push_name)

    for key in ["simulacoes_passadas", "registros_estoque", "registros_animais", "registros_vacinacao", "registros_vermifugacao"]:
        if key not in contexto:
            contexto[key] = []

    current_time = datetime.now().timestamp()
    if contexto.get("last_interaction_time") and (current_time - contexto.get("last_interaction_time")) > CONVERSATION_TIMEOUT_SECONDS:
        dados_persistentes = {k: v for k, v in contexto.items() if k in REGISTRATION_ORDER or k.startswith("registros_")}
        contexto.clear()
        contexto.update(dados_persistentes)
        reset_all_flow_flags(contexto)
        nome_usuario = contexto.get("nome_completo", "Usuário")
        resposta = (f"Olá, {nome_usuario}! Que bom te ver de novo. 😊\n"
                    f"Para facilitar, vamos voltar ao menu principal.\n\n"
                    f"{get_main_menu(participant_number)}")
        contexto["last_interaction_time"] = current_time
        save_conversation_context(participant_number, contexto)
        return resposta

    contexto["last_interaction_time"] = current_time
    
    if location_message:
        lat = location_message.get('degreesLatitude')
        lon = location_message.get('degreesLongitude')
        if lat is not None and lon is not None:
            local = obter_localizacao_por_coordenadas(lat, lon)
            if "erro" in local:
                return "Ops! 😔 Não consegui identificar sua localização a partir das coordenadas enviadas."
            
            cidade, estado, pais = local.get("cidade"), local.get("estado"), local.get("pais")
            contexto["localizacao"] = {"cidade": cidade, "estado": estado, "pais": pais}
            if not contexto.get("municipio"): contexto["municipio"] = cidade
            if not contexto.get("estado_propriedade"): contexto["estado_propriedade"] = estado
            
            reset_all_flow_flags(contexto)
            contexto["awaiting_weather_follow_up_choice"] = True
            resposta = format_weather_response(cidade, pais)
            save_conversation_context(participant_number, contexto)
            return resposta
        else:
            return f"Não consegui processar a localização enviada, {nome}. Por favor, tente novamente."

    if not mensagem_recebida:
        return None

    if any(cmd in mensagem_recebida for cmd in ["sair", "finalizar", "encerrar"]):
        reset_all_flow_flags(contexto)
        resposta = f"Entendido, {nome}. Estou finalizando nossa conversa. Até a próxima! 👋"
        save_conversation_context(participant_number, contexto)
        return resposta

    # --- INÍCIO DA MÁQUINA DE ESTADOS ---
    
    if contexto.get("conversational_mode_active"):
        if any(cmd in mensagem_recebida for cmd in ["menu", "voltar", "sair"]):
             reset_all_flow_flags(contexto)
             resposta = f"Ok, {nome}! Saindo do modo de conversa.\n\n{get_main_menu(participant_number)}"
        else:
            localizacao = contexto.get("localizacao", {})
            clima_info = "Não disponível"
            if localizacao.get("cidade"):
                clima_atual = obter_previsao_tempo(localizacao["cidade"], localizacao.get("pais", "BR"))
                if "erro" not in clima_atual:
                    clima_info = f"Temperatura: {clima_atual.get('temperatura', 0):.1f}°C, Descrição: {clima_atual.get('descricao', '')}"
            
            estacao_do_ano = get_season(datetime.now())

            prompt_para_ia = (
                f"Você é a Iagro, uma Engenheira Agrônoma e Veterinária Virtual. Sua missão é ser uma especialista completa para o produtor rural. Use emojis para deixar a conversa amigável! 🌱🚜☀️\n\n"
                f"INFORMAÇÕES DO USUÁRIO:\n"
                f"- Nome: {nome}\n"
                f"- Localização: {localizacao.get('cidade', 'Não informada')}\n"
                f"- Clima Atual: {clima_info}\n"
                f"- Estação do Ano: {estacao_do_ano}\n"
                f"- Culturas Principais: {contexto.get('culturas_produzidas', 'Não informada')}\n\n"
                f"SUAS ESPECIALIDADES:\n"
                f"1.  **Doenças de Animais:** Você pode diagnosticar doenças comuns em rebanhos (bovinos, caprinos, etc.), como mastite, febre aftosa, etc. Forneça sintomas, causas e, o mais importante, RECOMENDAÇÕES DE TRATAMENTO (medicamentos, dosagens, métodos de aplicação) e PREVENÇÃO. Sempre sugira consultar um veterinário local para confirmação.\n"
                f"2.  **Pragas e Doenças de Lavouras:** Identifique pragas (ex: lagartas, pulgões) e doenças (ex: ferrugem, oídio) em plantas. Descreva os danos e ofereça soluções de MANEJO INTEGRADO, incluindo controle biológico, cultural e, se necessário, químico (sugerindo princípios ativos de defensivos).\n"
                f"3.  **Recomendações de Plantio:** Com base na estação do ano ({estacao_do_ano}), no clima e na localização, sugira as melhores culturas para plantar.\n\n"
                f"INSTRUÇÕES DE DIÁLOGO:\n"
                f"- Seja MUITO DIRETA E CONCISA. Evite parágrafos longos. Use frases curtas.\n"
                f"- Se for uma saudação ('boa noite'), responda de forma curta e amigável.\n"
                f"- Se a pergunta for complexa (diagnóstico), faça perguntas adicionais para entender melhor os sintomas antes de dar uma resposta final.\n"
                f"- Lembre sempre que o usuário pode digitar 'menu' para voltar.\n\n"
                f"PERGUNTA DO USUÁRIO:\n'{mensagem_bruta}'"
            )
            try:
                response = openai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt_para_ia}], max_tokens=300)
                resposta = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"ERRO OPENAI: {e}")
                resposta = "Ops! 🤖 Meus circuitos estão um pouco sobrecarregados agora. Tente de novo em um instante."
        save_conversation_context(participant_number, contexto)
        return resposta

    elif contexto.get("awaiting_weather_location"):
        cidade = mensagem_bruta.strip().title()
        reset_all_flow_flags(contexto)
        contexto["awaiting_weather_follow_up_choice"] = True
        contexto["localizacao"] = {"cidade": cidade, "pais": "BR"}
        resposta = format_weather_response(cidade, "BR")
        save_conversation_context(participant_number, contexto)
        return resposta

    elif contexto.get("awaiting_weather_follow_up_choice"):
        if any(word in mensagem_recebida for word in ["outra", "nova", "sim", "1"]):
            reset_all_flow_flags(contexto)
            contexto["awaiting_weather_location"] = True
            resposta = f"Para qual cidade você gostaria da previsão, {nome}? 📍"
        else:
            reset_all_flow_flags(contexto)
            resposta = f"Ok, {nome}! Voltando ao menu principal.\n\n{get_main_menu(participant_number)}"
        save_conversation_context(participant_number, contexto)
        return resposta
    
    # Placeholder for stock management flow
    elif contexto.get("controle_estoque_ativo"):
        if "voltar" in mensagem_recebida or "menu" in mensagem_recebida:
            reset_all_flow_flags(contexto)
            return f"Ok, {nome}! Voltando ao menu principal.\n\n{get_main_menu(participant_number)}"
        # Detailed logic for stock management would go here
        return "Função de Estoque em desenvolvimento. Digite 'menu' para voltar."

    # Placeholder for herd management flow
    elif contexto.get("gestao_rebanho_ativo"):
        if "voltar" in mensagem_recebida or "menu" in mensagem_recebida:
            reset_all_flow_flags(contexto)
            return f"Ok, {nome}! Voltando ao menu principal.\n\n{get_main_menu(participant_number)}"
        # Detailed logic for herd management would go here
        return "Função de Gestão de Rebanho em desenvolvimento. Digite 'menu' para voltar."

    # Placeholder for crop simulation flow
    elif contexto.get("simulacao_safra_ativa"):
        if "voltar" in mensagem_recebida or "menu" in mensagem_recebida:
            reset_all_flow_flags(contexto)
            return f"Ok, {nome}! Voltando ao menu principal.\n\n{get_main_menu(participant_number)}"
        
        etapa = contexto.get("etapa_simulacao")
        if etapa == "cultura":
            contexto["dados_simulacao"] = {"cultura": mensagem_bruta.strip()}
            contexto["etapa_simulacao"] = "area"
            resposta = "Entendido. E qual a área a ser plantada (em hectares)?"
        # ... other simulation steps would go here
        else:
            resposta = "Função de Simulação de Safra em desenvolvimento. Digite 'menu' para voltar."
        save_conversation_context(participant_number, contexto)
        return resposta


    elif any(s in mensagem_recebida for s in ["1", "clima", "tempo"]):
        reset_all_flow_flags(contexto)
        localizacao = contexto.get("localizacao")
        if localizacao and localizacao.get("cidade"):
            contexto["awaiting_weather_follow_up_choice"] = True
            resposta = format_weather_response(localizacao['cidade'], localizacao.get('pais', 'BR'))
        else:
            contexto["awaiting_weather_location"] = True
            resposta = f"Para qual cidade você gostaria da previsão, {nome}? 📍"
        save_conversation_context(participant_number, contexto)
        return resposta

    elif any(s in mensagem_recebida for s in ["2", "papo", "conversar"]):
        reset_all_flow_flags(contexto)
        contexto["conversational_mode_active"] = True
        resposta = (f"Que bom conversar com você, {nome}! 😊\n"
                    "Pode me perguntar qualquer coisa sobre sua lavoura, o clima ou qualquer outra dúvida agrícola. "
                    "Para voltar ao menu, é só digitar 'menu'.")
        save_conversation_context(participant_number, contexto)
        return resposta

    elif any(s in mensagem_recebida for s in ["3", "estoque"]):
        reset_all_flow_flags(contexto)
        contexto["controle_estoque_ativo"] = True
        resposta = "Ok, vamos gerenciar seu estoque. O que você gostaria de fazer?\n\n1. Registrar Entrada\n2. Registrar Saída\n3. Consultar Estoque"
        save_conversation_context(participant_number, contexto)
        return resposta

    elif any(s in mensagem_recebida for s in ["4", "rebanho"]):
        reset_all_flow_flags(contexto)
        contexto["gestao_rebanho_ativo"] = True
        resposta = "Certo, vamos cuidar do rebanho. Qual a sua necessidade?\n\n1. Cadastrar Animal\n2. Registrar Vacinação\n3. Consultar Histórico"
        save_conversation_context(participant_number, contexto)
        return resposta

    elif any(s in mensagem_recebida for s in ["5", "safra", "simulação"]):
        reset_all_flow_flags(contexto)
        contexto["simulacao_safra_ativa"] = True
        contexto["etapa_simulacao"] = "cultura" 
        resposta = "Vamos fazer uma simulação de safra! 🌾\n\nPrimeiro, qual a cultura que você quer simular? (ex: Soja, Milho)"
        save_conversation_context(participant_number, contexto)
        return resposta

    elif any(s in mensagem_recebida for s in ["6", "cadastro"]):
        reset_all_flow_flags(contexto)
        if is_user_registered(participant_number):
            contexto["editing_registration"] = True
            contexto["awaiting_field_to_edit"] = True
            resposta = "Função de edição de cadastro ainda em implementação."
        else:
            contexto["registration_step"] = REGISTRATION_ORDER[0]
            resposta = f"Vamos iniciar seu cadastro! {REGISTRATION_QUESTIONS[contexto['registration_step']]}"
        save_conversation_context(participant_number, contexto)
        return resposta

    else:
        # Se chegamos aqui, é porque nenhuma opção de menu ou fluxo foi ativada.
        # A saudação inicial já foi tratada no começo.
        resposta = f"Desculpe, {nome}, não entendi. 🤔\n\n{get_main_menu(participant_number)}"
        save_conversation_context(participant_number, contexto)
        return resposta

# ==============================================================================
# --- ROTAS DA APLICAÇÃO FLASK (ADAPTADORES) ---
# ==============================================================================

@app.route("/", methods=["GET"])
def home():
    return "API Campo Inteligente (Refatorada e Otimizada) está online!"

@app.route("/webhook", methods=["POST"])
def webhook_route():
    try:
        data = request.json
        print(f"--- Webhook recebido ---\n{json.dumps(data, indent=2)}")

        if data.get('event') != 'messages.upsert' or not isinstance(data.get('data'), dict):
            return jsonify({"status": "Evento ignorado"}), 200

        msg_data = data['data']
        key = msg_data.get('key', {})
        if key.get('fromMe', False):
            return jsonify({"status": "Mensagem do bot ignorada"}), 200

        numero_destino = key.get('remoteJid')
        if not numero_destino:
            return jsonify({"status": "erro", "mensagem": "Número não fornecido."}), 400

        message_content = msg_data.get('message', {})
        mensagem_bruta = message_content.get('conversation') or message_content.get('extendedTextMessage', {}).get('text', '')
        location_message = message_content.get('locationMessage')
        
        if numero_destino.endswith('@g.us'):
            participant_number = key.get('participant', numero_destino)
            push_name = msg_data.get('pushName', 'Membro do Grupo')
            bot_jid = f"{BOT_NUMBER}@s.whatsapp.net"
            mentioned_jids = message_content.get('extendedTextMessage', {}).get('contextInfo', {}).get('mentionedJid', [])
            if bot_jid not in mentioned_jids and '@iagro' not in mensagem_bruta.lower():
                return jsonify({"status": "ignorado, sem menção em grupo"}), 200
            mensagem_bruta = re.sub(r'@\d+|@iagro', '', mensagem_bruta, flags=re.IGNORECASE).strip() or "menu"
        else:
            participant_number = numero_destino
            push_name = msg_data.get('pushName', 'Usuário')

        if not mensagem_bruta and not location_message:
            return jsonify({"status": "ignorado, mensagem vazia"}), 200

        send_typing_indicator(numero_destino)
        resposta_bot = process_message(participant_number, mensagem_bruta, location_message, push_name)

        if resposta_bot:
            send_whatsapp_message(numero_destino, resposta_bot)

        return jsonify({"status": "sucesso"}), 200

    except Exception as e:
        print(f"ERRO CRÍTICO NO WEBHOOK: {e}\n{traceback.format_exc()}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route("/webchat", methods=["POST"])
def webchat_route():
    try:
        data = request.json
        session_id = data.get("session_id") or str(uuid.uuid4())
        mensagem_recebida = data.get("mensagem", "").strip()

        if not mensagem_recebida:
            return jsonify({"status": "erro", "mensagem": "Mensagem vazia."}), 400

        participant_number = f"webchat_{session_id}"
        resposta_bot = process_message(participant_number, mensagem_recebida)
        
        # REMOVIDA a substituição por <br>. A API agora envia \n.
        # O frontend DEVE ser ajustado para renderizar as quebras de linha.
        # Adicione a propriedade CSS: white-space: pre-wrap; ao elemento da mensagem.
        return jsonify({"resposta": resposta_bot, "session_id": session_id})

    except Exception as e:
        print(f"ERRO CRÍTICO NO WEBHOOK: {e}\n{traceback.format_exc()}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
