from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import locale
import os
import requests
import openpyxl # Mantido, pois a função salvar_planilha existe
from dotenv import load_dotenv
import openai
import re
import json
import psycopg2
import time

# Carregando variáveis de ambiente
load_dotenv()

try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except:
    locale.setlocale(locale.LC_TIME, "")

# Configurando as chaves da API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
AUTH_KEY = os.getenv("AUTH_KEY")
EVOLUTION_API_URL = "https://1f27-45-169-217-33.ngrok-free.app"

# Configurações do Banco de Dados PostgreSQL
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5432)

# Tempo de inatividade da conversa em segundos (ex: 3 minutos)
CONVERSATION_TIMEOUT_SECONDS = 180

# Inicializando a API do OpenAI
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)

# Dicionário para armazenar o contexto da conversa por número de telefone (em memória, para demonstração)
# Para persistência real, usaremos o banco de dados.
conversa_contextos = {}

# Definição das perguntas de cadastro e as chaves correspondentes no contexto
REGISTRATION_QUESTIONS = {
    "nome_completo": "Qual é seu nome completo? 👤",
    "cpf": "Qual é seu CPF? (apenas números, por favor) 🔢",
    "rg": "Qual é seu RG? (apenas números, se possível) 🆔",
    "data_nascimento": "Qual sua data de nascimento? (dd/mm/aaaa) 🎂",
    "sexo": "Qual seu sexo? (Masculino ♂️, Feminino ♀️ ou Outro) �",
    "estado_civil": "Qual seu estado civil? Escolha uma opção:\n1. Casado 💍\n2. Solteiro 🧍\n3. Viúvo �\n4. Divorciado 💔",
    "telefone_contato": "Qual seu telefone para contato? (Ex: 11987654321, com DDD e sem espaços ou traços) 📱",
    "email": "Você deseja adicionar um endereço de e-mail ao seu cadastro? 📧\n1. Sim\n2. Não",
    "endereco_tipo": "Seu endereço é rural ou urbano? 🏡🏙️",
    "nome_propriedade": "Qual o nome da propriedade (se houver)? 🚜",
    "comunidade_bairro": "Qual a comunidade ou bairro? 🏘️",
    "municipio": "Qual o município? 📍",
    "estado_propriedade": "Qual o estado? (ex: BA, SP, MG...) 🇧🇷",
    "cep": "Qual o CEP? ✉️",
    "ponto_referencia": "Você deseja adicionar um ponto de referência? 🗺️\n1. Sim\n2. Não",
    "dap_caf": "Possui DAP ou CAF? Se sim, informe o número. 📄",
    "tipo_producao": "Sua produção é de que tipo? (Familiar ou Empresarial) 🧑‍🌾🏢",
    "producao_organica": "Sua produção é orgânica? (Sim ou Não) ✅❌",
    "utiliza_irrigacao": "Utiliza irrigação? (Sim ou Não) 💧",
    "area_total_propriedade": "Qual a área total da propriedade (em hectares)? 📏",
    "area_cultivada": "Qual a área cultivada (em hectares)? 🌱",
    "culturas_produzidas": "Quais culturas você produz? (Você pode informar várias, ex: milho, feijão, mandioca...) 🌽🥔"
}

# Ordem das perguntas para o fluxo de cadastro
REGISTRATION_ORDER = [
    "nome_completo", "cpf", "rg", "data_nascimento", "sexo", "estado_civil", "telefone_contato", "email",
    "endereco_tipo", "nome_propriedade", "comunidade_bairro", "municipio", "estado_propriedade", "cep", "ponto_referencia",
    "dap_caf", "tipo_producao", "producao_organica", "utiliza_irrigacao", "area_total_propriedade", "area_cultivada", "culturas_produzidas"
]

# Campos obrigatórios para considerar o usuário cadastrado
MANDATORY_REGISTRATION_FIELDS = [
    "nome_completo", "cpf", "rg", "data_nascimento", "sexo", "estado_civil", "telefone_contato",
    "endereco_tipo", "nome_propriedade", "comunidade_bairro", "municipio", "estado_propriedade", "cep",
    "dap_caf", "tipo_producao", "producao_organica", "utiliza_irrigacao", "area_total_propriedade", "area_cultivada", "culturas_produzidas"
]

# Mapeamento de termos do usuário para chaves de campo para edição
EDITABLE_FIELDS_MAP = {
    "nome": "nome_completo",
    "nome completo": "nome_completo",
    "cpf": "cpf",
    "rg": "rg",
    "data de nascimento": "data_nascimento",
    "sexo": "sexo",
    "estado civil": "estado_civil",
    "telefone": "telefone_contato",
    "email": "email",
    "endereço tipo": "endereco_tipo",
    "tipo de endereço": "endereco_tipo",
    "nome da propriedade": "nome_propriedade",
    "comunidade": "comunidade_bairro",
    "bairro": "comunidade_bairro",
    "município": "municipio",
    "estado da propriedade": "estado_propriedade",
    "cep": "cep",
    "ponto de referência": "ponto_referencia",
    "dap ou caf": "dap_caf",
    "dap": "dap_caf",
    "caf": "caf",
    "tipo de produção": "tipo_producao",
    "produção orgânica": "producao_organica",
    "irrigação": "utiliza_irrigacao",
    "area total": "area_total_propriedade",
    "área total": "area_total_propriedade",
    "area cultivada": "area_cultivada",
    "área cultivada": "area_cultivada",
    "culturas": "culturas_produzidas",
    "culturas produzidas": "culturas_produzidas"
}


# Função para obter conexão com o banco de dados PostgreSQL
def get_db_connection():
    conn = None
    try:
        print(f"DEBUG_DB_CONNECT: Tentando conectar ao PostgreSQL com: Host={DB_HOST}, Port={DB_PORT}, Database={DB_NAME}, User={DB_USER}")
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("DEBUG_DB_CONNECT: Conexão ao PostgreSQL estabelecida com sucesso.")
        return conn
    except psycopg2.Error as e:
        print(f"DEBUG_DB_CONNECT_ERROR: Erro ao conectar ao banco de dados PostgreSQL: {e}")
        return None

# Função para inicializar a tabela de contexto de conversas no banco de dados
def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversation_contexts (
                    phone_number VARCHAR(255) PRIMARY KEY,
                    context JSONB,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            print("DEBUG_DB_INIT: Tabela 'conversation_contexts' verificada/criada com sucesso.")
        except psycopg2.Error as e:
            print(f"DEBUG_DB_INIT_ERROR: Erro ao inicializar o banco de dados: {e}")
        finally:
            if conn:
                conn.close()

# Função para carregar o contexto da conversa do banco de dados
def load_conversation_context(phone_number):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT context FROM conversation_contexts WHERE phone_number = %s;", (phone_number,))
            result = cur.fetchone()
            cur.close()
            if result:
                loaded_context = result[0]
                print(f"DEBUG_DB_LOAD: Contexto carregado do DB para {phone_number}: {loaded_context}")
                return loaded_context
            print(f"DEBUG_DB_LOAD: Nenhum contexto encontrado no DB para {phone_number}. Retornando vazio.")
            return {}
        except psycopg2.Error as e:
            print(f"DEBUG_DB_LOAD_ERROR: Erro ao carregar contexto da conversa do banco de dados para {phone_number}: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    print(f"DEBUG_DB_LOAD_ERROR: Conexão ao DB falhou ao carregar contexto para {phone_number}.")
    return {}

# Função para salvar o contexto da conversa no banco de dados
def save_conversation_context(phone_number, context):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            context_json = json.dumps(context)
            cur.execute("""
                INSERT INTO conversation_contexts (phone_number, context)
                VALUES (%s, %s)
                ON CONFLICT (phone_number) DO UPDATE
                SET context = EXCLUDED.context, last_updated = CURRENT_TIMESTAMP;
            """, (phone_number, context_json))
            conn.commit()
            cur.close()
            print(f"DEBUG_DB_SAVE: Contexto para {phone_number} salvo/atualizado no DB: {context}")
            # time.sleep(0.1)  # Removido para otimização do tempo de resposta
        except psycopg2.Error as e:
            print(f"DEBUG_DB_SAVE_ERROR: Erro ao salvar contexto da conversa no banco de dados para {phone_number}: {e}")
            raise
        finally:
            if conn:
                conn.close()
    else:
        print(f"DEBUG_DB_SAVE_ERROR: Conexão ao DB falhou ao salvar contexto para {phone_number}.")
        raise Exception("Falha na conexão com o banco de dados ao tentar salvar o contexto.")


# Função para obter localização via IP
def obter_localizacao_via_ip():
    try:
        r = requests.get("http://ip-api.com/json/")
        d = r.json()
        if d['status'] == 'success':
            return {
                "pais": d['country'],
                "estado": d['regionName'],
                "cidade": d['city'],
                "ip": d['query']
            }
        return {"erro": "Não foi possível determinar sua localização."}
    except requests.RequestException as e:
        return {"erro": f"Erro de requisição: {e}"}
    except Exception as e:
        return {"erro": f"Erro geral: {e}"}


# Função para obter previsão do tempo
def obter_previsao_tempo(cidade, pais):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url)
        r.raise_for_status()
        d = r.json()
        return {
            "cidade": cidade,
            "descricao": d['weather'][0]['description'],
            "temperatura": d['main']['temp'],
            "sensacao": d['main']['feels_like'],
            "umidade": d['main']['humidity'],
            "vento": d['wind']['speed']
        }
    except requests.RequestException as e:
        return {"erro": f"Erro de requisição: {e}"}
    except KeyError:
        return {"erro": f"Erro: Dados do clima inválidos para {cidade}, {pais}"}
    except Exception as e:
        return {"erro": f"Erro geral: {e}"}


# Função para obter previsão estendida
def obter_previsao_estendida(cidade, pais):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url)
        r.raise_for_status()
        d = r.json()

        previsoes_diarias = {}
        for item in d["list"]:
            data_hora_utc = datetime.utcfromtimestamp(item["dt"])
            data = data_hora_utc.strftime("%d/%m/%Y")
            if data not in previsoes_diarias:
                previsoes_diarias[data] = {
                    "descricao": item["weather"][0]["description"],
                    "min": item["main"]["temp_min"],
                    "max": item["main"]["temp_max"],
                    "data_hora": [data_hora_utc]
                }
            else:
                previsoes_diarias[data]["min"] = min(previsoes_diarias[data]["min"], item["main"]["temp_min"])
                previsoes_diarias[data]["max"] = max(previsoes_diarias[data]["max"], item["main"]["temp_max"])
                previsoes_diarias[data]["data_hora"].append(data_hora_utc)

        previsao_formatada = [{"data": data, **dados} for data, dados in previsoes_diarias.items()]
        return {"previsao": previsao_formatada}
    except requests.RequestException as e:
        return {"erro": f"Erro de requisição: {e}"}
    except KeyError:
        return {"erro": "Erro: Dados de previsão estendida inválidos."}
    except Exception as e:
        return {"erro": f"Erro geral: {e}"}


# Função OBTER LOCALIZAÇÃO por coordenadas
def obter_localizacao_por_coordenadas(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&accept-language=pt"
        r = requests.get(url, headers={"User-Agent": "CampoInteligenteApp"})
        r.raise_for_status()
        d = r.json()
        endereco = d.get("address", {})
        cidade = endereco.get("city") or endereco.get("town") or endereco.get("village") or endereco.get("municipality") or ""
        estado = endereco.get("state") or ""
        pais = endereco.get("country") or ""
        if not cidade or not estado or not pais:
            return {"erro": "Não foi possível obter uma localização completa."}
        return {"cidade": cidade, "estado": estado, "pais": pais}
    except requests.RequestException as e:
        return {"erro": f"Erro de requisição: {e}"}
    except json.JSONDecodeError:
        return {"erro": "Erro: Resposta do servidor em formato inválido."}
    except Exception as e:
        return {"erro": f"Erro geral: {e}"}


# Função auxiliar para enviar mensagem via Evolution API
def send_whatsapp_message(numero, mensagem):
    payload = {
        "number": numero,
        "textMessage": {"text": mensagem}
    }
    headers = {
        "Content-Type": "application/json",
        "apikey": AUTH_KEY
    }
    url = f"http://127.0.0.1:8080/message/sendText/campointeligente"
    try:
        resposta = requests.post(url, json=payload, headers=headers)
        resposta.raise_for_status()
        if resposta.status_code == 200:
            print(f"DEBUG_WHATSAPP: Mensagem enviada com sucesso para {numero}: {mensagem}")
            # time.sleep(0.5) # Removido para otimização
            return resposta.status_code, resposta.json()
        else:
            print(f"DEBUG_WHATSAPP_ERROR: Falha ao enviar mensagem para {numero}. Status: {resposta.status_code}, Erro: {resposta.text}")
            return resposta.status_code, {"erro": resposta.text}
    except requests.RequestException as e:
        print(f"DEBUG_WHATSAPP_ERROR: Erro de requisição ao enviar mensagem para {numero}: {e}" )
        return None, {"erro": f"Erro de requisição ao enviar mensagem: {e}"}
    except Exception as e:
        print(f"DEBUG_WHATSAPP_ERROR: Erro geral ao enviar mensagem para {numero}: {e}")
        return None, {"erro": f"Erro geral ao enviar mensagem: {e}"}

# Nova função para formatar a resposta da previsão do tempo
def format_weather_response(cidade, pais):
    clima_atual = obter_previsao_tempo(cidade, pais)
    clima_estendido = obter_previsao_estendida(cidade, pais)

    if "erro" in clima_atual:
        return f"Ops! 😔 Não consegui a previsão para {cidade}, {pais}. Erro: {clima_atual['erro']}"

    # Mapeamento de descrições do OpenWeather para emojis e termos em português
    desc_emojis = {
        "céu limpo": "☀️ Céu limpo",
        "poucas nuvens": "🌤️ Poucas nuvens",
        "nuvens dispersas": "☁️ Nuvens dispersas",
        "nuvens quebradas": "☁️ Nuvens quebradas",
        "chuva leve": "🌧️ Chuva leve",
        "chuva moderada": "🌧️ Chuva moderada",
        "chuva forte": "⛈️ Chuva forte",
        "trovoada": "⚡⛈️ Trovoada",
        "neve": "🌨️ Neve",
        "névoa": "🌫️ Névoa",
        "garoa": "🌦️ Garoa",
        "chuva e garoa": "🌧️ Chuva e garoa",
        "tempestade": "🌪️ Tempestade",
        "chuva de granizo": "🧊🌧️ Chuva de granizo",
        "nublado": "☁️ Nublado",
        "overcast clouds": "☁️ Nublado"
    }
    
    descricao_clima = clima_atual['descricao'].lower()
    emoji_desc = "❓ Informação não disponível"
    for key, val in desc_emojis.items():
        if key in descricao_clima:
            emoji_desc = val
            break
    
    resposta = (
        f"Previsão para {clima_atual['cidade']}: {emoji_desc}\n"
        f"Agora: {clima_atual['temperatura']:.1f}°C (Sensação: {clima_atual['sensacao']:.1f}°C)\n"
        f"Umidade: {clima_atual['umidade']}%\n"
        f"Vento: {clima_atual['vento']:.1f} m/s\n\n"
    )
    
    if "previsao" in clima_estendido and clima_estendido["previsao"]:
        resposta += "Próximos dias:\n"
        for dia_previsao in clima_estendido["previsao"][:2]:
            desc_ext = dia_previsao['descricao'].lower()
            emoji_ext_desc = "❓ Informação não disponível"
            for key, val in desc_emojis.items():
                if key in desc_ext:
                    emoji_ext_desc = val
                    break
            resposta += (
                f"  {dia_previsao['data']}: {emoji_ext_desc} Min: {dia_previsao['min']:.1f}°C, Max: {dia_previsao['max']:.1f}°C\n"
            )
    
    resposta += "\nQuer outra consulta de clima ou voltar ao menu? (Digite 'outra' ou 'voltar')"
    return resposta


# Função para simular a safra (placeholder)
def simular_safra(dados):
    """
    Realiza a simulação da safra com base nos dados fornecidos.
    Esta é uma função de exemplo e precisa ser implementada com a lógica real.
    """
    cultura = dados.get("cultura", "N/A")
    area = dados.get("area", 0)
    tipo_solo = dados.get("tipo_solo", "N/A")
    condicoes_climaticas = dados.get("condicoes_climaticas", "N/A")
    ciclo_cultura = dados.get("ciclo_cultura", "N/A")

    produtividade_base = 3000
    
    if "soja" in cultura.lower():
        produtividade_base = 3200
    elif "milho" in cultura.lower():
        produtividade_base = 6000
    elif "trigo" in cultura.lower():
        produtividade_base = 2500
    elif "café" in cultura.lower():
        produtividade_base = 1500

    if "argiloso" in tipo_solo.lower():
        produtividade_base *= 1.05
    elif "arenoso" in tipo_solo.lower():
        produtividade_base *= 0.95

    if "chuva moderada" in condicoes_climaticas.lower() or "clima ideal" in condicoes_climaticas.lower():
        produtividade_base *= 1.10
    elif "seca" in condicoes_climaticas.lower():
        produtividade_base *= 0.70
    elif "excesso de chuva" in condicoes_climaticas.lower():
        produtividade_base *= 0.85

    resultado = {
        "produtividade_media": round(produtividade_base),
    }
    return resultado

# Função para formatar o resultado da simulação
def formatar_resultado_simulacao(dados, resultado):
    """
    Formata o resultado da simulação para exibição ao usuário.
    """
    cultura = dados.get("cultura", "Não informado")
    area = dados.get("area", "Não informado")
    tipo_solo = dados.get("tipo_solo", "Não informado")
    condicoes_climaticas = dados.get("condicoes_climaticas", "Não informado")
    ciclo_cultura = dados.get("ciclo_cultura", "Não informado")
    produtividade_media = resultado.get("produtividade_media", 0)
    
    producao_total_kg = area * produtividade_media if isinstance(area, (int, float)) else 0
    producao_total_toneladas = producao_total_kg / 1000

    observacoes = ""
    if "argiloso" in str(tipo_solo).lower() and "chuva moderada" in str(condicoes_climaticas).lower():
        observacoes = " - Com o solo argiloso e clima moderado, a produtividade tende a ser estável. "
    elif "seca" in str(condicoes_climaticas).lower():
        observacoes = " - Condições de seca podem impactar significativamente a produtividade. Considere estratégias de manejo de água. "
    elif "excesso de chuva" in str(condicoes_climaticas).lower():
        observacoes = " - Excesso de chuva pode aumentar o risco de doenças e dificultar o manejo. "

    observacoes += " - Atenção ao manejo de pragas e doenças comuns em climas úmidos. "
    observacoes += " - Recomendado monitoramento regular da umidade do solo. "


    mensagem = f"""
🌾 **Simulação de Safra - Resultado** ✅ Cultura: {cultura.capitalize()}
✅ Área: {area} hectares
✅ Solo: {tipo_solo.capitalize()}
✅ Clima Previsto: {condicoes_climaticas.capitalize()}
✅ Ciclo: {ciclo_cultura.capitalize()}

📊 **Estimativa de Produção:**
🔹 Produtividade média: **{produtividade_media:,.0f} kg/ha**
🔹 Produção total estimada: **{producao_total_kg:,.0f} kg** (ou {producao_total_toneladas:,.1f} toneladas)

💡 **Observações:**{observacoes}

✅ Deseja realizar **outra simulação** ou **finalizar**?
"""
    return mensagem


# Rota para chat com reconhecimento de perguntas sobre localização e clima
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    mensagem = data.get("mensagem", "").lower()

    if not mensagem:
        return jsonify({"erro": "Mensagem não fornecida."}), 400

    try:
        local = None
        coordenadas = re.findall(r"(-?\d+\.\d+)[, ]+\s*(-?\d+\.\d+)", mensagem)

        if coordenadas:
            lat, lon = coordenadas[0]
            local = obter_localizacao_por_coordenadas(lat, lon)
        else:
            local = obter_localizacao_via_ip()

        if "erro" in local:
            return jsonify({"resposta": "Desculpe, não consegui identificar sua localização."})

        cidade = local.get("cidade", "")
        estado = local.get("estado", "")
        pais = local.get("pais", "")

        # Obter clima pelo OpenWeather
        clima_atual = obter_previsao_tempo(cidade, pais)
        clima_estendido = obter_previsao_estendida(cidade, pais)

        # Envia para o GPT para gerar a resposta
        prompt = (
            f"Você é a Iagro, assistente virtual da Campo Inteligente.\n"
            f"O usuário está em {cidade}, {estado}, {pais}.\n"
            f"O clima atual é: {clima_atual}.\n"
            f"A previsão estendida é: {clima_estendido}.\n"
            f"O usuário disse: {mensagem}\n"
            "Gere uma resposta amigável e informativa sobre o clima e recomendações de plantio para a região, com base nos dados fornecidos. Se o usuário perguntar sobre o clima ou o melhor plantio, forneça informações sobre o clima atual e uma recomendação de plantio concisa e apropriada para a região. Não liste toda a previsão estendida, apenas destaque o período mais favorável, se possível."
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.4,
            )
            resposta = response.choices[0].message.content.strip()
        except openai.APIError as e:
            print(f"DEBUG_OPENAI_ERROR: Erro na API do OpenAI: {e}")
            resposta = "Desculpe, a API do OpenAI está temporariamente indisponível."
        except Exception as e:
            print(f"DEBUG_OPENAI_ERROR: Erro ao chamar OpenAI: {e}")
            resposta = "Desculpe, tive um problema ao processar sua mensagem."

        return jsonify({"resposta": resposta})

    except Exception as e:
        print(f"DEBUG_CHAT_ERROR: Erro inesperado na rota /chat: {e}")
        return jsonify({"erro": str(e)}), 500


# Rota para obter o clima
@app.route("/clima", methods=["GET"])
def clima():
    local = obter_localizacao_via_ip()
    if "erro" in local:
        return jsonify(local), 400
    clima = obter_previsao_tempo(local.get("cidade"), local.get("pais"))
    return jsonify(clima)


# Rota para obter previsão estendida do clima
@app.route("/clima-estendido", methods=["GET"])
def clima_estendido():
    local = obter_localizacao_via_ip()
    if "erro" in local:
        return jsonify(local), 400
    clima = obter_previsao_estendida(local.get("cidade"), local.get("pais"))
    return jsonify(clima)


# Rota para salvar a planilha com os dados fornecidos
@app.route("/salvar", methods=["POST"])
def salvar_planilha():
    try:
        dados = request.json.get("dados", [])
        if not dados:
            return jsonify({"erro": "Dados não forneceeded."}), 400
        arquivo = "respostas_agricultores_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Respostas"
        ws.append(["Nome", "Localização", "Data", "Dia da Semana"])
        for linha in dados:
            ws.append(linha)
        wb.save(arquivo)
        return jsonify({"arquivo_criado": arquivo})
    except Exception as e:
        print(f"DEBUG_PLANILHA_ERROR: Erro ao salvar planilha: {e}")
        return jsonify({"erro": str(e)}), 500


# Rota inicial
@app.route("/", methods=["GET"])
def home():
    return "API Campo Inteligente está online!"


# Função para verificar se o usuário está cadastrado no banco de dados
def is_user_registered(phone_number):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            where_clauses = [f"context->>'{field}' IS NOT NULL" for field in MANDATORY_REGISTRATION_FIELDS]
            query = f"SELECT 1 FROM conversation_contexts WHERE phone_number = %s AND {' AND '.join(where_clauses)};"
            cur.execute(query, (phone_number,))
            result = cur.fetchone()
            cur.close()
            return result is not None
        except psycopg2.Error as e:
            print(f"DEBUG_REGISTRATION_ERROR: Erro ao verificar cadastro do usuário: {e}")
            return False
        finally:
            if conn:
                conn.close()
    return False

# Funções de validação de CPF e RG (básicas)
def is_valid_cpf(cpf_number):
    cpf_number = re.sub(r'\D', '', cpf_number)
    if len(cpf_number) == 11 and cpf_number.isdigit():
        # Adicione lógica de validação de CPF mais robusta se necessário
        return True
    return False

def is_valid_rg(rg_number):
    rg_number = re.sub(r'[\W_]', '', rg_number)
    # RG pode ter diferentes formatos, aqui uma validação mais flexível
    # Verifica se tem entre 5 e 15 caracteres alfanuméricos
    if 5 <= len(rg_number) <= 15 and rg_number.isalnum():
        return True
    return False

def is_valid_date(date_string):
    try:
        # Tenta parsear a data no formato dd/mm/aaaa
        day, month, year = map(int, date_string.split('/'))
        # Verifica se o dia e o mês estão dentro de um intervalo razoável
        if not (1 <= month <= 12 and 1 <= day <= 31):
            return False
        # Tenta criar um objeto datetime para validar a data (ex: 31/02/2024 é inválido)
        datetime(year, month, day)
        return True
    except ValueError:
        return False

# Helper function to get the next registration question key
def get_next_registration_question_key(contexto):
    current_question_key = contexto.get("registration_step")
    current_index = -1
    if current_question_key and current_question_key in REGISTRATION_ORDER:
        current_index = REGISTRATION_ORDER.index(current_question_key)

    if contexto.get("awaiting_email_value_input", False):
        return "email"
    if contexto.get("awaiting_ponto_referencia_value_input", False):
        return "ponto_referencia"

    for i in range(current_index + 1, len(REGISTRATION_ORDER)):
        question_key = REGISTRATION_ORDER[i]
        
        if question_key in contexto and contexto[question_key] not in ["Não informado", None, ""]:
            if question_key == "municipio" and contexto.get("localizacao", {}).get("cidade"):
                if not contexto.get("municipio"):
                    contexto["municipio"] = contexto["localizacao"]["cidade"]
                if not contexto.get("estado_propriedade"):
                    contexto["estado_propriedade"] = contexto["localizacao"].get("estado", "")
                continue
            if question_key == "estado_propriedade" and contexto.get("localizacao", {}).get("estado"):
                continue
            continue

        if question_key == "email":
            if not contexto.get("email_choice_made", False):
                contexto["awaiting_email_choice"] = True
                return "email_choice"
            elif contexto.get("email_choice_made") == "sim" and not contexto.get("email"):
                contexto["awaiting_email_value_input"] = True
                return "email"
            else:
                continue

        if question_key == "ponto_referencia":
            if not contexto.get("ponto_referencia_choice_made", False):
                contexto["awaiting_ponto_referencia_choice"] = True
                return "ponto_referencia_choice"
            elif contexto.get("ponto_referencia_choice_made") == "sim" and not contexto.get("ponto_referencia"):
                contexto["awaiting_ponto_referencia_value_input"] = True
                return "ponto_referencia"
            else:
                continue

        return question_key
            
    return None

# Função para redefinir todos os flags de fluxo de conversa
def reset_all_flow_flags(contexto):
    contexto["awaiting_continuation_choice"] = False
    contexto["awaiting_weather_follow_up_choice"] = False
    contexto["awaiting_menu_return_prompt"] = False
    contexto["awaiting_weather_location"] = False
    contexto["registration_step"] = None
    contexto["editing_registration"] = False
    contexto["awaiting_field_to_edit"] = False
    contexto["current_editing_field"] = None
    contexto["awaiting_post_completion_response"] = False
    contexto["simulacao_safra_ativa"] = False
    contexto["etapa_simulacao"] = None
    contexto["dados_simulacao"] = {}
    contexto["awaiting_safra_finalizacao"] = False
    contexto["simulacao_sub_fluxo"] = None
    contexto["gerar_relatorio_simulacao_ativo"] = False
    contexto["gestao_rebanho_ativo"] = False
    contexto["gestao_rebanho_sub_fluxo"] = None
    contexto["gerar_relatorio_rebanho_ativo"] = False
    contexto["vacinacao_vermifugacao_ativo"] = False
    contexto["vacinacao_vermifugacao_opcao"] = None
    contexto["registro_vacinacao_etapa"] = None
    contexto["dados_vacinacao_registro"] = {}
    contexto["consulta_vacinacao_ativa"] = False
    contexto["awaiting_animal_id_consulta_vac"] = False
    contexto["registro_vermifugacao_etapa"] = None
    contexto["dados_vermifugacao_registro"] = {}
    contexto["consulta_vermifugacao_ativa"] = False
    contexto["awaiting_animal_id_consulta_verm"] = False
    contexto["lembretes_vacinacao_ativa"] = False
    contexto["awaiting_lembretes_contato"] = False
    contexto["cadastro_animal_ativo"] = False
    contexto["registro_animal_etapa"] = None
    contexto["dados_animal_registro"] = {}
    contexto["controle_reprodutivo_ativo"] = False
    contexto["historico_pesagens_ativo"] = False
    contexto["controle_estoque_ativo"] = False
    contexto["controle_estoque_sub_fluxo"] = None
    contexto["gerar_relatorio_estoque_ativo"] = False
    contexto["registro_entrada_estoque_ativo"] = False
    contexto["registro_entrada_estoque_etapa"] = None
    contexto["dados_entrada_estoque_registro"] = {}
    contexto["registro_saida_estoque_ativo"] = False
    contexto["registro_saida_estoque_etapa"] = None
    contexto["dados_saida_estoque_registro"] = {}
    contexto["consulta_estoque_ativa"] = False
    contexto["initial_greeting_step"] = "completed"
    contexto["awaiting_email_choice"] = False
    contexto["email_choice_made"] = False
    contexto["awaiting_email_value_input"] = False
    contexto["awaiting_ponto_referencia_choice"] = False
    contexto["ponto_referencia_choice_made"] = False
    contexto["awaiting_ponto_referencia_value_input"] = False


# Rota do webhook para receber e responder mensagens
@app.route("/webhook", methods=["POST"])
def webhook_route():
    try:
        data = request.json
        print(f"--- Webhook recebido ---")
        print(f"Dados recebidos: {data}")
        event = data.get('event')

        if event == 'messages.upsert':
            numero = data.get('data', {}).get('key', {}).get('remoteJid', '')
            location_message = data.get('data', {}).get('message', {}).get('locationMessage', {})
            mensagem_recebida = data.get('data', {}).get('message', {}).get('conversation', '').lower()

            print(f"DEBUG_WEBHOOK_START: Mensagem recebida de {numero}: '{mensagem_recebida}' (Location: {bool(location_message)})")

            if not numero:
                print(f"DEBUG_WEBHOOK_END: Número não fornecido.")
                return jsonify({"status": "erro", "mensagem": "Número não fornecido."}), 400

            # Carregar o contexto uma única vez no início do processamento do evento messages.upsert
            contexto = load_conversation_context(numero)
            # Definir usuario_cadastrado aqui para que esteja sempre disponível
            usuario_cadastrado = is_user_registered(numero)
            
            # **CORREÇÃO**: Definir o texto da opção de cadastro/edição com base no status do usuário
            if usuario_cadastrado:
                cadastro_opcao_texto = "Editar dados de cadastro"
            else:
                cadastro_opcao_texto = "Fazer meu cadastro"

            nome = contexto.get("nome_completo", "Usuário") 
            localizacao = contexto.get("localizacao")
            current_time = datetime.now().timestamp()

            # Lógica de Timeout da Conversa (aplicada no início do processamento)
            last_interaction_time = contexto.get("last_interaction_time", 0)
            if (current_time - last_interaction_time) > CONVERSATION_TIMEOUT_SECONDS:
                print(f"DEBUG_TIMEOUT: Timeout detectado para {numero}. Reiniciando o fluxo da conversa.")
                reset_all_flow_flags(contexto)
                contexto["initial_greeting_step"] = None # Reset initial greeting step on timeout
                resposta = (
                    f"Olá! 👋 Sou a Iagro, sua assistente de IA da Campo Inteligente. Pronta para otimizar sua gestão agrícola! 🚜🌱 Vamos começar?\n1. Sim\n2. Não"
                )
                contexto["last_interaction_time"] = current_time
                try:
                    save_conversation_context(numero, contexto)
                except Exception as e:
                    print(f"DEBUG_TIMEOUT_SAVE_ERROR: Erro ao salvar contexto após timeout: {e}")
                send_whatsapp_message(numero, resposta)
                return jsonify({"status": "sucesso", "resposta": resposta}), 200

            contexto["last_interaction_time"] = current_time
            # Salvamos o contexto aqui para garantir que o timestamp de última interação seja atualizado
            # antes de qualquer outra lógica de fluxo que possa enviar uma mensagem e, assim,
            # potencialmente encerrar o ciclo do webhook.
            try:
                save_conversation_context(numero, contexto)
            except Exception as e:
                print(f"DEBUG_WEBHOOK_START_SAVE_ERROR: Erro ao salvar contexto após atualização de timestamp: {e}")


            # --- Priorizar o tratamento de mensagens de localização ---
            if location_message:
                print(f"DEBUG_LOCATION_PROCESS: Processando mensagem de localização.")
                lat = location_message.get('degreesLatitude')
                lon = location_message.get('degreesLongitude')
                if lat is not None and lon is not None:
                    local = obter_localizacao_por_coordenadas(lat, lon)
                    if "erro" in local:
                        resposta = "Ops! 😔 Não consegui identificar sua localização a partir das coordenadas enviadas."
                    else:
                        cidade = local.get("cidade", "")
                        estado = local.get("estado", "")
                        pais = local.get("pais", "") 
                        contexto["localizacao"] = {"cidade": cidade, "estado": estado, "pais": pais}
                        if not contexto.get("municipio"):
                            contexto["municipio"] = cidade
                        if not contexto.get("estado_propriedade"):
                            contexto["estado_propriedade"] = estado

                        reset_all_flow_flags(contexto) # Reset all other flags
                        contexto["awaiting_weather_follow_up_choice"] = True # Set weather follow-up

                        try:
                            save_conversation_context(numero, contexto) # Salvar contexto atualizado
                        except Exception as e:
                            print(f"DEBUG_LOCATION_SAVE_ERROR: Erro ao salvar contexto após localização: {e}")
                        resposta = format_weather_response(cidade, pais)
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200
                else:
                    resposta = f"Não consegui processar a localização enviada, {nome}. Por favor, tente novamente ou digite o nome da cidade."
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "erro", "resposta": resposta}), 400

            # --- Se não for mensagem de localização, processar mensagem de texto ---
            if mensagem_recebida:
                # Recuperando flags do contexto (já carregado anteriormente)
                awaiting_weather_location = contexto.get("awaiting_weather_location", False)
                registration_step = contexto.get("registration_step", None)
                awaiting_continuation_choice = contexto.get("awaiting_continuation_choice", False)
                awaiting_post_completion_response = contexto.get("awaiting_post_completion_response", False)
                awaiting_weather_follow_up_choice = contexto.get("awaiting_weather_follow_up_choice", False)
                awaiting_menu_return_prompt = contexto.get("awaiting_menu_return_prompt", False)
                simulacao_safra_ativa = contexto.get("simulacao_safra_ativa", False)
                etapa_simulacao = contexto.get("etapa_simulacao", None)
                dados_simulacao = contexto.get("dados_simulacao", {})
                awaiting_safra_finalizacao = contexto.get("awaiting_safra_finalizacao", False)
                simulacao_sub_fluxo = contexto.get("simulacao_sub_fluxo", None)
                gerar_relatorio_simulacao_ativo = contexto.get("gerar_relatorio_simulacao_ativo", False)
                gestao_rebanho_ativo = contexto.get("gestao_rebanho_ativo", False)
                gestao_rebanho_sub_fluxo = contexto.get("gestao_rebanho_sub_fluxo", None)
                gerar_relatorio_rebanho_ativo = contexto.get("gerar_relatorio_rebanho_ativo", False)
                vacinacao_vermifugacao_ativo = contexto.get("vacinacao_vermifugacao_ativo", False)
                vacinacao_vermifugacao_opcao = contexto.get("vacinacao_vermifugacao_opcao", None)
                registro_vacinacao_etapa = contexto.get("registro_vacinacao_etapa", None)
                dados_vacinacao_registro = contexto.get("dados_vacinacao_registro", {})
                consulta_vacinacao_ativa = contexto.get("consulta_vacinacao_ativa", False)
                awaiting_animal_id_consulta_vac = contexto.get("awaiting_animal_id_consulta_vac", False)
                registro_vermifugacao_etapa = contexto.get("registro_vermifugacao_etapa", None)
                dados_vermifugacao_registro = contexto.get("dados_vermifugacao_registro", {})
                consulta_vermifugacao_ativa = contexto.get("consulta_vermifugacao_ativa", False)
                awaiting_animal_id_consulta_verm = contexto.get("awaiting_animal_id_consulta_verm", False)
                lembretes_vacinacao_ativa = contexto.get("lembretes_vacinacao_ativa", False)
                awaiting_lembretes_contato = contexto.get("awaiting_lembretes_contato", False)
                cadastro_animal_ativo = contexto.get("cadastro_animal_ativo", False)
                registro_animal_etapa = contexto.get("registro_animal_etapa", None)
                dados_animal_registro = contexto.get("dados_animal_registro", {})
                controle_reprodutivo_ativo = contexto.get("controle_reprodutivo_ativo", False)
                historico_pesagens_ativo = contexto.get("historico_pesagens_ativo", False)
                controle_estoque_ativo = contexto.get("controle_estoque_ativo", False)
                controle_estoque_sub_fluxo = contexto.get("controle_estoque_sub_fluxo", None)
                gerar_relatorio_estoque_ativo = contexto.get("gerar_relatorio_estoque_ativo", False)
                registro_entrada_estoque_ativo = contexto.get("registro_entrada_estoque_ativo", False)
                registro_entrada_estoque_etapa = contexto.get("registro_entrada_estoque_etapa", None)
                dados_entrada_estoque_registro = contexto.get("dados_entrada_estoque_registro", {})
                registro_saida_estoque_ativo = contexto.get("registro_saida_estoque_ativo", False)
                registro_saida_estoque_etapa = contexto.get("registro_saida_estoque_etapa", None)
                dados_saida_estoque_registro = contexto.get("dados_saida_estoque_registro", {})
                consulta_estoque_ativa = contexto.get("consulta_estoque_ativa", False)
                registros_vacinacao = contexto.get("registros_vacinacao", [])
                contexto["registros_vacinacao"] = registros_vacinacao
                registros_vermifugacao = contexto.get("registros_vermifugacao", [])
                contexto["registros_vermifugacao"] = registros_vermifugacao
                registros_animais = contexto.get("registros_animais", [])
                contexto["registros_animais"] = registros_animais
                registros_reprodutivos = contexto.get("registros_reprodutivos", [])
                contexto["registros_reprodutivos"] = registros_reprodutivos
                historico_pesagens = contexto.get("historico_pesagens", [])
                contexto["historico_pesagens"] = historico_pesagens
                registros_estoque = contexto.get("registros_estoque", [])
                contexto["registros_estoque"] = registros_estoque
                simulacoes_passadas = contexto.get("simulacoes_passadas", [])
                contexto["simulacoes_passadas"] = simulacoes_passadas
                initial_greeting_step = contexto.get("initial_greeting_step", None)
                editing_registration = contexto.get("editing_registration", False)
                awaiting_field_to_edit = contexto.get("awaiting_field_to_edit", False)
                current_editing_field = contexto.get("current_editing_field", None)
                awaiting_email_choice = contexto.get("awaiting_email_choice", False)
                email_choice_made = contexto.get("email_choice_made", False)
                awaiting_email_value_input = contexto.get("awaiting_email_value_input", False)
                awaiting_ponto_referencia_choice = contexto.get("awaiting_ponto_referencia_choice", False)
                ponto_referencia_choice_made = contexto.get("ponto_referencia_choice_made", False)
                awaiting_ponto_referencia_value_input = contexto.get("awaiting_ponto_referencia_value_input", False)

                # Handle explicit "voltar" or "menu" command
                if ("voltar" in mensagem_recebida or "menu" in mensagem_recebida or "opções" in mensagem_recebida):
                    print(f"DEBUG_COMMAND: Comando 'voltar'/'menu' detectado. Resetando fluxos.")
                    reset_all_flow_flags(contexto)
                    resposta = (
                        f"Ok, retornando ao menu principal. 👋\n\n"
                        f"Escolha uma das opções abaixo para começarmos, {nome}:\n"
                        f"1. Previsão Climática ☁️\n"
                        f"2. Controle de Estoque 📦\n"
                        f"3. Gestão de Rebanho 🐄\n"
                        f"4. Simulação de Safra 🌾\n"
                        f"5. {cadastro_opcao_texto} 📝\n"
                        f"6. Alertas de Pragas 🐛\n"
                        f"7. Análise de Mercado 📈\n"
                        f"8. Localização 📍\n"
                        f"9. Outras Informações 💡"
                    )
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_COMMAND_SAVE_ERROR: Erro ao salvar contexto após comando 'voltar'/'menu': {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # Verificação de usuário cadastrado para pular o fluxo de boas-vindas
                if usuario_cadastrado and initial_greeting_step != "completed":
                    print(f"DEBUG_REGISTERED_USER: Usuário {numero} já cadastrado. Pulando fluxo de saudação inicial.")
                    contexto["initial_greeting_step"] = "completed"
                    resposta = (
                        f"Olá, {nome}! 👋 Bem-vindo de volta ao Campo Inteligente! Estou aqui para ajudar você com sua produção agrícola.\n\n"
                        f"Escolha uma das opções abaixo para começarmos:\n"
                        f"1. Previsão Climática ☁️\n"
                        f"2. Controle de Estoque 📦\n"
                        f"3. Gestão de Rebanho 🐄\n"
                        f"4. Simulação de Safra 🌾\n"
                        f"5. {cadastro_opcao_texto} 📝\n"
                        f"6. Alertas de Pragas 🐛\n"
                        f"7. Análise de Mercado 📈\n"
                        f"8. Localização 📍\n"
                        f"9. Outras Informações 💡"
                    )
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_REGISTERED_USER_SAVE_ERROR: Erro ao salvar contexto para usuário cadastrado: {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # Initial Greeting Flow
                if initial_greeting_step is None:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step None) - Mensagem: '{mensagem_recebida}'")
                    resposta = "Olá! 👋 Sou a Iagro, sua assistente de IA da Campo Inteligente. Pronta para otimizar sua gestão agrícola! 🚜🌱 Vamos começar?\n1. Sim\n2. Não"
                    contexto["initial_greeting_step"] = 1
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_GREETING_SAVE_ERROR: Erro ao salvar contexto após step None: {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200
                
                elif initial_greeting_step == 1:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step 1) - Mensagem: '{mensagem_recebida}'")
                    if mensagem_recebida.strip() == "1" or "sim" in mensagem_recebida:
                        resposta = "Ótimo! Para começarmos, posso saber seu nome? 😊"
                        contexto["initial_greeting_step"] = 2
                    elif mensagem_recebida == "2" or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        resposta = "Entendido. Deseja encerrar a conversa?\n1. Sim\n2. Não"
                        contexto["initial_greeting_step"] = "awaiting_end_conversation"
                    else:
                        resposta = "Não entendi. Por favor, diga '1' para começar ou '2' para encerrar. 🤔"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_GREETING_SAVE_ERROR: Erro ao salvar contexto após etapa 1: {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif initial_greeting_step == 2:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step 2) - Mensagem: '{mensagem_recebida}'")
                    contexto["nome_completo"] = mensagem_recebida.strip().title()
                    nome = contexto["nome_completo"]
                    resposta = f"Prazer em te conhecer, {nome}! 👋 Poderia me falar de qual cidade você está falando? 📍"
                    contexto["initial_greeting_step"] = 3
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_GREETING_SAVE_ERROR: Erro ao salvar contexto após etapa 2: {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif initial_greeting_step == 3:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step 3) - Mensagem: '{mensagem_recebida}'")
                    cidade_input = mensagem_recebida.strip().title()
                    local_info = obter_previsao_tempo(cidade_input, "BR")
                    if "erro" not in local_info:
                        contexto["localizacao"] = {
                            "cidade": local_info.get("cidade", cidade_input),
                            "estado": local_info.get("estado", ""),
                            "pais": "BR"
                        }
                        contexto["municipio"] = local_info.get("cidade", cidade_input)
                        contexto["estado_propriedade"] = local_info.get("estado", "")

                        resposta = f"Certo, {cidade_input}! Entendi sua localização. Vamos em frente com o restante do seu cadastro, {nome}?\n1. Sim\n2. Não"
                        contexto["initial_greeting_step"] = 4
                    else:
                        resposta = f"Não consegui confirmar a cidade '{cidade_input}', {nome}. Por favor, digite o nome da sua cidade novamente ou compartilhe sua localização. 🤔"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_GREETING_SAVE_ERROR: Erro ao salvar contexto após etapa 3: {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif initial_greeting_step == 4:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step 4) - Mensagem: '{mensagem_recebida}'")
                    if mensagem_recebida.strip() == "1" or "sim" in mensagem_recebida:
                        contexto["initial_greeting_step"] = "completed"
                        next_question_key = get_next_registration_question_key(contexto)
                        if next_question_key:
                            contexto["registration_step"] = next_question_key
                            if next_question_key == "email_choice":
                                resposta = REGISTRATION_QUESTIONS["email"]
                            elif next_question_key == "ponto_referencia_choice":
                                resposta = REGISTRATION_QUESTIONS["ponto_referencia"]
                            else:
                                resposta = f"Excelente, {nome}! Agora vamos para o restante do seu cadastro. {REGISTRATION_QUESTIONS[next_question_key]}\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                        else:
                            resposta = f"Excelente, {nome}! Seu cadastro parece completo. Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                            contexto["awaiting_post_completion_response"] = True
                    elif mensagem_recebida.strip() == "2" or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        resposta = f"Entendido, {nome}. Deseja encerrar a conversa?\n1. Sim\n2. Não"
                        contexto["initial_greeting_step"] = "awaiting_end_conversation"
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, diga '1' para continuar o cadastro ou '2' para encerrar. 🤔"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_GREETING_SAVE_ERROR: Erro ao salvar contexto após etapa 4: {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif initial_greeting_step == "awaiting_end_conversation":
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step awaiting_end_conversation) - Mensagem: '{mensagem_recebida}'")
                    if mensagem_recebida.strip() == "1" or "sim" in mensagem_recebida:
                        resposta = f"Ok, {nome}, estarei aqui se precisar de algo mais! Até logo! 👋"
                        contexto.clear()
                        contexto["last_interaction_time"] = current_time
                    elif mensagem_recebida.strip() == "2" or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        resposta = (
                            f"Ok, {nome}! Estou aqui para ajudar você com sua produção agrícola! 👋\n\n"
                            f"Escolha uma das opções abaixo para começarmos:\n"
                            f"1. Previsão Climática ☁️\n"
                            f"2. Controle de Estoque 📦\n"
                            f"3. Gestão de Rebanho 🐄\n"
                            f"4. Simulação de Safra 🌾\n"
                            f"5. {cadastro_opcao_texto} 📝\n"
                            f"6. Alertas de Pragas 🐛\n"
                            f"7. Análise de Mercado 📈\n"
                            f"8. Localização 📍\n"
                            f"9. Outras Informações 💡"
                        )
                        contexto["initial_greeting_step"] = "completed"
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, diga '1' para encerrar ou '2' para ver as opções. 🤔"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_GREETING_SAVE_ERROR: Erro ao salvar contexto após awaiting_end_conversation: {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # Main conversational flow logic
                elif awaiting_continuation_choice:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_continuation_choice")
                    if "continuar" in mensagem_recebida:
                        contexto["awaiting_continuation_choice"] = False
                        resposta = f"Ótimo, {nome}! Vamos continuar de onde paramos. {REGISTRATION_QUESTIONS[registration_step]}"
                    elif "sair" in mensagem_recebida:
                        reset_all_flow_flags(contexto) # Reset all flags
                        resposta = f"Ok, {nome}, o cadastro foi cancelado. Posso ajudar com mais alguma coisa? 👋"
                    else:
                        resposta = f"Por favor, {nome}, diga 'continuar' para retomar o cadastro ou 'sair' para cancelá-lo."
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (continuar cadastro): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif awaiting_weather_follow_up_choice:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_weather_follow_up_choice")
                    if "outra" in mensagem_recebida or "nova" in mensagem_recebida or "sim" in mensagem_recebida or "clima" in mensagem_recebida:
                        reset_all_flow_flags(contexto) # Reset all flags
                        contexto["awaiting_weather_location"] = True # Only set this flag
                        resposta = f"Por favor, {nome}, me diga o nome da cidade ou compartilhe sua localização. 📍\n(Ou 'voltar' para o menu principal)"
                    elif "voltar" in mensagem_recebida or "menu" in mensagem_recebida or "opções" in mensagem_recebida or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        reset_all_flow_flags(contexto) # Reset all flags
                        resposta = (
                            f"Ok, {nome}, retornando ao menu principal. 👋\n\n"
                            f"Escolha uma das opções abaixo para começarmos:\n"
                            f"1. Previsão Climática ☁️\n"
                            f"2. Controle de Estoque 📦\n"
                            f"3. Gestão de Rebanho 🐄\n"
                            f"4. Simulação de Safra 🌾\n"
                            f"5. {cadastro_opcao_texto} 📝\n"
                            f"6. Alertas de Pragas 🐛\n"
                            f"7. Análise de Mercado 📈\n"
                            f"8. Localização 📍\n"
                            f"9. Outras Informações 💡"
                        )
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (seguimento clima): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif awaiting_menu_return_prompt:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_menu_return_prompt")
                    if "sim" in mensagem_recebida or "voltar" in mensagem_recebida or "menu" in mensagem_recebida or "opções" in mensagem_recebida:
                        reset_all_flow_flags(contexto) # Reset all flags
                        resposta = (
                            f"Ok, {nome}, retornando ao menu principal. 👋\n\n"
                            f"Escolha uma das opções abaixo para começarmos:\n"
                            f"1. Previsão Climática ☁️\n"
                            f"2. Controle de Estoque 📦\n"
                            f"3. Gestão de Rebanho 🐄\n"
                            f"4. Simulação de Safra 🌾\n"
                            f"5. {cadastro_opcao_texto} 📝\n"
                            f"6. Alertas de Pragas 🐛\n"
                            f"7. Análise de Mercado 📈\n"
                            f"8. Localização 📍\n"
                            f"9. Outras Informações 💡"
                        )
                    elif "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        contexto["awaiting_menu_return_prompt"] = False
                        resposta = f"Ok, {nome}! Posso ajudar com mais alguma coisa? 👋"
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, responda 'sim' ou 'não'"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (retorno ao menu principal após opção informativa): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif awaiting_post_completion_response:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_post_completion_response")
                    if "sim" in mensagem_recebida:
                        contexto["awaiting_post_completion_response"] = False
                        if contexto.get("gestao_rebanho_ativo"):
                            if contexto.get("vacinacao_vermifugacao_ativo"):
                                resposta = (
                                    f"O que deseja fazer agora na seção de Vacinação e Vermifugação, {nome}? 💉🐛\n"
                                    "Digite:\n\n"
                                    "1. Registrar vacinação\n"
                                    "2. Consultar vacinação\n"
                                    "3. Registrar vermifugação\n"
                                    "4. Consultar vermifugação\n"
                                    "5. Receber lembretes futuros\n"
                                    "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                )
                                contexto["vacinacao_vermifugacao_opcao"] = None
                            else:
                                resposta = (
                                    f"O que você gostaria de fazer agora na Gestão de Rebanho, {nome}? 🐄\n\n"
                                    "Digite:\n"
                                    "1. Cadastrar novo animal\n"
                                    "2. Controle de vacinação e vermifugação\n"
                                    "3. Controle reprodutivo\n"
                                    "4. Histórico de pesagens\n"
                                    "5. Consultar Animais\n"
                                    "6. Gerar Relatório\n"
                                    "Ou 'voltar' para o menu principal."
                                )
                                contexto["gestao_rebanho_sub_fluxo"] = None
                        elif contexto.get("controle_estoque_ativo"):
                            resposta = (
                                f"O que você gostaria de fazer agora no Controle de Estoque, {nome}? 📦\n\n"
                                "Digite:\n"
                                "1. Registrar Entrada de Insumos/Produtos\n"
                                "2. Registrar Saída de Insumos/Produtos\n"
                                "3. Consultar Estoque\n"
                                "4. Avisos de estoque baixo\n"
                                "5. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                            contexto["controle_estoque_sub_fluxo"] = None
                            contexto["registro_entrada_estoque_ativo"] = False
                            contexto["registro_entrada_estoque_etapa"] = None
                            contexto["dados_entrada_estoque_registro"] = {}
                            contexto["registro_saida_estoque_ativo"] = False
                            contexto["registro_saida_estoque_etapa"] = None
                            contexto["dados_saida_estoque_registro"] = {}
                            contexto["consulta_estoque_ativa"] = False
                            contexto["gerar_relatorio_estoque_ativo"] = False
                        elif contexto.get("simulacao_safra_ativa"):
                            resposta = (
                                f"O que você gostaria de fazer agora na Simulação de Safra, {nome}? 🌾\n\n"
                                "Digite:\n"
                                "1. Iniciar nova simulação\n"
                                "2. Consultar Simulações Anteriores\n"
                                "3. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                            contexto["simulacao_sub_fluxo"] = None
                            contexto["gerar_relatorio_simulacao_ativo"] = False
                        else:
                            resposta = (
                                f"Ok, {nome}! Estou aqui para ajudar você com sua produção agrícola! 👋\n\n"
                                f"Escolha uma das opções abaixo para começarmos:\n"
                                f"1. Previsão Climática ☁️\n"
                                f"2. Controle de Estoque 📦\n"
                                f"3. Gestão de Rebanho 🐄\n"
                                f"4. Simulação de Safra 🌾\n"
                                f"5. {cadastro_opcao_texto} 📝\n"
                                f"6. Alertas de Pragas 🐛\n"
                                f"7. Análise de Mercado 📈\n"
                                f"8. Localização 📍\n"
                                f"9. Outras Informações 💡"
                            )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (pós-conclusão - sim): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200
                    elif "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        reset_all_flow_flags(contexto) # Reset all flags
                        resposta = (
                            f"Ok, {nome}! Estou aqui para ajudar você com sua produção agrícola! 👋\n\n"
                            f"Escolha uma das opções abaixo para começarmos:\n"
                            f"1. Previsão Climática ☁️\n"
                            f"2. Controle de Estoque 📦\n"
                            f"3. Gestão de Rebanho 🐄\n"
                            f"4. Simulação de Safra 🌾\n"
                            f"5. {cadastro_opcao_texto} 📝\n"
                            f"6. Alertas de Pragas 🐛\n"
                            f"7. Análise de Mercado 📈\n"
                            f"8. Localização 📍\n"
                            f"9. Outras Informações 💡"
                        )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (retorno ao menu principal após 'não'): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, responda 'sim' ou 'não'."
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (pós-conclusão - opção inválida): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif simulacao_safra_ativa:
                    print(f"DEBUG_FLOW: Fluxo: simulacao_safra_ativa")
                    etapa = contexto.get("etapa_simulacao")
                    dados = contexto.get("dados_simulacao", {})

                    if "voltar" in mensagem_recebida:
                        if simulacao_sub_fluxo is not None or gerar_relatorio_simulacao_ativo:
                            contexto["simulacao_sub_fluxo"] = None
                            contexto["gerar_relatorio_simulacao_ativo"] = False
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Simulação de Safra. 🌾\n\n"
                                "O que você gostaria de fazer?\n\n"
                                "1. Iniciar nova simulação\n"
                                "2. Consultar Simulações Anteriores\n"
                                "3. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                        elif etapa == 1:
                            reset_all_flow_flags(contexto) # Reset all flags
                            resposta = (
                                f"Ok, {nome}, retornando ao menu principal. 👋\n\n"
                                f"Escolha uma das opções abaixo para começarmos:\n"
                                f"1. Previsão Climática ☁️\n"
                                f"2. Controle de Estoque 📦\n"
                                f"3. Gestão de Rebanho 🐄\n"
                                f"4. Simulação de Safra 🌾\n"
                                f"5. {cadastro_opcao_texto} 📝\n"
                                f"6. Alertas de Pragas 🐛\n"
                                f"7. Análise de Mercado 📈\n"
                                f"8. Localização 📍\n"
                                f"9. Outras Informações 💡"
                            )
                        else:
                            contexto["etapa_simulacao"] -= 1
                            if contexto["etapa_simulacao"] == 0:
                                reset_all_flow_flags(contexto) # Reset all flags
                                resposta = (
                                    f"Ok, {nome}, retornando ao menu principal. 👋\n\n"
                                    f"Escolha uma das opções abaixo para começarmos:\n"
                                    f"1. Previsão Climática ☁️\n"
                                    f"2. Controle de Estoque 📦\n"
                                    f"3. Gestão de Rebanho 🐄\n"
                                    f"4. Simulação de Safra 🌾\n"
                                    f"5. {cadastro_opcao_texto} 📝\n"
                                    f"6. Alertas de Pragas 🐛\n"
                                    f"7. Análise de Mercado 📈\n"
                                    f"8. Localização 📍\n"
                                    f"9. Outras Informações 💡"
                                )
                            else:
                                resposta = f"Ok, {nome}, voltando. Por favor, responda novamente a pergunta anterior sobre a simulação.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação voltar): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    if simulacao_sub_fluxo is None:
                        if mensagem_recebida.strip() == "1":
                            contexto["simulacao_sub_fluxo"] = 1
                            contexto["etapa_simulacao"] = 1
                            contexto["dados_simulacao"] = {}
                            resposta = f"Olá, {nome}! 👋 Vamos começar a sua simulação de safra. 🌾\n\nPor favor, me informe os seguintes dados para gerar a previsão mais precisa possível. 🌱\n\n👉 Qual é a cultura que deseja simular?\nEx.: soja, milho, trigo, café, etc.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif mensagem_recebida.strip() == "2":
                            contexto["simulacao_sub_fluxo"] = 2
                            if contexto["simulacoes_passadas"]:
                                resposta = "📊 **Suas Simulações Anteriores:** 📊\n"
                                for i, sim in enumerate(contexto["simulacoes_passadas"]):
                                    cultura = sim.get("cultura", "N/A")
                                    area = sim.get("area", "N/A")
                                    produtividade = sim.get("produtividade_media", "N/A")
                                    resposta += f"{i+1}. Cultura: {cultura.capitalize()}, Área: {area} ha, Produtividade Estimada: {produtividade} kg/ha\n"
                            else:
                                resposta = f"Você ainda não realizou nenhuma simulação, {nome}. Que tal iniciar uma? 🌱"
                            resposta += "\n\nDeseja voltar ao menu de Simulação de Safra? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        elif mensagem_recebida.strip() == "3":
                            contexto["simulacao_sub_fluxo"] = 3
                            contexto["gerar_relatorio_simulacao_ativo"] = True
                            if contexto["simulacoes_passadas"]:
                                resposta = "📈 **Relatório de Simulações de Safra:** 📈\n\n"
                                for i, sim in enumerate(contexto["simulacoes_passadas"]):
                                    cultura = sim.get("cultura", "N/A")
                                    area = sim.get("area", "N/A")
                                    tipo_solo = sim.get("tipo_solo", "N/A")
                                    condicoes_climaticas = sim.get("condicoes_climaticas", "N/A")
                                    ciclo_cultura = sim.get("ciclo_cultura", "N/A")
                                    produtividade = sim.get("produtividade_media", "N/A")
                                    
                                    resposta += f"--- Simulação {i+1} ---\n"
                                    resposta += f"Cultura: {cultura.capitalize()}\n"
                                    resposta += f"Área: {area} ha\n"
                                    resposta += f"Tipo de Solo: {tipo_solo.capitalize()}\n"
                                    resposta += f"Condições Climáticas: {condicoes_climaticas.capitalize()}\n"
                                    resposta += f"Ciclo da Cultura: {ciclo_cultura.capitalize()}\n"
                                    resposta += f"Produtividade Estimada: {produtividade} kg/ha\n\n"
                                
                                resposta += (
                                    "Este é um resumo textual. Se você esperava um relatório em formato de imagem (gráfico), PDF, Word ou Excel, "
                                    "informo que, no momento, nosso sistema via WhatsApp só consegue enviar relatórios em texto. "
                                    "Para outros formatos, seria necessário acessar nossa plataforma web.\n\n"
                                )
                            else:
                                resposta = f"Não há simulações registradas para gerar um relatório, {nome}. Que tal iniciar uma? 🌱"
                            
                            resposta += "\n\nDeseja voltar ao menu de Simulação de Safra? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        else:
                            resposta = (
                                f"Opção inválida, {nome}. Por favor, escolha uma das opções para Simulação de Safra: 🌾\n"
                                "1. Iniciar nova simulação\n"
                                "2. Consultar Simulações Anteriores\n"
                                "3. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação safra sub-menu): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif simulacao_sub_fluxo == 1:
                        if etapa == 1:
                            dados["cultura"] = mensagem_recebida
                            contexto["etapa_simulacao"] = 2
                            contexto["dados_simulacao"] = dados
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação etapa 1): {e}")
                            resposta = f"✅ Ótimo, {nome}! Agora, informe a área de plantio em hectares (ha): 🌱\nEx.: 50 ha\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif etapa == 2:
                            try:
                                area_str = re.findall(r'(\d+\.?\d*)', mensagem_recebida)
                                if area_str:
                                    area = float(area_str[0])
                                else:
                                    raise ValueError("Nenhum número válido encontrado para a área.")
                                if area <= 0:
                                    raise ValueError("Área deve ser um número positivo.")
                                dados["area"] = area
                                contexto["etapa_simulacao"] = 3
                                contexto["dados_simulacao"] = dados
                                try:
                                    save_conversation_context(numero, contexto)
                                except Exception as e:
                                    print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação etapa 2): {e}")
                                resposta = f"✅ Perfeito, {nome}! Qual o tipo de solo predominante? ⛰️\nEx.: arenoso, argiloso, misto, etc.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            except ValueError:
                                resposta = f"Por favor, {nome}, informe a área em hectares usando um número válido (ex: 50, 100.5).\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                        elif etapa == 3:
                            dados["tipo_solo"] = mensagem_recebida
                            contexto["etapa_simulacao"] = 4
                            contexto["dados_simulacao"] = dados
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação etapa 3): {e}")
                            resposta = f"✅ E quais são as condições climáticas previstas, {nome}? ☀️🌧️\nEx.: seca, chuva moderada, excesso de chuva, clima ideal...\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif etapa == 4:
                            dados["condicoes_climaticas"] = mensagem_recebida
                            contexto["etapa_simulacao"] = 5
                            contexto["dados_simulacao"] = dados
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação etapa 4): {e}")
                            resposta = f"✅ Por fim, {nome}, qual é a variedade ou o ciclo da cultura? ⏳\nEx.: ciclo precoce, médio ou tardio?\n(Se não souber, pode digitar \"não sei\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif etapa == 5:
                            dados["ciclo_cultura"] = mensagem_recebida
                            contexto["simulacoes_passadas"].append(dados)

                            contexto["etapa_simulacao"] = None
                            contexto["simulacao_safra_ativa"] = False
                            contexto["simulacao_sub_fluxo"] = None
                            contexto["dados_simulacao"] = {}
                            contexto["gerar_relatorio_simulacao_ativo"] = False
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação etapa 5): {e}")
                            
                            send_whatsapp_message(numero, "🚜 Processando a simulação da sua safra... \n\n🔄 Isso pode levar alguns segundos...")
                            
                            resultado_simulacao = simular_safra(dados)
                            
                            resposta_resultado = formatar_resultado_simulacao(dados, resultado_simulacao)
                            send_whatsapp_message(numero, resposta_resultado)

                            contexto["awaiting_safra_finalizacao"] = True
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação finalização): {e}")
                            resposta = f"✅ Deseja realizar **outra simulação**, {nome}, ou **finalizar**? 🤔\n\n1. Nova simulação\n2. Sair\n(Ou 'voltar' para o menu principal)"
                        else:
                            resposta = f"Ocorreu um erro no fluxo da simulação, {nome}. Por favor, digite '4' para iniciar uma nova simulação ou 'menu' para voltar ao menu principal."
                            reset_all_flow_flags(contexto) # Reset all flags
                            contexto["simulacao_safra_ativa"] = True # Keep simulation active
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (erro simulação etapa): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    else:
                        resposta = f"Ocorreu um erro no fluxo de Simulação de Safra, {nome}. Por favor, digite '4' para voltar ao menu de Simulação de Safra ou 'menu' para voltar ao menu principal."
                        reset_all_flow_flags(contexto) # Reset all flags
                        contexto["simulacao_safra_ativa"] = True
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (erro simulação safra sub-fluxo): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif awaiting_safra_finalizacao:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_safra_finalizacao")
                    if mensagem_recebida.strip() == "1":
                        contexto["simulacao_safra_ativa"] = True
                        contexto["etapa_simulacao"] = 1
                        contexto["dados_simulacao"] = {}
                        contexto["awaiting_safra_finalizacao"] = False
                        contexto["simulacao_sub_fluxo"] = 1
                        contexto["gerar_relatorio_simulacao_ativo"] = False
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação nova): {e}")
                        resposta_nova_simulacao = f"Ok, {nome}, vamos iniciar uma nova simulação. 🌱\n\n👉 Qual é a cultura que deseja simular?\nEx.: soja, milho, trigo, café, etc.\n(Ou 'voltar' para o menu principal)"
                        send_whatsapp_message(numero, resposta_nova_simulacao)
                        return jsonify({"status": "sucesso", "resposta": resposta_nova_simulacao}), 200
                    elif mensagem_recebida.strip() == "2":
                        reset_all_flow_flags(contexto) # Reset all flags
                        resposta_sair = (
                            f"Ok, {nome}, obrigado por utilizar a simulação de safra! 👋 Posso ajudar com mais alguma coisa?\n\n"
                            f"Escolha uma das opções abaixo para começarmos:\n"
                            f"1. Previsão Climática ☁️\n"
                            f"2. Controle de Estoque 📦\n"
                            f"3. Gestão de Rebanho 🐄\n"
                            f"4. Simulação de Safra 🌾\n"
                            f"5. {cadastro_opcao_texto} 📝\n"
                            f"6. Alertas de Pragas 🐛\n"
                            f"7. Análise de Mercado 📈\n"
                            f"8. Localização 📍\n"
                            f"9. Outras Informações 💡"
                        )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (simulação sair): {e}")
                        send_whatsapp_message(numero, resposta_sair)
                        return jsonify({"status": "sucesso", "resposta": resposta_sair}), 200
                    else:
                        resposta_opcao_invalida = f"Opção inválida, {nome}. Digite 1 para nova simulação ou 2 para sair.\n(Ou 'voltar' para o menu principal)"
                        send_whatsapp_message(numero, resposta_opcao_invalida)
                        return jsonify({"status": "erro", "resposta": resposta_opcao_invalida}), 200

                elif controle_estoque_ativo:
                    print(f"DEBUG_FLOW: Fluxo: controle_estoque_ativo")
                    if "voltar" in mensagem_recebida:
                        if registro_entrada_estoque_ativo or registro_saida_estoque_ativo or consulta_estoque_ativa or gerar_relatorio_estoque_ativo:
                            contexto["registro_entrada_estoque_ativo"] = False
                            contexto["registro_entrada_estoque_etapa"] = None
                            contexto["dados_entrada_estoque_registro"] = {}
                            contexto["registro_saida_estoque_ativo"] = False
                            contexto["registro_saida_estoque_etapa"] = None
                            contexto["dados_saida_estoque_registro"] = {}
                            contexto["consulta_estoque_ativa"] = False
                            contexto["gerar_relatorio_estoque_ativo"] = False
                            contexto["controle_estoque_sub_fluxo"] = None
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Controle de Estoque. 📦\n\n"
                                "O que você gostaria de fazer?\n\n"
                                "1. Registrar Entrada de Insumos/Produtos\n"
                                "2. Registrar Saída de Insumos/Produtos\n"
                                "3. Consultar Estoque\n"
                                "4. Avisos de estoque baixo\n"
                                "5. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                        elif controle_estoque_sub_fluxo is None:
                            reset_all_flow_flags(contexto) # Reset all flags
                            resposta = (
                                f"Ok, {nome}, retornando ao menu principal. 👋\n\n"
                                f"Escolha uma das opções abaixo para começarmos:\n"
                                f"1. Previsão Climática ☁️\n"
                                f"2. Controle de Estoque 📦\n"
                                f"3. Gestão de Rebanho 🐄\n"
                                f"4. Simulação de Safra 🌾\n"
                                f"5. {cadastro_opcao_texto} 📝\n"
                                f"6. Alertas de Pragas 🐛\n"
                                f"7. Análise de Mercado 📈\n"
                                f"8. Localização 📍\n"
                                f"9. Outras Informações 💡"
                            )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (controle estoque voltar): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    if controle_estoque_sub_fluxo is None:
                        if mensagem_recebida.strip() == "1":
                            contexto["controle_estoque_sub_fluxo"] = 1
                            contexto["registro_entrada_estoque_ativo"] = True
                            contexto["registro_entrada_estoque_etapa"] = 1
                            contexto["dados_entrada_estoque_registro"] = {}
                            resposta = f"✅ Qual o nome/identificação do item que está dando entrada no estoque, {nome}?  \n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif mensagem_recebida.strip() == "2":
                            contexto["controle_estoque_sub_fluxo"] = 2
                            contexto["registro_saida_estoque_ativo"] = True
                            contexto["registro_saida_estoque_etapa"] = 1
                            contexto["dados_saida_estoque_registro"] = {}
                            resposta = f"✅ Qual o nome/identificação do item que está saindo do estoque, {nome}? 📤\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif mensagem_recebida.strip() == "3":
                            contexto["controle_estoque_sub_fluxo"] = 3
                            contexto["consulta_estoque_ativa"] = True
                            if contexto["registros_estoque"]:
                                resposta = "📦 **Itens em Estoque:** 📦\n"
                                for i, item in enumerate(contexto["registros_estoque"]):
                                    nome_item = item.get("nome_item", "N/A")
                                    quantidade = item.get("quantidade", "N/A")
                                    data_entrada = item.get("data_entrada", "N/A")
                                    data_fabricacao = item.get("data_fabricacao", "N/A")
                                    data_vencimento = item.get("data_vencimento", "N/A")
                                    lote = item.get("numero_lote", "N/A")
                                    resposta += f"{i+1}. {nome_item.capitalize()} - Qtd: {quantidade} - Entrada: {data_entrada} - Fab: {data_fabricacao} - Venc: {data_vencimento} - Lote: {lote}\n"
                            else:
                                resposta = f"Seu estoque está vazio no momento, {nome}. Que tal registrar uma entrada? 📦"
                            resposta += "\n\nDeseja voltar ao menu de Controle de Estoque? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        elif mensagem_recebida.strip() == "4":
                            contexto["controle_estoque_sub_fluxo"] = 4
                            resposta = f"Em breve teremos os avisos de estoque baixo, {nome}! Aguarde! 📉\n\nDeseja voltar ao menu de Controle de Estoque? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        elif mensagem_recebida.strip() == "5":
                            contexto["controle_estoque_sub_fluxo"] = 5
                            contexto["gerar_relatorio_estoque_ativo"] = True
                            if contexto["registros_estoque"]:
                                resposta = "📊 **Relatório Detalhado de Estoque:** 📊\n\n"
                                for i, item in enumerate(contexto["registros_estoque"]):
                                    nome_item = item.get("nome_item", "N/A")
                                    quantidade = item.get("quantidade", "N/A")
                                    data_entrada = item.get("data_entrada", "N/A")
                                    data_fabricacao = item.get("data_fabricacao", "N/A")
                                    data_vencimento = item.get("data_vencimento", "N/A")
                                    numero_lote = item.get("numero_lote", "N/A")
                                    
                                    resposta += f"--- Item {i+1} ---\n"
                                    resposta += f"Nome: {nome_item.capitalize()}\n"
                                    resposta += f"Quantidade: {quantidade}\n"
                                    resposta += f"Data de Entrada: {data_entrada}\n"
                                    resposta += f"Data de Fabricação: {data_fabricacao}\n"
                                    resposta += f"Data de Vencimento: {data_vencimento}\n"
                                    resposta += f"Número de Lote: {numero_lote}\n\n"
                                
                                resposta += (
                                    "Este é um resumo textual. Se você esperava um relatório em formato de imagem (gráfico), PDF, Word ou Excel, "
                                    "informo que, no momento, nosso sistema via WhatsApp só consegue enviar relatórios em texto. "
                                    "Para outros formatos, seria necessário acessar nossa plataforma web.\n\n"
                                )
                            else:
                                resposta = f"Não há itens registrados no estoque para gerar um relatório, {nome}. Que tal registrar uma entrada? 📦"
                            
                            resposta += "\n\nDeseja voltar ao menu de Controle de Estoque? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        else:
                            resposta = (
                                f"Opção inválida, {nome}. Por favor, escolha uma das opções para Controle de Estoque: 📦\n"
                                "1. Registrar Entrada de Insumos/Produtos\n"
                                "2. Registrar Saída de Insumos/Produtos\n"
                                "3. Consultar Estoque\n"
                                "4. Avisos de estoque baixo\n"
                                "5. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (controle estoque sub-menu): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200
                    
                    elif registro_entrada_estoque_ativo:
                        print(f"DEBUG_FLOW: Fluxo: registro_entrada_estoque_etapa {registro_entrada_estoque_etapa}")
                        if registro_entrada_estoque_etapa == 1:
                            dados_entrada_estoque_registro["nome_item"] = mensagem_recebida.strip()
                            contexto["registro_entrada_estoque_etapa"] = 2
                            resposta = f"✅ Qual a quantidade do item, {nome}? (Ex: 100 kg, 50 litros, 3 unidades) 🔢\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_entrada_estoque_etapa == 2:
                            dados_entrada_estoque_registro["quantidade"] = mensagem_recebida.strip()
                            contexto["registro_entrada_estoque_etapa"] = 3
                            resposta = f"✅ Qual a data de entrada do item, {nome}? (dd/mm/aaaa) 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_entrada_estoque_etapa == 3:
                            if not is_valid_date(mensagem_recebida.strip()):
                                resposta = f"Data inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2024). 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                            dados_entrada_estoque_registro["data_entrada"] = mensagem_recebida.strip()
                            contexto["registro_entrada_estoque_etapa"] = 4
                            resposta = f"✅ Qual a data de fabricação do item, {nome}? (dd/mm/aaaa) 🗓️\n(Se não houver, responda \"não\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_entrada_estoque_etapa == 4:
                            data_fabricacao = mensagem_recebida.strip()
                            if data_fabricacao != "não" and not is_valid_date(data_fabricacao):
                                resposta = f"Data inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2024) ou responda 'não'. 🗓️\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                            dados_entrada_estoque_registro["data_fabricacao"] = data_fabricacao if data_fabricacao != "não" else "Não informado"
                            contexto["registro_entrada_estoque_etapa"] = 5
                            resposta = f"✅ Qual a data de vencimento do item, {nome}? (dd/mm/aaaa) ⏳\n(Se não houver, responda \"não\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_entrada_estoque_etapa == 5:
                            data_vencimento = mensagem_recebida.strip()
                            if data_vencimento != "não" and not is_valid_date(data_vencimento):
                                resposta = f"Data inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2024) ou responda 'não'. ⏳\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                            dados_entrada_estoque_registro["data_vencimento"] = data_vencimento if data_vencimento != "não" else "Não informado"
                            contexto["registro_entrada_estoque_etapa"] = 6
                            resposta = f"✅ Qual o número do lote do item, {nome}? (Se não houver, responda \"não\") 🏷️\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_entrada_estoque_etapa == 6:
                            numero_lote = mensagem_recebida.strip()
                            dados_entrada_estoque_registro["numero_lote"] = numero_lote if numero_lote != "não" else "Não informado"
                            
                            contexto["registros_estoque"].append(dados_entrada_estoque_registro)

                            contexto["registro_entrada_estoque_ativo"] = False
                            contexto["registro_entrada_estoque_etapa"] = None
                            contexto["controle_estoque_sub_fluxo"] = None

                            resposta = f"""📦 **Registro de Entrada Concluído, {nome}!** 📦
Item: {dados_entrada_estoque_registro.get("nome_item", "N/A").capitalize()}
Quantidade: {dados_entrada_estoque_registro.get("quantidade", "N/A")}
Data de Entrada: {dados_entrada_estoque_registro.get("data_entrada", "N/A")}
Data de Fabricação: {dados_entrada_estoque_registro.get("data_fabricacao", "N/A")}
Data de Vencimento: {dados_entrada_estoque_registro.get("data_vencimento", "N/A")}
Número de Lote: {dados_entrada_estoque_registro.get("numero_lote", "N/A")}
✅ Item registrado com sucesso! 🎉"""
                            
                            resposta += f"\n\nO que você gostaria de fazer agora no Controle de Estoque, {nome}? 📦\n\nDigite:\n1. Registrar Entrada de Insumos/Produtos\n2. Registrar Saída de Insumos/Produtos\n3. Consultar Estoque\n4. Avisos de estoque baixo\n5. Gerar Relatório\nOu 'voltar' para o menu principal."
                            contexto["awaiting_post_completion_response"] = True
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (registro entrada estoque etapa {registro_entrada_estoque_etapa}): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif registro_saida_estoque_ativo:
                        print(f"DEBUG_FLOW: Fluxo: registro_saida_estoque_etapa {registro_saida_estoque_etapa}")
                        if registro_saida_estoque_etapa == 1:
                            item_nome_saida = mensagem_recebida.strip().lower()
                            # Verificar se o item existe no estoque
                            item_encontrado = None
                            for item in contexto["registros_estoque"]:
                                if item.get("nome_item", "").lower() == item_nome_saida:
                                    item_encontrado = item
                                    break
                            
                            if item_encontrado:
                                dados_saida_estoque_registro["nome_item"] = item_nome_saida
                                contexto["registro_saida_estoque_etapa"] = 2
                                resposta = f"✅ Qual a quantidade de '{item_nome_saida.capitalize()}' que está saindo, {nome}? (Disponível: {item_encontrado.get('quantidade', 'N/A')}) 🔢\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            else:
                                resposta = f"O item '{item_nome_saida.capitalize()}' não foi encontrado no seu estoque, {nome}. Por favor, verifique o nome e tente novamente.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                        elif registro_saida_estoque_etapa == 2:
                            try:
                                quantidade_saida_str = re.findall(r'(\d+\.?\d*)', mensagem_recebida)
                                if quantidade_saida_str:
                                    quantidade_saida = float(quantidade_saida_str[0])
                                else:
                                    raise ValueError("Nenhum número válido encontrado para a quantidade.")
                                
                                item_nome = dados_saida_estoque_registro["nome_item"]
                                item_no_estoque = next((item for item in contexto["registros_estoque"] if item.get("nome_item", "").lower() == item_nome), None)

                                if item_no_estoque:
                                    quantidade_disponivel_str = str(item_no_estoque.get("quantidade", "0")).replace(',', '.')
                                    quantidade_disponivel_match = re.findall(r'(\d+\.?\d*)', quantidade_disponivel_str)
                                    quantidade_disponivel = float(quantidade_disponivel_match[0]) if quantidade_disponivel_match else 0

                                    if quantidade_saida > quantidade_disponivel:
                                        resposta = f"A quantidade de saída ({quantidade_saida}) é maior que a disponível ({quantidade_disponivel}), {nome}. Por favor, digite uma quantidade válida. 🔢\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                        try: save_conversation_context(numero, contexto)
                                        except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                        send_whatsapp_message(numero, resposta)
                                        return jsonify({"status": "erro", "resposta": resposta}), 200
                                    else:
                                        # Atualiza a quantidade no estoque
                                        item_no_estoque["quantidade"] = str(quantidade_disponivel - quantidade_saida)
                                        dados_saida_estoque_registro["quantidade"] = mensagem_recebida.strip()
                                        contexto["registro_saida_estoque_etapa"] = 3
                                        resposta = f"✅ Qual a data de saída do item, {nome}? (dd/mm/aaaa) 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                else:
                                    resposta = f"Ocorreu um erro ao encontrar o item no estoque para atualização de quantidade, {nome}. Por favor, tente novamente.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                            except ValueError:
                                resposta = f"Por favor, {nome}, informe a quantidade em números. 🔢\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                        elif registro_saida_estoque_etapa == 3:
                            if not is_valid_date(mensagem_recebida.strip()):
                                resposta = f"Data inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2024). 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                            dados_saida_estoque_registro["data_saida"] = mensagem_recebida.strip()
                            
                            contexto["registro_saida_estoque_ativo"] = False
                            contexto["registro_saida_estoque_etapa"] = None
                            contexto["controle_estoque_sub_fluxo"] = None

                            resposta = f"""📤 **Registro de Saída Concluído, {nome}!** 📤
Item: {dados_saida_estoque_registro.get("nome_item", "N/A").capitalize()}
Quantidade: {dados_saida_estoque_registro.get("quantidade", "N/A")}
Data de Saída: {dados_saida_estoque_registro.get("data_saida", "N/A")}
✅ Saída registrada com sucesso! 🎉"""

                            resposta += f"\n\nO que você gostaria de fazer agora no Controle de Estoque, {nome}? 📦\n\nDigite:\n1. Registrar Entrada de Insumos/Produtos\n2. Registrar Saída de Insumos/Produtos\n3. Consultar Estoque\n4. Avisos de estoque baixo\n5. Gerar Relatório\nOu 'voltar' para o menu principal."
                            contexto["awaiting_post_completion_response"] = True
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (registro saída estoque etapa {registro_saida_estoque_etapa}): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    else:
                        resposta = f"Ocorreu um erro no fluxo de Controle de Estoque, {nome}. Por favor, digite '2' para voltar ao menu de Controle de Estoque ou 'menu' para voltar ao menu principal."
                        reset_all_flow_flags(contexto) # Reset all flags
                        contexto["controle_estoque_ativo"] = True
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (erro controle estoque sub-fluxo): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif gestao_rebanho_ativo:
                    print(f"DEBUG_FLOW: Fluxo: gestao_rebanho_ativo")
                    if "voltar" in mensagem_recebida:
                        if vacinacao_vermifugacao_ativo:
                            contexto["vacinacao_vermifugacao_ativo"] = False
                            contexto["vacinacao_vermifugacao_opcao"] = None
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Vacinação e Vermifugação. 💉🐛\n"
                                "O que você gostaria de fazer?\n\n"
                                "Digite:\n"
                                "1. Registrar vacinação\n"
                                "2. Consultar vacinação\n"
                                "3. Registrar vermifugação\n"
                                "4. Consultar vermifugação\n"
                                "5. Receber lembretes futuros\n"
                                "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                            )
                        elif gestao_rebanho_sub_fluxo is not None:
                            contexto["cadastro_animal_ativo"] = False
                            contexto["registro_animal_etapa"] = None
                            contexto["dados_animal_registro"] = {}
                            contexto["controle_reprodutivo_ativo"] = False
                            contexto["historico_pesagens_ativo"] = False
                            contexto["gerar_relatorio_rebanho_ativo"] = False
                            contexto["gestao_rebanho_sub_fluxo"] = None
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Gestão de Rebanho. 🐄\n\n"
                                "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                                "Digite:\n"
                                "1. Cadastrar novo animal\n"
                                "2. Controle de vacinação e vermifugação\n"
                                "3. Controle reprodutivo\n"
                                "4. Histórico de pesagens\n"
                                "5. Consultar Animais\n"
                                "6. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                        else:
                            reset_all_flow_flags(contexto) # Reset all flags
                            resposta = (
                                f"Ok, {nome}, retornando ao menu principal. 👋\n\n"
                                f"Escolha uma das opções abaixo para começarmos:\n"
                                f"1. Previsão Climática ☁️\n"
                                f"2. Controle de Estoque 📦\n"
                                f"3. Gestão de Rebanho 🐄\n"
                                f"4. Simulação de Safra 🌾\n"
                                f"5. {cadastro_opcao_texto} 📝\n"
                                f"6. Alertas de Pragas 🐛\n"
                                f"7. Análise de Mercado 📈\n"
                                f"8. Localização 📍\n"
                                f"9. Outras Informações 💡"
                            )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (gestão rebanho voltar para principal): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    if gestao_rebanho_sub_fluxo is None:
                        if mensagem_recebida.strip() == "1":
                            contexto["gestao_rebanho_sub_fluxo"] = 1
                            contexto["cadastro_animal_ativo"] = True
                            contexto["registro_animal_etapa"] = 1
                            contexto["dados_animal_registro"] = {}
                            resposta = f"✅ Informe o nome ou identificação do novo animal, {nome}: 🐮\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                        elif mensagem_recebida.strip() == "2":
                            contexto["gestao_rebanho_sub_fluxo"] = 2
                            contexto["vacinacao_vermifugacao_ativo"] = True
                            contexto["vacinacao_vermifugacao_opcao"] = None
                            resposta = (
                                f"🐄 **Controle de Vacinação e Vermifugação, {nome}** 💉🐛\n\n"
                                "O que você gostaria de fazer?\n\n"
                                "Digite:\n"
                                "1. Registrar vacinação\n"
                                "2. Consultar vacinação\n"
                                "3. Registrar vermifugação\n"
                                "4. Consultar vermifugação\n"
                                "5. Receber lembretes futuros\n"
                                "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                            )
                        elif mensagem_recebida.strip() == "3":
                            contexto["gestao_rebanho_sub_fluxo"] = 3
                            contexto["controle_reprodutivo_ativo"] = True
                            resposta = f"Em breve teremos o controle reprodutivo, {nome}! Aguarde! 🤰\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        elif mensagem_recebida.strip() == "4":
                            contexto["gestao_rebanho_sub_fluxo"] = 4
                            contexto["historico_pesagens_ativo"] = True
                            resposta = f"Em breve teremos o histórico de pesagens, {nome}! Aguarde! ⚖️\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        elif mensagem_recebida.strip() == "5":
                            contexto["gestao_rebanho_sub_fluxo"] = 5
                            if contexto["registros_animais"]:
                                resposta = "🐄 **Seus Animais Cadastrados:** 🐄\n"
                                for i, animal in enumerate(contexto["registros_animais"]):
                                    animal_id = animal.get("animal_id", "N/A")
                                    resposta += f"{i+1}. {animal_id.capitalize()}\n"
                            else:
                                resposta = f"Você ainda não cadastrou nenhum animal, {nome}. Que tal cadastrar um novo animal? 🐮"
                            resposta += "\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        elif mensagem_recebida.strip() == "6":
                            contexto["gestao_rebanho_sub_fluxo"] = 6
                            contexto["gerar_relatorio_rebanho_ativo"] = True
                            if contexto["registros_animais"]:
                                resposta = "📊 **Relatório Detalhado do Rebanho:** 📊\n\n"
                                for i, animal in enumerate(contexto["registros_animais"]):
                                    animal_id = animal.get("animal_id", "N/A")
                                    vacinas_animal = [v for v in contexto["registros_vacinacao"] if v.get("animal_id", "").lower() == animal_id.lower()]
                                    vermifugos_animal = [v for v in contexto["registros_vermifugacao"] if v.get("animal_id", "").lower() == animal_id.lower()]

                                    resposta += f"--- Animal {i+1} ---\n"
                                    resposta += f"Identificação: {animal_id.capitalize()}\n"
                                    
                                    if vacinas_animal:
                                        resposta += "Vacinações:\n"
                                        for vac in vacinas_animal:
                                            resposta += f"  - {vac.get('vacina', 'N/A')} em {vac.get('data_vacinacao', 'N/A')}\n"
                                    else:
                                        resposta += "Vacinações: Nenhuma registrada.\n"
                                    
                                    if vermifugos_animal:
                                        resposta += "Vermifugações:\n"
                                        for verm in vermifugos_animal:
                                            resposta += f"  - {verm.get('vermifugo', 'N/A')} em {verm.get('data_vermifugacao', 'N/A')}\n"
                                    else:
                                        resposta += "Vermifugações: Nenhuma registrada.\n"
                                    resposta += "\n"
                                
                                resposta += (
                                    "Este é um resumo textual. Se você esperava um relatório em formato de imagem (gráfico), PDF, Word ou Excel, "
                                    "informo que, no momento, nosso sistema via WhatsApp só consegue enviar relatórios em texto. "
                                    "Para outros formatos, seria necessário acessar nossa plataforma web.\n\n"
                                )
                            else:
                                resposta = f"Não há animais registrados para gerar um relatório, {nome}. Que tal cadastrar um novo animal? 🐮"
                            
                            resposta += "\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        else:
                            resposta = (
                                f"Opção inválida, {nome}. Por favor, escolha uma das opções para Gestão de Rebanho: 🐄\n"
                                "1. Cadastrar novo animal\n"
                                "2. Controle de vacinação e vermifugação\n"
                                "3. Controle reprodutivo\n"
                                "4. Histórico de pesagens\n"
                                "5. Consultar Animais\n"
                                "6. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (gestão rebanho sub-menu): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif cadastro_animal_ativo:
                        print(f"DEBUG_FLOW: Fluxo: cadastro_animal_ativo")
                        if "voltar" in mensagem_recebida:
                            contexto["cadastro_animal_ativo"] = False
                            contexto["registro_animal_etapa"] = None
                            contexto["dados_animal_registro"] = {}
                            contexto["gestao_rebanho_sub_fluxo"] = None
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Gestão de Rebanho. 🐄\n\n"
                                "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                                "Digite:\n"
                                "1. Cadastrar novo animal\n"
                                "2. Controle de vacinação e vermifugação\n"
                                "3. Controle reprodutivo\n"
                                "4. Histórico de pesagens\n"
                                "5. Consultar Animais\n"
                                "6. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (cadastro animal voltar): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        if registro_animal_etapa == 1:
                            dados_animal_registro["animal_id"] = mensagem_recebida.strip()
                            contexto["registro_animal_etapa"] = None
                            contexto["cadastro_animal_ativo"] = False
                            contexto["gestao_rebanho_sub_fluxo"] = None
                            # Verifica se o animal já está cadastrado
                            if any(animal.get("animal_id", "").lower() == dados_animal_registro["animal_id"].lower() for animal in contexto["registros_animais"]):
                                resposta = f"O animal '{dados_animal_registro['animal_id'].capitalize()}' já está cadastrado, {nome}. Por favor, informe um nome ou identificação diferente ou digite 'voltar'. 🐮\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                            else:
                                contexto["registros_animais"].append(dados_animal_registro)
                                resposta = f"✅ Animal '{dados_animal_registro['animal_id'].capitalize()}' cadastrado com sucesso, {nome}! 🎉"
                                resposta += f"\n\nO que você gostaria de fazer agora na Gestão de Rebanho, {nome}? 🐄\n\nDigite:\n1. Cadastrar novo animal\n2. Controle de vacinação e vermifugação\n3. Controle reprodutivo\n4. Histórico de pesagens\n5. Consultar Animais\n6. Gerar Relatório\nOu 'voltar' para o menu principal."
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (cadastro animal): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif vacinacao_vermifugacao_ativo:
                        print(f"DEBUG_FLOW: Fluxo: vacinacao_vermifugacao_ativo")
                        if "voltar" in mensagem_recebida:
                            if registro_vacinacao_etapa is not None or consulta_vacinacao_ativa or registro_vermifugacao_etapa is not None or consulta_vermifugacao_ativa or lembretes_vacinacao_ativa:
                                contexto["registro_vacinacao_etapa"] = None
                                contexto["dados_vacinacao_registro"] = {}
                                contexto["consulta_vacinacao_ativa"] = False
                                contexto["awaiting_animal_id_consulta_vac"] = False
                                contexto["registro_vermifugacao_etapa"] = None
                                contexto["dados_vermifugacao_registro"] = {}
                                contexto["consulta_vermifugacao_ativa"] = False
                                contexto["awaiting_animal_id_consulta_verm"] = False
                                contexto["lembretes_vacinacao_ativa"] = False
                                contexto["awaiting_lembretes_contato"] = False
                                contexto["vacinacao_vermifugacao_opcao"] = None
                                resposta = (
                                    f"Ok, {nome}, retornando ao menu de Vacinação e Vermifugação. 💉🐛\n"
                                    "O que você gostaria de fazer?\n\n"
                                    "Digite:\n"
                                    "1. Registrar vacinação\n"
                                    "2. Consultar vacinação\n"
                                    "3. Registrar vermifugação\n"
                                    "4. Consultar vermifugação\n"
                                    "5. Receber lembretes futuros\n"
                                    "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                )
                            else:
                                contexto["vacinacao_vermifugacao_ativo"] = False
                                contexto["gestao_rebanho_sub_fluxo"] = None
                                resposta = (
                                    f"Ok, {nome}, retornando ao menu de Gestão de Rebanho. 🐄\n\n"
                                    "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                                    "Digite:\n"
                                    "1. Cadastrar novo animal\n"
                                    "2. Controle de vacinação e vermifugação\n"
                                    "3. Controle reprodutivo\n"
                                    "4. Histórico de pesagens\n"
                                    "5. Consultar Animais\n"
                                    "6. Gerar Relatório\n"
                                    "Ou 'voltar' para o menu principal."
                                )
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (vac/verm voltar): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        if vacinacao_vermifugacao_opcao is None:
                            if mensagem_recebida.strip() == "1":
                                contexto["vacinacao_vermifugacao_opcao"] = 1
                                contexto["registro_vacinacao_etapa"] = 1
                                contexto["dados_vacinacao_registro"] = {}
                                resposta = f"✅ Informe o nome ou identificação do animal para vacinação, {nome}: 🐮\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif mensagem_recebida.strip() == "2":
                                contexto["vacinacao_vermifugacao_opcao"] = 2
                                contexto["consulta_vacinacao_ativa"] = True
                                contexto["awaiting_animal_id_consulta_vac"] = True
                                resposta = f"✅ Informe o nome ou identificação do animal que deseja consultar, {nome}: 🔍\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif mensagem_recebida.strip() == "3":
                                contexto["vacinacao_vermifugacao_opcao"] = 3
                                contexto["registro_vermifugacao_etapa"] = 1
                                contexto["dados_vermifugacao_registro"] = {}
                                resposta = f"✅ Informe o nome ou identificação do animal para vermifugação, {nome}: 🐛\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif mensagem_recebida.strip() == "4":
                                contexto["vacinacao_vermifugacao_opcao"] = 4
                                contexto["consulta_vermifugacao_ativa"] = True
                                contexto["awaiting_animal_id_consulta_verm"] = True
                                resposta = f"✅ Informe o nome ou identificação do animal que deseja consultar para vermifugação, {nome}: 🔍\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif mensagem_recebida.strip() == "5":
                                contexto["vacinacao_vermifugacao_opcao"] = 5
                                contexto["lembretes_vacinacao_ativa"] = True
                                contexto["awaiting_lembretes_contato"] = True
                                resposta = f"✅ Pronto, {nome}! Você receberá lembretes sempre que um reforço de vacinação estiver próximo. 🐮📩"
                            else:
                                resposta = (
                                    f"Opção inválida, {nome}. Por favor, escolha uma das opções para Vacinação e Vermifugação: 💉🐛\n"
                                    "1. Registrar vacinação\n"
                                    "2. Consultar vacinação\n"
                                    "3. Registrar vermifugação\n"
                                    "4. Consultar vermifugação\n"
                                    "5. Receber lembretes futuros\n"
                                    "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                )
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (vac/verm sub-menu choice): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif vacinacao_vermifugacao_opcao == 1:
                            print(f"DEBUG_FLOW: Fluxo: registro_vacinacao_etapa {registro_vacinacao_etapa}")
                            if registro_vacinacao_etapa == 1:
                                animal_id_vac = mensagem_recebida.strip()
                                # Verifica se o animal está cadastrado
                                if not any(animal.get("animal_id", "").lower() == animal_id_vac.lower() for animal in contexto["registros_animais"]):
                                    resposta = f"O animal '{animal_id_vac.capitalize()}' não está cadastrado, {nome}. Por favor, cadastre o animal primeiro ou informe um animal já cadastrado.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                dados_vacinacao_registro["animal_id"] = animal_id_vac
                                contexto["registro_vacinacao_etapa"] = 2
                                resposta = f"✅ Qual foi a vacina aplicada, {nome}? 💉\nEx.: Aftosa, Brucelose, Raiva...\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vacinacao_etapa == 2:
                                dados_vacinacao_registro["vacina"] = mensagem_recebida.strip()
                                contexto["registro_vacinacao_etapa"] = 3
                                resposta = f"✅ Qual a data da vacinação, {nome}? (dd/mm/aaaa) 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vacinacao_etapa == 3:
                                if not is_valid_date(mensagem_recebida.strip()):
                                    resposta = f"Data inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2024). 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                dados_vacinacao_registro["data_vacinacao"] = mensagem_recebida.strip()
                                contexto["registro_vacinacao_etapa"] = 4
                                resposta = f"✅ Quando será a próxima dose ou reforço, {nome}? 🗓️\nEx.: 27/11/2025\n(Se não houver, responda \"não\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vacinacao_etapa == 4:
                                proxima_dose = mensagem_recebida.strip()
                                if proxima_dose != "não" and not is_valid_date(proxima_dose):
                                    resposta = f"Data inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2024) ou responda 'não'. 🗓️\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                dados_vacinacao_registro["proxima_dose"] = proxima_dose if proxima_dose != "não" else "Não informado"
                                
                                contexto["registros_vacinacao"].append(dados_vacinacao_registro)

                                contexto["registro_vacinacao_etapa"] = None
                                contexto["vacinacao_vermifugacao_opcao"] = None
                                
                                animal_id = dados_vacinacao_registro.get("animal_id", "N/A")
                                vacina = dados_vacinacao_registro.get("vacina", "N/A")
                                data_vacinacao = dados_vacinacao_registro.get("data_vacinacao", "N/A")
                                proxima_dose_msg = dados_vacinacao_registro.get("proxima_dose", "N/A")

                                resposta = f"""🐄 **Registro de Vacinação, {nome}** 🐄
✅ Animal: {animal_id.capitalize()}
✅ Vacina: {vacina.capitalize()}
✅ Data: {data_vacinacao}
✅ Próxima dose: {proxima_dose_msg}
💉 Lembrete agendado para a próxima vacinação. 🎉"""
                                
                                resposta += f"\n\nO que deseja fazer agora na seção de Vacinação e Vermifugação, {nome}? 💉🐛\nDigite:\n1. Registrar outra vacinação\n2. Consultar vacinação\n3. Registrar vermifugação\n4. Consultar vermifugação\n5. Receber lembretes futuros\nOu 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                contexto["awaiting_post_completion_response"] = True
                                
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (registro vacinação etapa {registro_vacinacao_etapa}): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        
                        elif vacinacao_vermifugacao_opcao == 2:
                            print(f"DEBUG_FLOW: Fluxo: consulta_vacinacao_ativa")
                            if awaiting_animal_id_consulta_vac:
                                animal_id_consulta = mensagem_recebida.strip()
                                # Verifica se o animal está cadastrado
                                if not any(animal.get("animal_id", "").lower() == animal_id_consulta.lower() for animal in contexto["registros_animais"]):
                                    resposta = f"O animal '{animal_id_consulta.capitalize()}' não está cadastrado, {nome}. Por favor, cadastre o animal primeiro ou informe um animal já cadastrado.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200

                                contexto["awaiting_animal_id_consulta_vac"] = False
                                
                                historico_animal = [
                                    reg for reg in contexto["registros_vacinacao"]
                                    if reg.get("animal_id", "").lower() == animal_id_consulta.lower()
                                ]

                                if historico_animal:
                                    resposta = f"🐄 **Histórico de Vacinação - {animal_id_consulta.capitalize()}** 🐄\n"
                                    for i, reg in enumerate(historico_animal):
                                        vacina = reg.get("vacina", "N/A")
                                        data_vacinacao = reg.get("data_vacinacao", "N/A")
                                        proxima_dose = reg.get("proxima_dose", "N/A")
                                        resposta += f"{i+1}. {vacina.capitalize()} - {data_vacinacao} → Próxima: {proxima_dose}\n"
                                else:
                                    resposta = f"Não encontrei registros de vacinação para o animal '{animal_id_consulta.capitalize()}', {nome}. 🙁"
                                
                                resposta += f"\n✅ Deseja consultar outro animal, {nome}? Digite `sim` ou `não`.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                contexto["consulta_vacinacao_ativa"] = False
                                contexto["vacinacao_vermifugacao_opcao"] = None
                                contexto["awaiting_post_completion_response"] = True
                            
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (consulta vacinação): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif vacinacao_vermifugacao_opcao == 3:
                            print(f"DEBUG_FLOW: Fluxo: registro_vermifugacao_etapa {registro_vermifugacao_etapa}")
                            if registro_vermifugacao_etapa == 1:
                                animal_id_verm = mensagem_recebida.strip()
                                # Verifica se o animal está cadastrado
                                if not any(animal.get("animal_id", "").lower() == animal_id_verm.lower() for animal in contexto["registros_animais"]):
                                    resposta = f"O animal '{animal_id_verm.capitalize()}' não está cadastrado, {nome}. Por favor, cadastre o animal primeiro ou informe um animal já cadastrado.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                dados_vermifugacao_registro["animal_id"] = animal_id_verm
                                contexto["registro_vermifugacao_etapa"] = 2
                                resposta = f"✅ Qual foi o vermífugo aplicado, {nome}? 🐛\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vermifugacao_etapa == 2:
                                dados_vermifugacao_registro["vermifugo"] = mensagem_recebida.strip()
                                contexto["registro_vermifugacao_etapa"] = 3
                                resposta = f"✅ Qual a data da vermifugação, {nome}? (dd/mm/aaaa) 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vermifugacao_etapa == 3:
                                if not is_valid_date(mensagem_recebida.strip()):
                                    resposta = f"Data inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2024). 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                dados_vermifugacao_registro["data_vermifugacao"] = mensagem_recebida.strip()
                                contexto["registro_vermifugacao_etapa"] = 4
                                resposta = f"✅ Quando será a próxima dose ou reforço, {nome}? 🗓️ (Se não houver, responda \"não\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vermifugacao_etapa == 4:
                                proxima_dose_verm = mensagem_recebida.strip()
                                if proxima_dose_verm != "não" and not is_valid_date(proxima_dose_verm):
                                    resposta = f"Data inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2024) ou responda 'não'. 🗓️\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                dados_vermifugacao_registro["proxima_dose"] = proxima_dose_verm if proxima_dose_verm != "não" else "Não informado"
                                
                                contexto["registros_vermifugacao"].append(dados_vermifugacao_registro)

                                contexto["registro_vermifugacao_etapa"] = None
                                contexto["vacinacao_vermifugacao_opcao"] = None
                                
                                animal_id = dados_vermifugacao_registro.get("animal_id", "N/A")
                                vermifugo = dados_vermifugacao_registro.get("vermifugo", "N/A")
                                data_vermifugacao = dados_vermifugacao_registro.get("data_vermifugacao", "N/A")
                                proxima_dose_msg = dados_vermifugacao_registro.get("proxima_dose", "N/A")

                                resposta = f"""🐛 **Registro de Vermifugação, {nome}** 🐛
✅ Animal: {animal_id.capitalize()}
✅ Vermífugo: {vermifugo.capitalize()}
✅ Data: {data_vermifugacao}
✅ Próxima dose: {proxima_dose_msg}"""
                                
                                resposta += f"\n\nO que deseja fazer agora na seção de Vacinação e Vermifugação, {nome}? 💉🐛\nDigite:\n1. Registrar vacinação\n2. Consultar vacinação\n3. Registrar vermifugação\n4. Consultar vermifugação\n5. Receber lembretes futuros\nOu 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                contexto["awaiting_post_completion_response"] = True
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (registro vermifugação etapa {registro_vermifugacao_etapa}): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif vacinacao_vermifugacao_opcao == 4:
                            print(f"DEBUG_FLOW: Fluxo: consulta_vermifugacao_ativa")
                            if awaiting_animal_id_consulta_verm:
                                animal_id_consulta = mensagem_recebida.strip()
                                # Verifica se o animal está cadastrado
                                if not any(animal.get("animal_id", "").lower() == animal_id_consulta.lower() for animal in contexto["registros_animais"]):
                                    resposta = f"O animal '{animal_id_consulta.capitalize()}' não está cadastrado, {nome}. Por favor, cadastre o animal primeiro ou informe um animal já cadastrado.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200

                                contexto["awaiting_animal_id_consulta_verm"] = False
                                
                                historico_animal_verm = [
                                    reg for reg in contexto["registros_vermifugacao"]
                                    if reg.get("animal_id", "").lower() == animal_id_consulta.lower()
                                ]

                                if historico_animal_verm:
                                    resposta = f"🐛 **Histórico de Vermifugação - {animal_id_consulta.capitalize()}** 🐛\n"
                                    for i, reg in enumerate(historico_animal_verm):
                                        vermifugo = reg.get("vermifugo", "N/A")
                                        data_vermifugacao = reg.get("data_vermifugacao", "N/A")
                                        proxima_dose = reg.get("proxima_dose", "N/A")
                                        resposta += f"{i+1}. {vermifugo.capitalize()} - {data_vermifugacao} → Próxima: {proxima_dose}\n"
                                else:
                                    resposta = f"Não encontrei registros de vermifugação para o animal '{animal_id_consulta.capitalize()}', {nome}. 🙁"
                                
                                resposta += f"\n✅ Deseja consultar outro animal, {nome}? Digite `sim` ou `não`.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                contexto["consulta_vermifugacao_ativa"] = False
                                contexto["vacinacao_vermifugacao_opcao"] = None
                                contexto["awaiting_post_completion_response"] = True
                            
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (consulta vermifugação): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif vacinacao_vermifugacao_opcao == 5:
                            print(f"DEBUG_FLOW: Fluxo: lembretes_vacinacao_ativa")
                            if awaiting_lembretes_contato:
                                contato_lembretes = mensagem_recebida.strip()
                                contexto["contato_lembretes"] = contato_lembretes
                                contexto["awaiting_lembretes_contato"] = False
                                contexto["lembretes_vacinacao_ativa"] = False
                                
                                resposta = f"✅ Pronto, {nome}! Você receberá lembretes sempre que um reforço de vacinação estiver próximo. 🐮📩"
                                
                                resposta += f"\n\nO que deseja fazer agora na seção de Vacinação e Vermifugação, {nome}? 💉🐛\nDigite:\n1. Registrar vacinação\n2. Consultar vacinação\n3. Registrar vermifugação\n4. Consultar vermifugação\n5. Receber lembretes futuros\nOu 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                contexto["awaiting_post_completion_response"] = True
                            
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (lembretes vacinação): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        
                        else:
                            resposta = f"Ocorreu um erro no fluxo de vacinação/vermifugação, {nome}. Por favor, digite '2' para voltar ao menu de Vacinação e Vermifugação ou 'menu' para voltar ao menu principal."
                            contexto["vacinacao_vermifugacao_ativo"] = True
                            contexto["vacinacao_vermifugacao_opcao"] = None
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (erro vac/verm sub-fluxo): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif controle_reprodutivo_ativo:
                        print(f"DEBUG_FLOW: Fluxo: controle_reprodutivo_ativo")
                        if "voltar" in mensagem_recebida:
                            contexto["controle_reprodutivo_ativo"] = False
                            contexto["gestao_rebanho_sub_fluxo"] = None
                            contexto["gerar_relatorio_rebanho_ativo"] = False
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Gestão de Rebanho. 🐄\n\n"
                                "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                                "Digite:\n"
                                "1. Cadastrar novo animal\n"
                                "2. Controle de vacinação e vermifugação\n"
                                "3. Controle reprodutivo\n"
                                "4. Histórico de pesagens\n"
                                "5. Consultar Animais\n"
                                "6. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (controle reprodutivo voltar): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        resposta = f"Você está no fluxo de Controle Reprodutivo, {nome}. Em breve teremos mais funcionalidades aqui! 🤰\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                        contexto["awaiting_post_completion_response"] = True
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (controle reprodutivo): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif historico_pesagens_ativo:
                        print(f"DEBUG_FLOW: Fluxo: historico_pesagens_ativo")
                        if "voltar" in mensagem_recebida:
                            contexto["historico_pesagens_ativo"] = False
                            contexto["gestao_rebanho_sub_fluxo"] = None
                            contexto["gerar_relatorio_rebanho_ativo"] = False
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Gestão de Rebanho. 🐄\n\n"
                                "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                                "Digite:\n"
                                "1. Cadastrar novo animal\n"
                                "2. Controle de vacinação e vermifugação\n"
                                "3. Controle reprodutivo\n"
                                "4. Histórico de pesagens\n"
                                "5. Consultar Animais\n"
                                "6. Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (histórico pesagens voltar): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        resposta = f"Você está no fluxo de Histórico de Pesagens, {nome}. Em breve teremos mais funcionalidades aqui! ⚖️\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                        contexto["awaiting_post_completion_response"] = True
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (histórico pesagens): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    else:
                        resposta = f"Ocorreu um erro no fluxo de Gestão de Rebanho, {nome}. Por favor, digite '3' para iniciar a Gestão de Rebanho ou 'menu' para voltar ao menu principal."
                        reset_all_flow_flags(contexto) # Reset all flags
                        contexto["gestao_rebanho_ativo"] = True
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (erro gestão rebanho sub-fluxo): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif registration_step:
                    print(f"DEBUG_FLOW: Fluxo: registration_step (etapa: {registration_step})")
                    current_question_key = registration_step
                    
                    if "voltar" in mensagem_recebida:
                        if contexto.get("editing_registration"):
                            contexto["current_editing_field"] = None
                            contexto["awaiting_field_to_edit"] = True
                            resposta = f"Qual campo você gostaria de editar, {nome}? (Ex: 'nome completo', 'cpf', 'endereço', etc.) 📝\n\nSe preferir, posso te mostrar seus dados atuais. Diga 'meus dados'.\n(Ou 'voltar' para o menu principal)"
                        else:
                            reset_all_flow_flags(contexto) # Reset all flags
                            resposta = (
                                f"Ok, {nome}, o cadastro foi cancelado. Retornando ao menu principal. 👋\n\n"
                                f"Escolha uma das opções abaixo para começarmos:\n"
                                f"1. Previsão Climática ☁️\n"
                                f"2. Controle de Estoque 📦\n"
                                f"3. Gestão de Rebanho 🐄\n"
                                f"4. Simulação de Safra 🌾\n"
                                f"5. {cadastro_opcao_texto} 📝\n"
                                f"6. Alertas de Pragas 🐛\n"
                                f"7. Análise de Mercado 📈\n"
                                f"8. Localização 📍\n"
                                f"9. Outras Informações 💡"
                            )
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (cadastro voltar): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    if contexto.get("editing_registration"):
                        print(f"DEBUG_FLOW: Fluxo: editing_registration")
                        if contexto.get("awaiting_field_to_edit"):
                            field_to_edit = None
                            for term, key in EDITABLE_FIELDS_MAP.items():
                                if term in mensagem_recebida:
                                    field_to_edit = key
                                    break
                            
                            if field_to_edit:
                                contexto["current_editing_field"] = field_to_edit
                                contexto["awaiting_field_to_edit"] = False
                                if field_to_edit == "email":
                                    contexto["awaiting_email_choice"] = True
                                    resposta = REGISTRATION_QUESTIONS["email"]
                                elif field_to_edit == "ponto_referencia":
                                    contexto["awaiting_ponto_referencia_choice"] = True
                                    resposta = REGISTRATION_QUESTIONS["ponto_referencia"]
                                else:
                                    resposta = f"Ok, {nome}, qual é o novo valor para '{REGISTRATION_QUESTIONS[field_to_edit].replace('Qual é seu ', '').replace('Qual o seu ', '').replace('Qual a sua ', '').replace('Qual seu ', '').replace('Qual a ', '').replace('Qual o ', '').replace('Seu ', '').replace('Tem algum ', '').replace('Sua ', '').replace('Sua produção é de que tipo?', 'tipo de produção?').replace('Sua produção é orgânica?', 'produção orgânica?').replace('Utiliza irrigação?', 'utiliza irrigação?').replace('Você pode informar várias, ex: milho, feijão, mandioca...', '')}'? ✏️\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif "meus dados" in mensagem_recebida:
                                dados_atuais = f"Seus dados de cadastro atuais, {nome}: 📋\n"
                                for key, question in REGISTRATION_QUESTIONS.items():
                                    # Formata a exibição para campos de escolha Sim/Não
                                    if key in ["email", "ponto_referencia"]:
                                        display_value = contexto.get(key, "Não preenchido")
                                        # Ajusta o prefixo da pergunta para um título mais limpo para exibição
                                        if key == "email":
                                            display_question = "E-mail"
                                        elif key == "ponto_referencia":
                                            display_question = "Ponto de referência"
                                        dados_atuais += f"- {display_question}: {display_value}\n"
                                    else:
                                        value = contexto.get(key, "Não preenchido")
                                        # Remove os "Qual é seu/sua/o" e emojis da pergunta original para exibição
                                        clean_question = question.splitlines()[0].replace('Qual é seu ', '').replace('Qual o seu ', '').replace('Qual a sua ', '').replace('Qual seu ', '').replace('Qual a ', '').replace('Qual o ', '').replace('Seu ', '').replace('Tem algum ', '').replace('Sua ', '').replace('Sua produção é de que tipo?', 'Tipo de produção?').replace('Sua produção é orgânica?', 'Produção orgânica?').replace('Utiliza irrigação?', 'Utiliza irrigação?').split("?")[0].strip() # Pega só a primeira linha, remove o '?', e limpa espaços
                                        dados_atuais += f"- {clean_question}: {value}\n"
                                resposta = f"{dados_atuais}\nQual campo você gostaria de editar agora, {nome}? Ou diga 'concluído' para finalizar a edição. ✅\n(Ou 'voltar' para o menu principal)"
                            elif "concluído" in mensagem_recebida or "concluido" in mensagem_recebida:
                                reset_all_flow_flags(contexto) # Reset all flags
                                contexto["awaiting_post_completion_response"] = True
                                resposta = f"Edição de cadastro concluída, {nome}! 🎉 Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                            else:
                                resposta = f"Não entendi qual campo você deseja editar, {nome}. Por favor, diga o nome do campo (ex: 'nome completo', 'cpf', 'email') ou diga 'meus dados' para ver o que já está preenchido. 🤔\n(Ou 'voltar' para o menu principal)"
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (edição de cadastro): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif contexto.get("current_editing_field"):
                            field_to_update = contexto["current_editing_field"]
                            if field_to_update == "cpf":
                                if not is_valid_cpf(mensagem_recebida):
                                    resposta = f"CPF inválido, {nome}. Por favor, digite um CPF válido (apenas 11 números). 🔢\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                else:
                                    contexto[field_to_update] = re.sub(r'\D', '', mensagem_recebida)
                            elif field_to_update == "rg":
                                if not is_valid_rg(mensagem_recebida):
                                    resposta = f"RG inválido, {nome}. Por favor, digite um RG válido. 🆔\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                else:
                                    contexto[field_to_update] = mensagem_recebida.strip()
                            elif field_to_update == "data_nascimento":
                                if not is_valid_date(mensagem_recebida.strip()):
                                    resposta = f"Data de nascimento inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2000). 🎂\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                                else:
                                    contexto[field_to_update] = mensagem_recebida.strip()
                            elif field_to_update == "estado_civil":
                                estado_civil_map = {
                                    "1": "Casado", "2": "Solteiro", "3": "Viúvo", "4": "Divorciado"
                                }
                                if mensagem_recebida.strip() in estado_civil_map:
                                    contexto[field_to_update] = estado_civil_map[mensagem_recebida.strip()]
                                else:
                                    resposta = f"Opção inválida, {nome}. Por favor, escolha uma das opções para estado civil:\n1. Casado 💍\n2. Solteiro 🧍\n3. Viúvo 💔\n4. Divorciado 💔\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                    try: save_conversation_context(numero, contexto)
                                    except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                    send_whatsapp_message(numero, resposta)
                                    return jsonify({"status": "erro", "resposta": resposta}), 200
                            else:
                                contexto[field_to_update] = mensagem_recebida.strip()

                            contexto["current_editing_field"] = None
                            contexto["awaiting_field_to_edit"] = True
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (campo editado): {e}")
                            
                            # Formata a mensagem de confirmação de atualização
                            question_text = REGISTRATION_QUESTIONS[field_to_update].splitlines()[0]
                            # Remove "Qual é seu/sua/o", emojis e o ponto de interrogação
                            clean_question_text = re.sub(r'Qual (?:é )?s(?:eu|ua|ua)?\s', '', question_text).replace('?', '').strip()
                            clean_question_text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F900-\U0001F9FF\U0001F4C0-\U0001F4FF\U0001F1E0-\U0001F1FF]+', '', clean_question_text).strip()
                            
                            if field_to_update == "email":
                                clean_question_text = "E-mail"
                            elif field_to_update == "ponto_referencia":
                                clean_question_text = "Ponto de referência"
                            elif "produção é de que tipo" in clean_question_text.lower():
                                clean_question_text = "Tipo de produção"
                            elif "produção é orgânica" in clean_question_text.lower():
                                clean_question_text = "Produção orgânica"
                            elif "utiliza irrigação" in clean_question_text.lower():
                                clean_question_text = "Utiliza irrigação"

                            resposta = f"'{clean_question_text}' atualizado para: {mensagem_recebida.strip()}, {nome}. ✅\n\nDeseja editar outro campo ou diga 'concluído' para finalizar a edição? 🤔\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        else:
                            contexto["awaiting_field_to_edit"] = True
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (início da edição): {e}")
                            resposta = f"Qual campo você gostaria de editar, {nome}? (Ex: 'nome completo', 'cpf', 'endereço', etc.) 📝\n\nSe preferir, posso te mostrar seus dados atuais. Diga 'meus dados'.\n(Ou 'voltar' para o menu principal)"
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                    
                    elif awaiting_email_choice:
                        if mensagem_recebida.strip() == "1" or "sim" in mensagem_recebida:
                            contexto["email_choice_made"] = "sim"
                            contexto["awaiting_email_choice"] = False
                            contexto["awaiting_email_value_input"] = True
                            resposta = "Por favor, digite seu endereço de e-mail: 📧"
                        elif mensagem_recebida.strip() == "2" or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                            contexto["email"] = "Não informado"
                            contexto["email_choice_made"] = "nao"
                            contexto["awaiting_email_choice"] = False
                            next_question_key = get_next_registration_question_key(contexto)
                            if next_question_key:
                                contexto["registration_step"] = next_question_key
                                resposta = REGISTRATION_QUESTIONS[next_question_key]
                            else:
                                contexto["registration_step"] = None
                                contexto["awaiting_post_completion_response"] = True
                                resposta = f"Cadastro concluído com sucesso, {nome}! 🎉 Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                        else:
                            resposta = "Não entendi. Por favor, diga '1' para Sim ou '2' para Não."
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (email choice): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif awaiting_email_value_input:
                        contexto["email"] = mensagem_recebida.strip()
                        contexto["awaiting_email_value_input"] = False
                        next_question_key = get_next_registration_question_key(contexto)
                        if next_question_key:
                            contexto["registration_step"] = next_question_key
                            resposta = REGISTRATION_QUESTIONS[next_question_key]
                        else:
                            contexto["registration_step"] = None
                            contexto["awaiting_post_completion_response"] = True
                            resposta = f"Cadastro concluído com sucesso, {nome}! 🎉 Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (email value): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif awaiting_ponto_referencia_choice:
                        if mensagem_recebida.strip() == "1" or "sim" in mensagem_recebida:
                            contexto["ponto_referencia_choice_made"] = "sim"
                            contexto["awaiting_ponto_referencia_choice"] = False
                            contexto["awaiting_ponto_referencia_value_input"] = True
                            resposta = "Por favor, descreva o ponto de referência: 🗺️"
                        elif mensagem_recebida.strip() == "2" or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                            contexto["ponto_referencia"] = "Não informado"
                            contexto["ponto_referencia_choice_made"] = "nao"
                            contexto["awaiting_ponto_referencia_choice"] = False
                            next_question_key = get_next_registration_question_key(contexto)
                            if next_question_key:
                                contexto["registration_step"] = next_question_key
                                resposta = REGISTRATION_QUESTIONS[next_question_key]
                            else:
                                contexto["registration_step"] = None
                                contexto["awaiting_post_completion_response"] = True
                                resposta = f"Cadastro concluído com sucesso, {nome}! 🎉 Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                        else:
                            resposta = "Não entendi. Por favor, diga '1' para Sim ou '2' para Não."
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (ponto_referencia choice): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif awaiting_ponto_referencia_value_input:
                        contexto["ponto_referencia"] = mensagem_recebida.strip()
                        contexto["awaiting_ponto_referencia_value_input"] = False
                        next_question_key = get_next_registration_question_key(contexto)
                        if next_question_key:
                            contexto["registration_step"] = next_question_key
                            resposta = REGISTRATION_QUESTIONS[next_question_key]
                        else:
                            contexto["registration_step"] = None
                            contexto["awaiting_post_completion_response"] = True
                            resposta = f"Cadastro concluído com sucesso, {nome}! 🎉 Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (ponto_referencia value): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    else:
                        if current_question_key == "cpf":
                            if not is_valid_cpf(mensagem_recebida):
                                resposta = f"CPF inválido, {nome}. Por favor, digite um CPF válido (apenas 11 números). 🔢\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                            else:
                                contexto[current_question_key] = re.sub(r'\D', '', mensagem_recebida)
                        elif current_question_key == "rg":
                            if not is_valid_rg(mensagem_recebida):
                                resposta = f"RG inválido, {nome}. Por favor, digite um RG válido. 🆔\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                            else:
                                contexto[current_question_key] = mensagem_recebida.strip()
                        elif current_question_key == "data_nascimento":
                            if not is_valid_date(mensagem_recebida.strip()):
                                resposta = f"Data de nascimento inválida, {nome}. Por favor, digite a data no formato dd/mm/aaaa (ex: 01/01/2000). 🎂\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                            else:
                                contexto[current_question_key] = mensagem_recebida.strip()
                        elif current_question_key == "estado_civil":
                            estado_civil_map = {
                                "1": "Casado", "2": "Solteiro", "3": "Viúvo", "4": "Divorciado"
                            }
                            if mensagem_recebida.strip() in estado_civil_map:
                                contexto[current_question_key] = estado_civil_map[mensagem_recebida.strip()]
                            else:
                                resposta = f"Opção inválida, {nome}. Por favor, escolha uma das opções para estado civil:\n1. Casado 💍\n2. Solteiro 🧍\n3. Viúvo 💔\n4. Divorciado 💔\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                try: save_conversation_context(numero, contexto)
                                except Exception as e: print(f"DEBUG_FLOW_SAVE_ERROR: {e}"); send_whatsapp_message(numero, "Erro ao salvar."); return jsonify({"status": "erro"}), 500
                                send_whatsapp_message(numero, resposta)
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                        else:
                            contexto[current_question_key] = mensagem_recebida.strip()
                        
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (cadastro etapa {current_question_key}): {e}")

                        next_question_key = get_next_registration_question_key(contexto)
                        
                        if next_question_key:
                            contexto["registration_step"] = next_question_key
                            if next_question_key == "email_choice":
                                resposta = REGISTRATION_QUESTIONS["email"]
                            elif next_question_key == "ponto_referencia_choice":
                                resposta = REGISTRATION_QUESTIONS["ponto_referencia"]
                            else:
                                resposta = REGISTRATION_QUESTIONS[next_question_key]
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (próxima etapa cadastro): {e}")
                            send_whatsapp_message(numero, resposta)
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        else:
                            reset_all_flow_flags(contexto) # Reset all flags
                            contexto["awaiting_post_completion_response"] = True
                            try:
                                save_conversation_context(numero, contexto)
                            except Exception as e:
                                print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (cadastro concluído): {e}")
                            resposta = f"Cadastro concluído com sucesso, {nome}! 🎉 Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200
                
                elif awaiting_weather_location:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_weather_location")
                    city_match_explicit = re.search(r"(?:clima|previsão|tempo)\s+(?:em|para)\s+([a-zA-Z\u00C0-\u017F\s-]+)", mensagem_recebida)
                    cidade_solicitada_from_message = ""

                    if mensagem_recebida.strip() and not mensagem_recebida.strip().isdigit():
                        cidade_solicitada_from_message = mensagem_recebida.strip()
                    
                    if city_match_explicit:
                        cidade_solicitada_from_message = city_match_explicit.group(1).strip()

                    if cidade_solicitada_from_message:
                        pais_solicitado = "BR"
                        resposta_clima = format_weather_response(cidade_solicitada_from_message, pais_solicitado)
                        reset_all_flow_flags(contexto) # Reset all flags
                        contexto["awaiting_weather_follow_up_choice"] = True # Only set this flag
                        contexto["localizacao"] = {"cidade": cidade_solicitada_from_message, "estado": "", "pais": pais_solicitado}
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (clima por cidade): {e}")
                        send_whatsapp_message(numero, resposta_clima)
                        return jsonify({"status": "sucesso", "resposta": resposta_clima}), 200
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, me diga o nome da cidade (ex: 'São Paulo') ou compartilhe sua localização atual pelo WhatsApp. 📍\n(Ou 'voltar' para o menu principal)"
                        try:
                            save_conversation_context(numero, contexto)
                        except Exception as e:
                            print(f"DEBUG_FLOW_SAVE_ERROR: Erro ao salvar contexto (re-prompt localização): {e}")
                        send_whatsapp_message(numero, resposta)
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # Handle Main Menu Options
                elif mensagem_recebida.strip() == "1" or "clima" in mensagem_recebida or "previsão climática" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 1 - Previsão Climática selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    if localizacao and localizacao.get("cidade"):
                        cidade_salva = localizacao["cidade"]
                        pais_salvo = localizacao["pais"]
                        resposta = format_weather_response(cidade_salva, pais_salvo)
                        contexto["awaiting_weather_follow_up_choice"] = True
                    else:
                        resposta = f"Para qual cidade você gostaria da previsão climática, {nome}? Você também pode compartilhar sua localização. 📍\n(Ou 'voltar' para o menu principal)"
                        contexto["awaiting_weather_location"] = True
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 1): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida.strip() == "2" or "controle de estoque" in mensagem_recebida or "estoque" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 2 - Controle de Estoque selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    contexto["controle_estoque_ativo"] = True
                    resposta = (
                        f"Bem-vindo ao Controle de Estoque, {nome}! 📦\n\n"
                        "O que você gostaria de fazer?\n\n"
                        "1. Registrar Entrada de Insumos/Produtos\n"
                        "2. Registrar Saída de Insumos/Produtos\n"
                        "3. Consultar Estoque\n"
                        "4. Avisos de estoque baixo\n"
                        "5. Gerar Relatório\n"
                        "Ou 'voltar' para o menu principal."
                    )
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 2 - controle de estoque): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida.strip() == "3" or "gestão de rebanho" in mensagem_recebida or "gestao de rebanho" in mensagem_recebida or "rebanho" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 3 - Gestão de Rebanho selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    contexto["gestao_rebanho_ativo"] = True
                    resposta = (
                        f"Bem-vindo à Gestão de Rebanho, {nome}! 🐄\n\n"
                        "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                        "Digite:\n"
                        "1. Cadastrar novo animal\n"
                        "2. Controle de vacinação e vermifugação\n"
                        "3. Controle reprodutivo\n"
                        "4. Histórico de pesagens\n"
                        "5. Consultar Animais\n"
                        "6. Gerar Relatório\n"
                        "Ou 'voltar' para o menu principal."
                    )
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 3 - gestão de rebanho): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida.strip() == "4" or "simulação de safra" in mensagem_recebida or "safra" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 4 - Simulação de Safra selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    contexto["simulacao_safra_ativa"] = True
                    resposta = (
                        f"Bem-vindo à Simulação de Safra, {nome}! 🌾\n\n"
                        "O que você gostaria de fazer?\n\n"
                        "1. Iniciar nova simulação\n"
                        "2. Consultar Simulações Anteriores\n"
                        "3. Gerar Relatório\n"
                        "Ou 'voltar' para o menu principal."
                    )
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 4 - simulação de safra): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida.strip() == "5" or "cadastro" in mensagem_recebida or "cadastra-se" in mensagem_recebida or "editar dados" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 5 - Cadastro/Editar selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    if usuario_cadastrado:
                        contexto["registration_step"] = "nome_completo" # Reinicia o passo de cadastro para que o get_next_registration_question_key funcione
                        contexto["editing_registration"] = True
                        resposta = f"Entendido, {nome}! Você deseja editar seus dados de cadastro. Qual campo você gostaria de editar? (Ex: 'nome completo', 'cpf', 'endereço', etc.) 📝\n\nSe preferir, posso te mostrar seus dados atuais. Diga 'meus dados'.\n(Ou 'voltar' para o menu principal)"
                    else:
                        contexto["registration_step"] = REGISTRATION_ORDER[0]
                        resposta = f"Ótimo, {nome}! Vamos começar seu cadastro. {REGISTRATION_QUESTIONS[contexto['registration_step']]}\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 5 - cadastrar/editar): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida.strip() == "6" or "alertas" in mensagem_recebida or "pragas" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 6 - Alertas de Pragas selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    contexto["awaiting_menu_return_prompt"] = True # Set flag to expect return to menu prompt
                    resposta = f"Em breve teremos alertas de pragas para a sua região, {nome}! Fique ligado! 🐛\nDeseja voltar ao menu principal? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu principal)"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 6): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida.strip() == "7" or "análise de mercado" in mensagem_recebida or "mercado" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 7 - Análise de Mercado selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    contexto["awaiting_menu_return_prompt"] = True # Set flag to expect return to menu prompt
                    resposta = f"Em breve teremos análises de mercado para te ajudar a tomar as melhores decisões, {nome}! Aguarde! 📈\nDeseja voltar ao menu principal? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu principal)"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 7): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida.strip() == "8" or "localização" in mensagem_recebida or "minha localização" in mensagem_recebida or "onde estou" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 8 - Localização selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    local = obter_localizacao_via_ip()
                    if "erro" in local:
                        resposta = f"Desculpe, {nome}, não consegui determinar sua localização atual. Por favor, tente compartilhar sua localização pelo WhatsApp ou digite o nome da sua cidade para que eu possa ajudar. 📍\n(Ou 'voltar' para o menu principal)"
                        contexto["awaiting_weather_location"] = True
                    else:
                        cidade = local.get("cidade", "N/A")
                        estado = local.get("estado", "N/A")
                        pais = local.get("pais", "N/A")
                        resposta = f"Sua localização atual é: {cidade}, {estado}, {pais}. 🌍\n\nDeseja voltar ao menu principal? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu principal)"
                        contexto["awaiting_menu_return_prompt"] = True
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 8): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida.strip() == "9" or "outras informações" in mensagem_recebida or "outras informacoes" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 9 - Outras Informações selecionada.")
                    reset_all_flow_flags(contexto) # Reset all flags
                    contexto["awaiting_menu_return_prompt"] = True # Set flag to expect return to menu prompt
                    resposta = f"Para outras informações, você pode visitar nosso site em www.campointeligente.com.br ou entrar em contato com nosso suporte técnico. 💡\n\nDeseja voltar ao menu principal? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu principal)"
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_MAIN_MENU_SAVE_ERROR: Erro ao salvar contexto (opção 9): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                else:
                    print(f"DEBUG_FALLBACK: Mensagem não reconhecida: '{mensagem_recebida}'")
                    resposta = (
                        f"Desculpe, {nome}, não entendi sua mensagem. 🤔\n"
                        f"Por favor, escolha uma das opções do menu principal ou diga 'menu' para vê-las novamente:\n"
                        f"1. Previsão Climática ☁️\n"
                        f"2. Controle de Estoque 📦\n"
                        f"3. Gestão de Rebanho 🐄\n"
                        f"4. Simulação de Safra 🌾\n"
                        f"5. {cadastro_opcao_texto} 📝\n"
                        f"6. Alertas de Pragas 🐛\n"
                        f"7. Análise de Mercado 📈\n"
                        f"8. Localização 📍\n"
                        f"9. Outras Informações 💡"
                    )
                    try:
                        save_conversation_context(numero, contexto)
                    except Exception as e:
                        print(f"DEBUG_FALLBACK_SAVE_ERROR: Erro ao salvar contexto (fallback): {e}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

            else:
                print(f"DEBUG_WEBHOOK_END: Nenhum tipo de mensagem suportado ou mensagem vazia para {numero}.")
                return jsonify({"status": "erro", "mensagem": "Nenhum tipo de mensagem suportado ou mensagem vazia."}), 400
        else:
            print(f"DEBUG_WEBHOOK_END: Evento não suportado: {event}")
            return jsonify({"status": "erro", "mensagem": f"Evento '{event}' não suportado."}), 400

    except Exception as e:
        print(f"DEBUG_WEBHOOK_ERROR: Erro inesperado no webhook: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
