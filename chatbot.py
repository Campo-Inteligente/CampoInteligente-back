from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import locale
import os
import requests
import openpyxl
from dotenv import load_dotenv
import openai
import re
import json
import psycopg2

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
CONVERSATION_TIMEOUT_SECONDS = 180 # Alterado de 60 para 180 segundos (3 minutos)

# Inicializando a API do OpenAI
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)

# Dicionário para armazenar o contexto da conversa por número de telefone (em memória, para demonstração)
# Para persistência real, usaremos o banco de dados.
conversa_contextos = {}

# Definição das perguntas de cadastro e as chaves correspondentes no contexto
REGISTRATION_QUESTIONS = {
    "nome_completo": "Qual é seu nome completo?",
    "cpf": "Qual é seu CPF? (apenas números, por favor)",
    "rg": "Qual é seu RG?",
    "data_nascimento": "Qual sua data de nascimento? (dd/mm/aaaa)",
    "sexo": "Qual seu sexo? (Masculino, Feminino ou Outro)",
    "estado_civil": "Qual seu estado civil? (Solteiro ou Casado)",
    "telefone_contato": "Qual seu telefone para contato?",
    "email": "Qual seu e-mail? (opcional)",  # Campo opcional

    "endereco_tipo": "Seu endereço é rural ou urbano?",
    "nome_propriedade": "Qual o nome da propriedade (se houver)?",
    "comunidade_bairro": "Qual a comunidade ou bairro?",
    "municipio": "Qual o município?",
    "estado_propriedade": "Qual o estado? (ex: BA, SP, MG...)",
    "cep": "Qual o CEP?",
    "ponto_referencia": "Tem algum ponto de referência? (opcional)",  # Campo opcional

    "dap_caf": "Possui DAP ou CAF? Se sim, informe o número.",
    "tipo_producao": "Sua produção é de que tipo? (Familiar ou Empresarial)",
    "producao_organica": "Sua produção é orgânica? (Sim ou Não)",
    "utiliza_irrigacao": "Utiliza irrigação? (Sim ou Não)",
    "area_total_propriedade": "Qual a área total da propriedade (em hectares)?",
    "area_cultivada": "Qual a área cultivada (em hectares)?",
    "culturas_produzidas": "Quais culturas você produz? (Você pode informar várias, ex: milho, feijão, mandioca...)"
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
        except psycopg2.Error as e:
            print(f"DEBUG_DB_SAVE_ERROR: Erro ao salvar contexto da conversa no banco de dados para {phone_number}: {e}")
        finally:
            if conn:
                conn.close()
    else:
        print(f"DEBUG_DB_SAVE_ERROR: Conexão ao DB falhou ao salvar contexto para {phone_number}.")


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
            return resposta.status_code, resposta.json()
        else:
            print(f"DEBUG_WHATSAPP_ERROR: Falha ao enviar mensagem para {numero}. Status: {resposta.status_code}, Erro: {resposta.text}")
            return resposta.status_code, {"erro": resposta.text}
    except requests.RequestException as e:
        print(f"DEBUG_WHATSAPP_ERROR: Erro de requisição ao enviar mensagem para {numero}: {e}")
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
        "nuvens quebradas": "☁️ Nuvens quebradas", # Corrigido!
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
        "overcast clouds": "☁️ Nublado" # Adicionado para garantir a tradução
    }
    
    descricao_clima = clima_atual['descricao'].lower()
    emoji_desc = "❓ Informação não disponível" # Default fallback
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
        for dia_previsao in clima_estendido["previsao"][:2]: # Limit to 2 days for brevity
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

    # Lógica de simulação de exemplo:
    # A produtividade pode variar com base na cultura, solo e clima.
    produtividade_base = 3000 # kg/ha
    
    if "soja" in cultura.lower():
        produtividade_base = 3200
    elif "milho" in cultura.lower():
        produtividade_base = 6000
    elif "trigo" in cultura.lower():
        produtividade_base = 2500
    elif "café" in cultura.lower():
        produtividade_base = 1500 # sacas/ha (precisaria de conversão para kg)

    # Ajustes baseados no solo e clima (exemplo simplificado)
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

    # Retorno de exemplo:
    resultado = {
        "produtividade_media": round(produtividade_base),  # kg/ha
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
🌾 **Simulação de Safra - Resultado** 🌾

✅ Cultura: {cultura.capitalize()}
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
            "Gere uma resposta amigável e informativa sobre o clima e recomendações de plantio para a região, com base nos dados fornecidos.  Se o usuário perguntar sobre o clima ou o melhor plantio, forneça informações sobre o clima atual e uma recomendação de plantio concisa e apropriada para a região. Não liste toda a previsão estendida, apenas destaque o período mais favorável, se possível."
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
            # Verifica se o contexto do usuário possui TODAS as chaves de cadastro obrigatórias preenchidas
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


# Rota do webhook para receber e responder mensagens
@app.route("/webhook", methods=["POST"])
def webhook_route():
    try:
        data = request.json
        print(f"--- Webhook recebido ---")
        print(f"Dados recebidos: {data}")
        event = data.get('event')

        if event == 'messages.upsert':
            mensagem_recebida = data.get('data', {}).get('message', {}).get('conversation', '').lower()
            numero = data.get('data', {}).get('key', {}).get('remoteJid', '')

            print(f"DEBUG_WEBHOOK_START: Mensagem recebida de {numero}: '{mensagem_recebida}'")

            if mensagem_recebida and numero:
                # Carrega o contexto da conversa do banco de dados
                contexto = load_conversation_context(numero)
                print(f"DEBUG_WEBHOOK_START: Contexto carregado para {numero} no início do webhook: {contexto}")
                
                # --- Definições iniciais para evitar erros de variável não definida ---
                usuario_cadastrado = is_user_registered(numero)
                cadastro_opcao_texto = "Editar dados de cadastro" if usuario_cadastrado else "Cadastra-se"
                nome = contexto.get("nome_completo", "Usuário") # Get user's name, default to "Usuário"
                # --- Fim das definições iniciais ---

                # Extract flags from context
                localizacao = contexto.get("localizacao")
                last_interaction_time = contexto.get("last_interaction_time", 0) # Default to 0 if not set
                awaiting_weather_location = contexto.get("awaiting_weather_location", False)
                registration_step = contexto.get("registration_step", None)
                registration_interrupted_by_timeout = contexto.get("registration_interrupted_by_timeout", False)
                awaiting_continuation_choice = contexto.get("awaiting_continuation_choice", False)
                awaiting_post_completion_response = contexto.get("awaiting_post_completion_response", False)
                awaiting_weather_follow_up_choice = contexto.get("awaiting_weather_follow_up_choice", False)
                awaiting_menu_return_prompt = contexto.get("awaiting_menu_return_prompt", False)
                # Novos flags para a simulação de safra
                simulacao_safra_ativa = contexto.get("simulacao_safra_ativa", False)
                etapa_simulacao = contexto.get("etapa_simulacao", None)
                dados_simulacao = contexto.get("dados_simulacao", {})
                awaiting_safra_finalizacao = contexto.get("awaiting_safra_finalizacao", False)
                simulacao_sub_fluxo = contexto.get("simulacao_sub_fluxo", None) # New flag for sub-menu
                gerar_relatorio_simulacao_ativo = contexto.get("gerar_relatorio_simulacao_ativo", False)

                # Novos flags para Gestão de Rebanho
                gestao_rebanho_ativo = contexto.get("gestao_rebanho_ativo", False)
                gestao_rebanho_sub_fluxo = contexto.get("gestao_rebanho_sub_fluxo", None) # 1: Cadastrar animal, 2: Vac/Verm, 3: Reprodutivo, 4: Pesagens, 5: Consultar Animais, 6: Gerar Relatório
                gerar_relatorio_rebanho_ativo = contexto.get("gerar_relatorio_rebanho_ativo", False)

                # Sub-fluxos dentro de Vacinação/Vermifugação (antigo controle_vacinacao_ativo)
                vacinacao_vermifugacao_ativo = contexto.get("vacinacao_vermifugacao_ativo", False) # New flag for this specific sub-menu
                vacinacao_vermifugacao_opcao = contexto.get("vacinacao_vermifugacao_opcao", None) # 1: registro vac, 2: consulta vac, 3: registro verm, 4: consulta verm, 5: lembretes

                registro_vacinacao_etapa = contexto.get("registro_vacinacao_etapa", None)
                dados_vacinacao_registro = contexto.get("dados_vacinacao_registro", {})
                consulta_vacinacao_ativa = contexto.get("consulta_vacinacao_ativa", False)
                awaiting_animal_id_consulta_vac = contexto.get("awaiting_animal_id_consulta_vac", False) # Renamed for clarity

                registro_vermifugacao_etapa = contexto.get("registro_vermifugacao_etapa", None)
                dados_vermifugacao_registro = contexto.get("dados_vermifugacao_registro", {})
                consulta_vermifugacao_ativa = contexto.get("consulta_vermifugacao_ativa", False)
                awaiting_animal_id_consulta_verm = contexto.get("awaiting_animal_id_consulta_verm", False) # New flag

                lembretes_vacinacao_ativo = contexto.get("lembretes_vacinacao_ativo", False)
                awaiting_lembretes_contato = contexto.get("awaiting_lembretes_contato", False)

                # Novos flags para Cadastrar Animal
                cadastro_animal_ativo = contexto.get("cadastro_animal_ativo", False)
                registro_animal_etapa = contexto.get("registro_animal_etapa", None)
                dados_animal_registro = contexto.get("dados_animal_registro", {})

                # Novos flags para Controle Reprodutivo
                controle_reprodutivo_ativo = contexto.get("controle_reprodutivo_ativo", False)
                # Add more specific flags/steps for reproductive control here

                # Novos flags para Histórico de Pesagens
                historico_pesagens_ativo = contexto.get("historico_pesagens_ativo", False)
                # Add more specific flags/steps for weighing history here

                # Novos flags para Controle de Estoque
                controle_estoque_ativo = contexto.get("controle_estoque_ativo", False)
                controle_estoque_sub_fluxo = contexto.get("controle_estoque_sub_fluxo", None) # 1: Registrar Entrada, 2: Registrar Saída, 3: Consultar Estoque, 4: Avisos, 5: Gerar Relatório
                gerar_relatorio_estoque_ativo = contexto.get("gerar_relatorio_estoque_ativo", False)

                # Novos flags para as novas funcionalidades de Controle de Estoque
                registro_entrada_estoque_ativo = contexto.get("registro_entrada_estoque_ativo", False)
                registro_entrada_estoque_etapa = contexto.get("registro_entrada_estoque_etapa", None)
                dados_entrada_estoque_registro = contexto.get("dados_entrada_estoque_registro", {})
                
                registro_saida_estoque_ativo = contexto.get("registro_saida_estoque_ativo", False)
                registro_saida_estoque_etapa = contexto.get("registro_saida_estoque_etapa", None)
                dados_saida_estoque_registro = contexto.get("dados_saida_estoque_registro", {})
                
                consulta_estoque_ativa = contexto.get("consulta_estoque_ativa", False)


                # Para armazenar os registros (simulado)
                registros_vacinacao = contexto.get("registros_vacinacao", [])
                contexto["registros_vacinacao"] = registros_vacinacao # Ensure it's always in context
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

                # Novo flag para o fluxo de boas-vindas inicial
                initial_greeting_step = contexto.get("initial_greeting_step", None)
                print(f"DEBUG_INITIAL_GREETING_CHECK: initial_greeting_step antes da lógica de saudação: {initial_greeting_step}")

                # Flags para edição de cadastro
                editing_registration = contexto.get("editing_registration", False)
                awaiting_field_to_edit = contexto.get("awaiting_field_to_edit", False)
                current_editing_field = contexto.get("current_editing_field", None)


                current_time = datetime.now().timestamp()

                # --- Lógica de Timeout da Conversa (mantém no topo) ---
                # Se a última interação foi há mais de CONVERSATION_TIMEOUT_SECONDS, reinicia o fluxo
                if (current_time - last_interaction_time) > CONVERSATION_TIMEOUT_SECONDS:
                    print(f"DEBUG_TIMEOUT: Timeout detectado para {numero}. Reiniciando o fluxo da conversa.")
                    # Reset all relevant flags to ensure a clean return to the main menu
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False
                    contexto["initial_greeting_step"] = None # Reset initial greeting step on timeout

                    # AQUI: A mensagem de timeout foi alterada para a apresentação completa da Iagro.
                    resposta = (
                        f"Olá! 👋 Bem vindo ao Campo Inteligente! Me chamo Iagro, sou sua assistente de IA. Estou aqui para te ajudar a tomar as melhores decisões e melhorar sua gestão com o apoio da tecnologia. Vamos começar?\n1. Sim\n2. Não"
                    )
                    contexto["last_interaction_time"] = current_time # Update timestamp
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_TIMEOUT: Resposta gerada (timeout reset): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_TIMEOUT: Resultado do envio (timeout reset): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # Atualiza o timestamp da última interação para qualquer mensagem recebida
                contexto["last_interaction_time"] = current_time
                save_conversation_context(numero, contexto)

                # --- Handle explicit "voltar" or "menu" command (resets all flows and goes to main menu) ---
                if ("voltar" in mensagem_recebida or "menu" in mensagem_recebida or "opções" in mensagem_recebida):
                    print(f"DEBUG_COMMAND: Comando 'voltar'/'menu' detectado. Resetando fluxos.")
                    # Reset all relevant flags to ensure a clean return to the main menu
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False
                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE


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
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_COMMAND: Resposta gerada (retorno forçado ao menu principal): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_COMMAND: Resultado do envio (retorno forçado ao menu principal): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # --- Handle Location Message (highest priority, as it's a specific message type) ---
                location_message = data.get('data', {}).get('message', {}).get('locationMessage', {})
                if location_message:
                    print(f"DEBUG_LOCATION: Mensagem de localização recebida: {location_message}")
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
                            # Reset all relevant flags for a clean state before providing weather
                            contexto["awaiting_weather_location"] = False
                            contexto["awaiting_weather_follow_up_choice"] = True # Set to True as we are providing weather and then asking for follow-up
                            contexto["awaiting_menu_return_prompt"] = False
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
                            contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                            save_conversation_context(numero, contexto)

                            # AUTOMATICALLY PROVIDE WEATHER FORECAST
                            resposta = format_weather_response(cidade, pais) # This function already includes the follow-up question
                        
                        print(f"DEBUG_LOCATION: Resposta gerada (localização via mensagem - com clima): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_LOCATION: Resultado do envio (localização via mensagem - com clima): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # --- Initial Greeting Flow (standalone IF block) ---
                # This block handles the initial conversation setup.
                # It should only proceed to other flows once initial_greeting_step is "completed".
                if initial_greeting_step is None:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step None) - Mensagem: '{mensagem_recebida}'")
                    resposta = "Olá! 👋 Bem vindo ao Campo Inteligente! Me chamo Iagro, sou sua assistente de IA. Estou aqui para te ajudar a tomar as melhores decisões e melhorar sua gestão com o apoio da tecnologia. Vamos começar?\n1. Sim\n2. Não"
                    contexto["initial_greeting_step"] = 1
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_GREETING: initial_greeting_step definido para 1. Contexto salvo: {contexto}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200
                
                elif initial_greeting_step == 1:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step 1) - Mensagem: '{mensagem_recebida}'")
                    if mensagem_recebida == "1" or "sim" in mensagem_recebida:
                        resposta = "Ótimo! Para começarmos, posso saber seu nome? 😊"
                        contexto["initial_greeting_step"] = 2
                        print(f"DEBUG_GREETING: initial_greeting_step definido para 2. Contexto salvo: {contexto}")
                    elif mensagem_recebida == "2" or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        resposta = "Entendido. Deseja encerrar a conversa?\n1. Sim\n2. Não"
                        contexto["initial_greeting_step"] = "awaiting_end_conversation"
                        print(f"DEBUG_GREETING: initial_greeting_step definido para awaiting_end_conversation. Contexto salvo: {contexto}")
                    else:
                        resposta = "Não entendi. Por favor, diga '1' para começar ou '2' para encerrar. 🤔"
                        print(f"DEBUG_GREETING: Opção inválida, mantendo initial_greeting_step em 1. Contexto salvo: {contexto}")
                    save_conversation_context(numero, contexto)
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif initial_greeting_step == 2:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step 2) - Mensagem: '{mensagem_recebida}'")
                    contexto["nome_completo"] = mensagem_recebida.strip().title()
                    nome = contexto["nome_completo"] # Update local 'nome' variable
                    resposta = f"Prazer em te conhecer, {nome}! 👋 Poderia me falar de qual cidade você está falando? 📍"
                    contexto["initial_greeting_step"] = 3
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_GREETING: initial_greeting_step definido para 3. Contexto salvo: {contexto}")
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif initial_greeting_step == 3:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step 3) - Mensagem: '{mensagem_recebida}'")
                    cidade_input = mensagem_recebida.strip().title()
                    local_info = obter_previsao_tempo(cidade_input, "BR") # Assume Brasil por enquanto
                    if "erro" not in local_info:
                        contexto["localizacao"] = {
                            "cidade": local_info.get("cidade", cidade_input),
                            "estado": "", # Pode ser preenchido com uma API de geocodificação reversa se necessário
                            "pais": "BR"
                        }
                        resposta = f"Certo, {cidade_input}! Entendi sua localização. Vamos em frente com o restante do seu cadastro, {nome}?\n1. Sim\n2. Não"
                        contexto["initial_greeting_step"] = 4
                        print(f"DEBUG_GREETING: initial_greeting_step definido para 4. Contexto salvo: {contexto}")
                    else:
                        resposta = f"Não consegui confirmar a cidade '{cidade_input}', {nome}. Por favor, digite o nome da sua cidade novamente ou compartilhe sua localização. 🤔"
                        # Permanece na mesma etapa para tentar novamente
                        print(f"DEBUG_GREETING: Erro ao confirmar cidade, mantendo initial_greeting_step em 3. Contexto salvo: {contexto}")
                    save_conversation_context(numero, contexto)
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif initial_greeting_step == 4:
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step 4) - Mensagem: '{mensagem_recebida}'")
                    if mensagem_recebida == "1" or "sim" in mensagem_recebida:
                        contexto["initial_greeting_step"] = "completed"
                        print(f"DEBUG_GREETING: initial_greeting_step definido para 'completed'. Contexto salvo: {contexto}")
                        # Se o nome já foi coletado, a próxima pergunta será a de CPF
                        if contexto.get("nome_completo"):
                            next_question_key = REGISTRATION_ORDER[REGISTRATION_ORDER.index("nome_completo") + 1]
                            contexto["registration_step"] = next_question_key
                            resposta = f"Excelente, {nome}! Agora vamos para o restante do seu cadastro. {REGISTRATION_QUESTIONS[next_question_key]}\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                        else: # Fallback if name wasn't captured for some reason
                            contexto["registration_step"] = REGISTRATION_ORDER[0]
                            resposta = f"Excelente, {nome}! Agora vamos para o restante do seu cadastro. {REGISTRATION_QUESTIONS[REGISTRATION_ORDER[0]]}\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                        
                    elif mensagem_recebida == "2" or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        resposta = f"Entendido, {nome}. Deseja encerrar a conversa?\n1. Sim\n2. Não"
                        contexto["initial_greeting_step"] = "awaiting_end_conversation"
                        print(f"DEBUG_GREETING: initial_greeting_step definido para awaiting_end_conversation. Contexto salvo: {contexto}")
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, diga '1' para continuar o cadastro ou '2' para encerrar. 🤔"
                        print(f"DEBUG_GREETING: Opção inválida, mantendo initial_greeting_step em 4. Contexto salvo: {contexto}")
                    save_conversation_context(numero, contexto)
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif initial_greeting_step == "awaiting_end_conversation":
                    print(f"DEBUG_GREETING: Entrando no fluxo de saudação inicial (step awaiting_end_conversation) - Mensagem: '{mensagem_recebida}'")
                    if mensagem_recebida == "1" or "sim" in mensagem_recebida:
                        resposta = f"Ok, {nome}, estarei aqui se precisar de algo mais! Até logo! 👋"
                        contexto.clear() # Limpa todo o contexto para um novo início
                        contexto["last_interaction_time"] = current_time # Mantém o timestamp
                        print(f"DEBUG_GREETING: Contexto limpo após encerramento. Contexto salvo: {contexto}")
                    elif mensagem_recebida == "2" or "não" in mensagem_recebida or "nao" in mensagem_recebida:
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
                        contexto["initial_greeting_step"] = "completed" # Set to completed if user chooses not to end conversation
                        print(f"DEBUG_GREETING: initial_greeting_step definido para 'completed'. Contexto salvo: {contexto}")
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, diga '1' para encerrar ou '2' para ver as opções. 🤔"
                        print(f"DEBUG_GREETING: Opção inválida, mantendo initial_greeting_step em awaiting_end_conversation. Contexto salvo: {contexto}")
                    save_conversation_context(numero, contexto)
                    send_whatsapp_message(numero, resposta)
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # --- Main conversational flow logic (strict if/elif chain) ---
                # These should be checked *after* the initial greeting flow is completed.
                # The 'initial_greeting_step' will be "completed" at this point if the user passed the initial flow.
                elif awaiting_continuation_choice:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_continuation_choice")
                    if "continuar" in mensagem_recebida:
                        contexto["awaiting_continuation_choice"] = False
                        resposta = f"Ótimo, {nome}! Vamos continuar de onde paramos. {REGISTRATION_QUESTIONS[registration_step]}"
                    elif "sair" in mensagem_recebida:
                        contexto["awaiting_continuation_choice"] = False
                        contexto["registration_step"] = None
                        # Reset all relevant flags
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
                        # Novas flags de estoque
                        contexto["registro_entrada_estoque_ativo"] = False
                        contexto["registro_entrada_estoque_etapa"] = None
                        contexto["dados_entrada_estoque_registro"] = {}
                        contexto["registro_saida_estoque_ativo"] = False
                        contexto["registro_saida_estoque_etapa"] = None
                        contexto["dados_saida_estoque_registro"] = {}
                        contexto["consulta_estoque_ativa"] = False
                        resposta = f"Ok, {nome}, o cadastro foi cancelado. Posso ajudar com mais alguma coisa? 👋"
                    else:
                        resposta = f"Por favor, {nome}, diga 'continuar' para retomar o cadastro ou 'sair' para cancelá-lo."
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_FLOW: Resposta gerada (continuar cadastro): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_FLOW: Resultado do envio (continuar cadastro): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif awaiting_weather_follow_up_choice:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_weather_follow_up_choice")
                    if "outra" in mensagem_recebida or "nova" in mensagem_recebida or "sim" in mensagem_recebida or "clima" in mensagem_recebida:
                        contexto["awaiting_weather_location"] = True
                        contexto["awaiting_weather_follow_up_choice"] = False
                        # Reset all relevant flags
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
                        # Novas flags de estoque
                        contexto["registro_entrada_estoque_ativo"] = False
                        contexto["registro_entrada_estoque_etapa"] = None
                        contexto["dados_entrada_estoque_registro"] = {}
                        contexto["registro_saida_estoque_ativo"] = False
                        contexto["registro_saida_estoque_etapa"] = None
                        contexto["dados_saida_estoque_registro"] = {}
                        contexto["consulta_estoque_ativa"] = False
                        resposta = f"Por favor, {nome}, me diga o nome da cidade ou compartilhe sua localização. 📍"
                    elif "voltar" in mensagem_recebida or "menu" in mensagem_recebida or "opções" in mensagem_recebida or "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        contexto["awaiting_weather_location"] = False
                        contexto["awaiting_weather_follow_up_choice"] = False
                        contexto["awaiting_menu_return_prompt"] = False
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
                        # Novas flags de estoque
                        contexto["registro_entrada_estoque_ativo"] = False
                        contexto["registro_entrada_estoque_etapa"] = None
                        contexto["dados_entrada_estoque_registro"] = {}
                        contexto["registro_saida_estoque_ativo"] = False
                        contexto["registro_saida_estoque_etapa"] = None
                        contexto["dados_saida_estoque_registro"] = {}
                        contexto["consulta_estoque_ativa"] = False
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
                        resposta = f"Não entendi, {nome}. Deseja fazer outra consulta de clima ou voltar para as opções iniciais? (Responda 'outra' ou 'voltar')"
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_FLOW: Resposta gerada (seguimento clima): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_FLOW: Resultado do envio (seguimento clima): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif awaiting_menu_return_prompt:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_menu_return_prompt")
                    if "sim" in mensagem_recebida or "voltar" in mensagem_recebida or "menu" in mensagem_recebida or "opções" in mensagem_recebida:
                        contexto["awaiting_menu_return_prompt"] = False
                        contexto["awaiting_weather_location"] = False
                        contexto["awaiting_weather_follow_up_choice"] = False
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
                        # Novas flags de estoque
                        contexto["registro_entrada_estoque_ativo"] = False
                        contexto["registro_entrada_estoque_etapa"] = None
                        contexto["dados_entrada_estoque_registro"] = {}
                        contexto["registro_saida_estoque_ativo"] = False
                        contexto["registro_saida_estoque_etapa"] = None
                        contexto["dados_saida_estoque_registro"] = {}
                        contexto["consulta_estoque_ativa"] = False
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
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_FLOW: Resposta gerada (retorno ao menu principal após opção informativa): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_FLOW: Resultado do envio (retorno ao menu principal após opção informativa): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif awaiting_post_completion_response:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_post_completion_response")
                    if "sim" in mensagem_recebida:
                        contexto["awaiting_post_completion_response"] = False
                        if contexto.get("gestao_rebanho_ativo"): # If we just finished a Gestão de Rebanho sub-flow
                            if contexto.get("vacinacao_vermifugacao_ativo"): # If we were in vac/verm sub-menu
                                resposta = (
                                    f"O que deseja fazer agora na seção de Vacinação e Vermifugação, {nome}? 💉🐛\n"
                                    "Digite:\n\n"
                                    "1 para Registrar vacinação\n"
                                    "2 para Consultar vacinação\n"
                                    "3 para Registrar vermifugação\n"
                                    "4 para Consultar vermifugação\n"
                                    "5 para Receber lembretes futuros\n"
                                    "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                )
                                contexto["vacinacao_vermifugacao_opcao"] = None # Reset sub-sub-flow choice
                            else: # Just finished a Gestão de Rebanho sub-flow (e.g., animal registration)
                                resposta = (
                                    f"O que você gostaria de fazer agora na Gestão de Rebanho, {nome}? 🐄\n\n"
                                    "Digite:\n"
                                    "1 para Cadastrar novo animal\n"
                                    "2 para Controle de vacinação e vermifugação\n"
                                    "3 para Controle reprodutivo\n"
                                    "4 para Histórico de pesagens\n"
                                    "5 para Consultar Animais\n" # New option
                                    "6 para Gerar Relatório\n" # New option
                                    "Ou 'voltar' para o menu principal."
                                )
                                contexto["gestao_rebanho_sub_fluxo"] = None # Reset sub-flow choice
                        elif contexto.get("controle_estoque_ativo"): # If we just finished a Controle de Estoque sub-flow
                            resposta = (
                                f"O que você gostaria de fazer agora no Controle de Estoque, {nome}? 📦\n\n"
                                "Digite:\n"
                                "1 para Registrar Entrada de Insumos/Produtos\n"
                                "2 para Registrar Saída de Insumos/Produtos\n"
                                "3 para Consultar Estoque\n"
                                "4 para Avisos de estoque baixo\n"
                                "5 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                            contexto["controle_estoque_sub_fluxo"] = None # Reset sub-flow choice
                            # Reset new stock flags
                            contexto["registro_entrada_estoque_ativo"] = False
                            contexto["registro_entrada_estoque_etapa"] = None
                            contexto["dados_entrada_estoque_registro"] = {}
                            contexto["registro_saida_estoque_ativo"] = False
                            contexto["registro_saida_estoque_etapa"] = None
                            contexto["dados_saida_estoque_registro"] = {}
                            contexto["consulta_estoque_ativa"] = False
                            contexto["gerar_relatorio_estoque_ativo"] = False # New flag
                        elif contexto.get("simulacao_safra_ativa"): # If we just finished a Simulação de Safra sub-flow
                            resposta = (
                                f"O que você gostaria de fazer agora na Simulação de Safra, {nome}? 🌾\n\n"
                                "Digite:\n"
                                "1 para Iniciar nova simulação\n"
                                "2 para Consultar Simulações Anteriores\n" # New option
                                "3 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                            contexto["simulacao_sub_fluxo"] = None # Reset sub-flow
                            contexto["gerar_relatorio_simulacao_ativo"] = False # New flag
                        else: # General "sim" after other flows (e.g., registration)
                            resposta = (
                                f"Ok, {nome}! Estou aqui para ajudar você com sua produção agrícola! 👋\n\n"
                                f"Escolha uma das opções abaixo para começarmos:\n"
                                f"1. Previsão Climática ☁️\n"
                                f"2. Controle de Estoque 📦\n"
                                f"3. Gestão de Rebanho 🐄\n"
                                f"4. Simulação de Safra �\n"
                                f"5. {cadastro_opcao_texto} 📝\n"
                                f"6. Alertas de Pragas 🐛\n"
                                f"7. Análise de Mercado 📈\n"
                                f"8. Localização 📍\n"
                                f"9. Outras Informações 💡"
                            )
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (pós-conclusão - sim): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (pós-conclusão - sim): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200
                    elif "não" in mensagem_recebida or "nao" in mensagem_recebida:
                        # Reset all flags to ensure clean return to the main menu
                        contexto["awaiting_post_completion_response"] = False
                        contexto["awaiting_weather_location"] = False
                        contexto["awaiting_weather_follow_up_choice"] = False
                        contexto["awaiting_menu_return_prompt"] = False
                        contexto["registration_step"] = None
                        contexto["editing_registration"] = False
                        contexto["awaiting_field_to_edit"] = False
                        contexto["current_editing_field"] = None
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
                        # Novas flags de estoque
                        contexto["registro_entrada_estoque_ativo"] = False
                        contexto["registro_entrada_estoque_etapa"] = None
                        contexto["dados_entrada_estoque_registro"] = {}
                        contexto["registro_saida_estoque_ativo"] = False
                        contexto["registro_saida_estoque_etapa"] = None
                        contexto["dados_saida_estoque_registro"] = {}
                        contexto["consulta_estoque_ativa"] = False
                        
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
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (retorno ao menu principal após 'não'): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (retorno ao menu principal após 'não'): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, responda 'sim' ou 'não'."
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (pós-conclusão - opção inválida): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (pós-conclusão - opção inválida): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif simulacao_safra_ativa:
                    print(f"DEBUG_FLOW: Fluxo: simulacao_safra_ativa")
                    etapa = contexto.get("etapa_simulacao")
                    dados = contexto.get("dados_simulacao", {})

                    if "voltar" in mensagem_recebida:
                        # If in a sub-flow of Simulação de Safra, go back to Simulação de Safra main menu
                        if simulacao_sub_fluxo is not None or gerar_relatorio_simulacao_ativo:
                            contexto["simulacao_sub_fluxo"] = None
                            contexto["gerar_relatorio_simulacao_ativo"] = False
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Simulação de Safra. 🌾\n\n"
                                "O que você gostaria de fazer?\n\n"
                                "1 para Iniciar nova simulação\n"
                                "2 para Consultar Simulações Anteriores\n"
                                "3 para Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                        elif etapa == 1: # Trying to go back from the first step of simulation
                            contexto["simulacao_safra_ativa"] = False
                            contexto["etapa_simulacao"] = None
                            contexto["dados_simulacao"] = {}
                            contexto["awaiting_safra_finalizacao"] = False
                            contexto["simulacao_sub_fluxo"] = None
                            contexto["gerar_relatorio_simulacao_ativo"] = False
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
                        else: # Go back one step in the simulation flow
                            contexto["etapa_simulacao"] -= 1
                            if contexto["etapa_simulacao"] == 0: # If it goes below 1, means it's the first step
                                contexto["simulacao_safra_ativa"] = False
                                contexto["etapa_simulacao"] = None
                                contexto["dados_simulacao"] = {}
                                contexto["simulacao_sub_fluxo"] = None
                                contexto["gerar_relatorio_simulacao_ativo"] = False
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
                                # Need to map back to the correct question for the previous step
                                # For now, a generic message or re-asking the current question is safer.
                                resposta = f"Ok, {nome}, voltando. Por favor, responda novamente a pergunta anterior sobre a simulação.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (simulação voltar): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (simulação voltar): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    if simulacao_sub_fluxo is None: # User just entered Simulação de Safra menu
                        if mensagem_recebida == "1": # Iniciar nova simulação
                            contexto["simulacao_sub_fluxo"] = 1
                            contexto["etapa_simulacao"] = 1
                            contexto["dados_simulacao"] = {}
                            resposta = f"Olá, {nome}! 👋 Vamos começar a sua simulação de safra. 🌾\n\nPor favor, me informe os seguintes dados para gerar a previsão mais precisa possível. 🌱\n\n👉 Qual é a cultura que deseja simular?\nEx.: soja, milho, trigo, café, etc.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif mensagem_recebida == "2": # Consultar Simulações Anteriores
                            contexto["simulacao_sub_fluxo"] = 2
                            if contexto["simulacoes_passadas"]:
                                resposta = "📊 **Suas Simulações Anteriores:** 📊\n"
                                for i, sim in enumerate(contexto["simulacoes_passadas"]):
                                    cultura = sim.get("cultura", "N/A")
                                    area = sim.get("area", "N/A")
                                    produtividade = sim.get("produtividade_media", "N/A")
                                    resposta += f"{i+1}️⃣ Cultura: {cultura.capitalize()}, Área: {area} ha, Produtividade Estimada: {produtividade} kg/ha\n"
                            else:
                                resposta = f"Você ainda não realizou nenhuma simulação, {nome}. Que tal iniciar uma? 🌱"
                            resposta += "\n\nDeseja voltar ao menu de Simulação de Safra? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True # Reusing for sub-menu return
                        elif mensagem_recebida == "3": # Gerar Relatório
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
                                "1 para Iniciar nova simulação\n"
                                "2 para Consultar Simulações Anteriores\n"
                                "3 para Gerar Relatório\n"
                                "Ou 'voltar' para o menu principal."
                            )
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (simulação safra sub-menu): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (simulação safra sub-menu): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    # Continue with existing simulation steps if simulacao_sub_fluxo is 1 (Iniciar nova simulação)
                    elif simulacao_sub_fluxo == 1:
                        if etapa == 1:
                            dados["cultura"] = mensagem_recebida
                            contexto["etapa_simulacao"] = 2
                            contexto["dados_simulacao"] = dados
                            save_conversation_context(numero, contexto)
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
                                save_conversation_context(numero, contexto)
                                resposta = f"✅ Perfeito, {nome}! Qual o tipo de solo predominante? ⛰️\nEx.: arenoso, argiloso, misto, etc.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            except ValueError:
                                resposta = f"Por favor, {nome}, informe a área em hectares usando um número válido (ex: 50, 100.5).\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                print(f"DEBUG_FLOW: Resposta gerada (erro simulação etapa 2): {resposta}")
                                send_status, send_resp = send_whatsapp_message(numero, resposta)
                                print(f"DEBUG_FLOW: Resultado do envio (erro simulação etapa 2): Status={send_status}, Resposta={send_resp}")
                                return jsonify({"status": "erro", "resposta": resposta}), 200
                        elif etapa == 3:
                            dados["tipo_solo"] = mensagem_recebida
                            contexto["etapa_simulacao"] = 4
                            contexto["dados_simulacao"] = dados
                            save_conversation_context(numero, contexto)
                            resposta = f"✅ E quais são as condições climáticas previstas, {nome}? ☀️🌧️\nEx.: seca, chuva moderada, excesso de chuva, clima ideal...\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif etapa == 4:
                            dados["condicoes_climaticas"] = mensagem_recebida
                            contexto["etapa_simulacao"] = 5
                            contexto["dados_simulacao"] = dados
                            save_conversation_context(numero, contexto)
                            resposta = f"✅ Por fim, {nome}, qual é a variedade ou o ciclo da cultura? ⏳\nEx.: ciclo precoce, médio ou tardio?\n(Se não souber, pode digitar \"não sei\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif etapa == 5:
                            dados["ciclo_cultura"] = mensagem_recebida
                            
                            # Save the completed simulation to history
                            contexto["simulacoes_passadas"].append(dados)

                            contexto["etapa_simulacao"] = None  # Finaliza a coleta de dados da simulação
                            contexto["simulacao_safra_ativa"] = False # Desativa o flag da simulação ativa
                            contexto["simulacao_sub_fluxo"] = None # Reset sub-flow
                            contexto["dados_simulacao"] = {} # Clear temporary data
                            contexto["gerar_relatorio_simulacao_ativo"] = False
                            save_conversation_context(numero, contexto)
                            
                            print(f"DEBUG_FLOW: Enviando mensagem de processamento da simulação...")
                            send_status, send_resp = send_whatsapp_message(numero, "🚜 Processando a simulação da sua safra... \n\n🔄 Isso pode levar alguns segundos...")
                            print(f"DEBUG_FLOW: Resultado do envio (simulação processando): Status={send_status}, Resposta={send_resp}")
                            
                            # Chama a função para simular a safra
                            resultado_simulacao = simular_safra(dados)
                            
                            # Após a simulação, envie o resultado formatado
                            resposta_resultado = formatar_resultado_simulacao(dados, resultado_simulacao)
                            print(f"DEBUG_FLOW: Resposta gerada (simulação resultado): {resposta_resultado}")
                            send_status_resultado, send_resp_resultado = send_whatsapp_message(numero, resposta_resultado)
                            print(f"DEBUG_FLOW: Resultado do envio (simulação resultado): Status={send_status_resultado}, Resposta={send_resp_resultado}")

                            # Pergunta de finalização
                            contexto["awaiting_safra_finalizacao"] = True
                            save_conversation_context(numero, contexto)
                            resposta = f"✅ Deseja realizar **outra simulação**, {nome}, ou **finalizar**? 🤔\n\n1. Nova simulação\n2. Sair\n(Ou 'voltar' para o menu principal)"
                        else: # Fallback for unexpected simulation step
                            resposta = f"Ocorreu um erro no fluxo da simulação, {nome}. Por favor, digite '4' para iniciar uma nova simulação ou 'menu' para voltar ao menu principal."
                            contexto["simulacao_safra_ativa"] = False
                            contexto["etapa_simulacao"] = None
                            contexto["dados_simulacao"] = {}
                            contexto["awaiting_safra_finalizacao"] = False
                            contexto["simulacao_sub_fluxo"] = None
                            contexto["gerar_relatorio_simulacao_ativo"] = False
                            save_conversation_context(numero, contexto)

                        print(f"DEBUG_FLOW: Resposta gerada (simulação etapa {etapa}): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (simulação etapa {etapa}): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    else: # Fallback for unexpected Simulação de Safra sub-flow step
                        resposta = f"Ocorreu um erro no fluxo de Simulação de Safra, {nome}. Por favor, digite '4' para voltar ao menu de Simulação de Safra ou 'menu' para voltar ao menu principal."
                        contexto["simulacao_safra_ativa"] = True # Keep active to allow choosing another sub-flow
                        contexto["simulacao_sub_fluxo"] = None # Reset sub-sub-flow choice
                        contexto["gerar_relatorio_simulacao_ativo"] = False
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (erro simulação safra sub-fluxo): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (erro simulação safra sub-fluxo): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif awaiting_safra_finalizacao:
                    print(f"DEBUG_FLOW: Fluxo: awaiting_safra_finalizacao")
                    if mensagem_recebida == "1":
                        # Inicia uma nova simulação
                        contexto["simulacao_safra_ativa"] = True
                        contexto["etapa_simulacao"] = 1
                        contexto["dados_simulacao"] = {}
                        contexto["awaiting_safra_finalizacao"] = False # Resetar este flag
                        contexto["simulacao_sub_fluxo"] = 1 # Set sub-flow to iniciar nova simulação
                        contexto["gerar_relatorio_simulacao_ativo"] = False
                        save_conversation_context(numero, contexto)
                        resposta_nova_simulacao = f"Ok, {nome}, vamos iniciar uma nova simulação. 🌱\n\n👉 Qual é a cultura que deseja simular?\nEx.: soja, milho, trigo, café, etc.\n(Ou 'voltar' para o menu principal)"
                        print(f"DEBUG_FLOW: Resposta gerada (simulação nova): {resposta_nova_simulacao}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta_nova_simulacao)
                        print(f"DEBUG_FLOW: Resultado do envio (simulação nova): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta_nova_simulacao}), 200
                    elif mensagem_recebida == "2":
                        # Sai da simulação e retorna ao menu principal
                        contexto["awaiting_safra_finalizacao"] = False
                        # Resetar flags da simulação de safra
                        contexto["simulacao_safra_ativa"] = False
                        contexto["etapa_simulacao"] = None
                        contexto["dados_simulacao"] = {}
                        contexto["simulacao_sub_fluxo"] = None
                        contexto["gerar_relatorio_simulacao_ativo"] = False
                        save_conversation_context(numero, contexto)
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
                        print(f"DEBUG_FLOW: Resposta gerada (simulação sair): {resposta_sair}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta_sair)
                        print(f"DEBUG_FLOW: Resultado do envio (simulação sair): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta_sair}), 200
                    else:
                        resposta_opcao_invalida = f"Opção inválida, {nome}. Digite 1 para nova simulação ou 2 para sair.\n(Ou 'voltar' para o menu principal)"
                        print(f"DEBUG_FLOW: Resposta gerada (simulação opção inválida): {resposta_opcao_invalida}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta_opcao_invalida)
                        print(f"DEBUG_FLOW: Resultado do envio (simulação opção inválida): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "erro", "resposta": resposta_opcao_invalida}), 200

                elif controle_estoque_ativo:
                    print(f"DEBUG_FLOW: Fluxo: controle_estoque_ativo")
                    if "voltar" in mensagem_recebida:
                        # If we are in a sub-sub-flow, go back to main estoque menu
                        if registro_entrada_estoque_ativo or registro_saida_estoque_ativo or consulta_estoque_ativa or gerar_relatorio_estoque_ativo:
                            contexto["registro_entrada_estoque_ativo"] = False
                            contexto["registro_entrada_estoque_etapa"] = None
                            contexto["dados_entrada_estoque_registro"] = {}
                            contexto["registro_saida_estoque_ativo"] = False
                            contexto["registro_saida_estoque_etapa"] = None
                            contexto["dados_saida_estoque_registro"] = {}
                            contexto["consulta_estoque_ativa"] = False
                            contexto["gerar_relatorio_estoque_ativo"] = False
                            contexto["controle_estoque_sub_fluxo"] = None # Back to main estoque menu
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Controle de Estoque. 📦\n\n"
                                "O que você gostaria de fazer?\n\n"
                                "1 para Registrar Entrada de Insumos/Produtos\n"
                                "2 para Registrar Saída de Insumos/Produtos\n"
                                "3 para Consultar Estoque\n"
                                "4 para Avisos de estoque baixo\n"
                                "5 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                        elif controle_estoque_sub_fluxo is None: # Trying to go back from main estoque menu
                            contexto["controle_estoque_ativo"] = False
                            contexto["controle_estoque_sub_fluxo"] = None
                            contexto["gerar_relatorio_estoque_ativo"] = False
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
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (controle estoque voltar): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (controle estoque voltar): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    if controle_estoque_sub_fluxo is None:
                        if mensagem_recebida == "1": # Registrar Entrada
                            contexto["controle_estoque_sub_fluxo"] = 1
                            contexto["registro_entrada_estoque_ativo"] = True
                            contexto["registro_entrada_estoque_etapa"] = 1
                            contexto["dados_entrada_estoque_registro"] = {}
                            resposta = f"✅ Qual o nome/identificação do item que está dando entrada no estoque, {nome}? 📦\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif mensagem_recebida == "2": # Registrar Saída
                            contexto["controle_estoque_sub_fluxo"] = 2
                            contexto["registro_saida_estoque_ativo"] = True
                            contexto["registro_saida_estoque_etapa"] = 1
                            contexto["dados_saida_estoque_registro"] = {}
                            resposta = f"✅ Qual o nome/identificação do item que está saindo do estoque, {nome}? 📤\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif mensagem_recebida == "3": # Consultar Estoque
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
                                    resposta += f"{i+1}️⃣ {nome_item.capitalize()} - Qtd: {quantidade} - Entrada: {data_entrada} - Fab: {data_fabricacao} - Venc: {data_vencimento} - Lote: {lote}\n"
                            else:
                                resposta = f"Seu estoque está vazio no momento, {nome}. Que tal registrar uma entrada? 📦"
                            resposta += "\n\nDeseja voltar ao menu de Controle de Estoque? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True # Reusing for sub-menu return
                        elif mensagem_recebida == "4": # Avisos de estoque baixo
                            contexto["controle_estoque_sub_fluxo"] = 4
                            resposta = f"Em breve teremos os avisos de estoque baixo, {nome}! Aguarde! 📉\n\nDeseja voltar ao menu de Controle de Estoque? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True
                        elif mensagem_recebida == "5": # Gerar Relatório
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
                                "1 para Registrar Entrada de Insumos/Produtos\n"
                                "2 para Registrar Saída de Insumos/Produtos\n"
                                "3 para Consultar Estoque\n"
                                "4 para Avisos de estoque baixo\n"
                                "5 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (controle estoque sub-menu): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (controle estoque sub-menu): Status={send_status}, Resposta={send_resp}")
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
                            dados_entrada_estoque_registro["data_entrada"] = mensagem_recebida.strip()
                            contexto["registro_entrada_estoque_etapa"] = 4
                            resposta = f"✅ Qual a data de fabricação do item, {nome}? (dd/mm/aaaa) 🗓️\n(Se não houver, responda \"não\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_entrada_estoque_etapa == 4:
                            data_fabricacao = mensagem_recebida.strip()
                            dados_entrada_estoque_registro["data_fabricacao"] = data_fabricacao if data_fabricacao != "não" else "Não informado"
                            contexto["registro_entrada_estoque_etapa"] = 5
                            resposta = f"✅ Qual a data de vencimento do item, {nome}? (dd/mm/aaaa) ⏳\n(Se não houver, responda \"não\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_entrada_estoque_etapa == 5:
                            data_vencimento = mensagem_recebida.strip()
                            dados_entrada_estoque_registro["data_vencimento"] = data_vencimento if data_vencimento != "não" else "Não informado"
                            contexto["registro_entrada_estoque_etapa"] = 6
                            resposta = f"✅ Qual o número do lote do item, {nome}? (Se não houver, responda \"não\") 🏷️\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_entrada_estoque_etapa == 6:
                            numero_lote = mensagem_recebida.strip()
                            dados_entrada_estoque_registro["numero_lote"] = numero_lote if numero_lote != "não" else "Não informado"
                            
                            contexto["registros_estoque"].append(dados_entrada_estoque_registro) # Add to stock records

                            contexto["registro_entrada_estoque_ativo"] = False
                            contexto["registro_entrada_estoque_etapa"] = None
                            contexto["controle_estoque_sub_fluxo"] = None # Back to main estoque menu

                            resposta = f"""📦 **Registro de Entrada Concluído, {nome}!** 📦
Item: {dados_entrada_estoque_registro.get("nome_item", "N/A").capitalize()}
Quantidade: {dados_entrada_estoque_registro.get("quantidade", "N/A")}
Data de Entrada: {dados_entrada_estoque_registro.get("data_entrada", "N/A")}
Data de Fabricação: {dados_entrada_estoque_registro.get("data_fabricacao", "N/A")}
Data de Vencimento: {dados_entrada_estoque_registro.get("data_vencimento", "N/A")}
Número de Lote: {dados_entrada_estoque_registro.get("numero_lote", "N/A")}
✅ Item registrado com sucesso! 🎉"""
                            
                            resposta += f"\n\nO que você gostaria de fazer agora no Controle de Estoque, {nome}? 📦\n\nDigite:\n1 para Registrar Entrada de Insumos/Produtos\n2 para Registrar Saída de Insumos/Produtos\n3 para Consultar Estoque\n4 para Avisos de estoque baixo\n5 para Gerar Relatório\nOu 'voltar' para o menu principal."
                            contexto["awaiting_post_completion_response"] = True # Use this flag to indicate a choice is needed
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (registro entrada estoque etapa {registro_entrada_estoque_etapa}): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (registro entrada estoque etapa {registro_entrada_estoque_etapa}): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif registro_saida_estoque_ativo:
                        print(f"DEBUG_FLOW: Fluxo: registro_saida_estoque_etapa {registro_saida_estoque_etapa}")
                        if registro_saida_estoque_etapa == 1:
                            dados_saida_estoque_registro["nome_item"] = mensagem_recebida.strip()
                            contexto["registro_saida_estoque_etapa"] = 2
                            resposta = f"✅ Qual a quantidade do item que está saindo, {nome}? 🔢\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_saida_estoque_etapa == 2:
                            dados_saida_estoque_registro["quantidade"] = mensagem_recebida.strip()
                            contexto["registro_saida_estoque_etapa"] = 3
                            resposta = f"✅ Qual a data de saída do item, {nome}? (dd/mm/aaaa) 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                        elif registro_saida_estoque_etapa == 3:
                            dados_saida_estoque_registro["data_saida"] = mensagem_recebida.strip()
                            
                            # For a real system, you'd decrement the stock here.
                            # For now, just logging the exit.
                            # You might want to add a separate list for 'saidas_estoque' if needed.

                            contexto["registro_saida_estoque_ativo"] = False
                            contexto["registro_saida_estoque_etapa"] = None
                            contexto["controle_estoque_sub_fluxo"] = None # Back to main estoque menu

                            resposta = f"""📤 **Registro de Saída Concluído, {nome}!** 📤
Item: {dados_saida_estoque_registro.get("nome_item", "N/A").capitalize()}
Quantidade: {dados_saida_estoque_registro.get("quantidade", "N/A")}
Data de Saída: {dados_saida_estoque_registro.get("data_saida", "N/A")}
✅ Saída registrada com sucesso! 🎉"""

                            resposta += f"\n\nO que você gostaria de fazer agora no Controle de Estoque, {nome}? 📦\n\nDigite:\n1 para Registrar Entrada de Insumos/Produtos\n2 para Registrar Saída de Insumos/Produtos\n3 para Consultar Estoque\n4 para Avisos de estoque baixo\n5 para Gerar Relatório\nOu 'voltar' para o menu principal."
                            contexto["awaiting_post_completion_response"] = True
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (registro saída estoque etapa {registro_saida_estoque_etapa}): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (registro saída estoque etapa {registro_saida_estoque_etapa}): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    else: # Fallback for unexpected Controle de Estoque sub-flow step
                        resposta = f"Ocorreu um erro no fluxo de Controle de Estoque, {nome}. Por favor, digite '2' para voltar ao menu de Controle de Estoque ou 'menu' para voltar ao menu principal."
                        contexto["controle_estoque_ativo"] = True # Keep active to allow choosing another sub-flow
                        contexto["controle_estoque_sub_fluxo"] = None # Reset sub-sub-flow choice
                        # Reset new stock flags
                        contexto["registro_entrada_estoque_ativo"] = False
                        contexto["registro_entrada_estoque_etapa"] = None
                        contexto["dados_entrada_estoque_registro"] = {}
                        contexto["registro_saida_estoque_ativo"] = False
                        contexto["registro_saida_estoque_etapa"] = None
                        contexto["dados_saida_estoque_registro"] = {}
                        contexto["consulta_estoque_ativa"] = False
                        contexto["gerar_relatorio_estoque_ativo"] = False
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (erro controle estoque sub-fluxo): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (erro controle estoque sub-fluxo): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200


                elif gestao_rebanho_ativo:
                    print(f"DEBUG_FLOW: Fluxo: gestao_rebanho_ativo")
                    if "voltar" in mensagem_recebida:
                        # If we are in a sub-flow of Gestão de Rebanho, go back to Gestão de Rebanho main menu
                        if vacinacao_vermifugacao_ativo: # If we were in vac/verm sub-menu, go back to Gestão de Rebanho menu
                            contexto["vacinacao_vermifugacao_ativo"] = False
                            contexto["vacinacao_vermifugacao_opcao"] = None
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Vacinação e Vermifugação. 💉🐛\n\n"
                                "O que você gostaria de fazer?\n\n"
                                "Digite:\n"
                                "1 para Registrar vacinação\n"
                                "2 para Consultar vacinação\n"
                                "3 para Registrar vermifugação\n"
                                "4 para Consultar vermifugação\n"
                                "5 para Receber lembretes futuros\n"
                                "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                            )
                        elif gestao_rebanho_sub_fluxo is not None: # If in any other sub-flow, go back to Gestão de Rebanho menu
                            contexto["cadastro_animal_ativo"] = False
                            contexto["registro_animal_etapa"] = None
                            contexto["dados_animal_registro"] = {}
                            contexto["controle_reprodutivo_ativo"] = False
                            contexto["historico_pesagens_ativo"] = False
                            contexto["gerar_relatorio_rebanho_ativo"] = False
                            contexto["gestao_rebanho_sub_fluxo"] = None # Reset sub-flow choice
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Gestão de Rebanho. 🐄\n\n"
                                "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                                "Digite:\n"
                                "1 para Cadastrar novo animal\n"
                                "2 para Controle de vacinação e vermifugação\n"
                                "3 para Controle reprodutivo\n"
                                "4 para Histórico de pesagens\n"
                                "5 para Consultar Animais\n" # New option
                                "6 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                        else: # Go back to main menu from Gestão de Rebanho menu
                            contexto["gestao_rebanho_ativo"] = False
                            contexto["gestao_rebanho_sub_fluxo"] = None
                            contexto["gerar_relatorio_rebanho_ativo"] = False
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
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (gestão rebanho voltar para principal): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (gestão rebanho voltar para principal): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    if gestao_rebanho_sub_fluxo is None: # User just entered Gestão de Rebanho menu
                        if mensagem_recebida == "1": # Cadastrar novo animal
                            contexto["gestao_rebanho_sub_fluxo"] = 1
                            contexto["cadastro_animal_ativo"] = True
                            contexto["registro_animal_etapa"] = 1
                            contexto["dados_animal_registro"] = {}
                            resposta = f"✅ Informe o nome ou identificação do novo animal, {nome}: 🐮\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                        elif mensagem_recebida == "2": # Controle de vacinação e vermifugação
                            contexto["gestao_rebanho_sub_fluxo"] = 2
                            contexto["vacinacao_vermifugacao_ativo"] = True
                            contexto["vacinacao_vermifugacao_opcao"] = None # Reset sub-sub-flow choice
                            resposta = (
                                f"🐄 **Controle de Vacinação e Vermifugação, {nome}** 💉🐛\n\n"
                                "O que você gostaria de fazer?\n\n"
                                "Digite:\n"
                                "1 para Registrar vacinação\n"
                                "2 para Consultar vacinação\n"
                                "3 para Registrar vermifugação\n"
                                "4 para Consultar vermifugação\n"
                                "5 para Receber lembretes futuros\n"
                                "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                            )
                        elif mensagem_recebida == "3": # Controle reprodutivo
                            contexto["gestao_rebanho_sub_fluxo"] = 3
                            contexto["controle_reprodutivo_ativo"] = True
                            resposta = f"Em breve teremos o controle reprodutivo, {nome}! Aguarde! 🤰\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True # Reusing this flag for sub-menu return
                        elif mensagem_recebida == "4": # Histórico de pesagens
                            contexto["gestao_rebanho_sub_fluxo"] = 4
                            contexto["historico_pesagens_ativo"] = True
                            resposta = f"Em breve teremos o histórico de pesagens, {nome}! Aguarde! ⚖️\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True # Reusing this flag for sub-menu return
                        elif mensagem_recebida == "5": # Consultar Animais
                            contexto["gestao_rebanho_sub_fluxo"] = 5
                            if contexto["registros_animais"]:
                                resposta = "🐄 **Seus Animais Cadastrados:** 🐄\n"
                                for i, animal in enumerate(contexto["registros_animais"]):
                                    animal_id = animal.get("animal_id", "N/A")
                                    resposta += f"{i+1}️⃣ {animal_id.capitalize()}\n"
                            else:
                                resposta = f"Você ainda não cadastrou nenhum animal, {nome}. Que tal cadastrar um novo animal? 🐮"
                            resposta += "\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            contexto["awaiting_post_completion_response"] = True # Reusing for sub-menu return
                        elif mensagem_recebida == "6": # Gerar Relatório
                            contexto["gestao_rebanho_sub_fluxo"] = 6
                            contexto["gerar_relatorio_rebanho_ativo"] = True
                            if contexto["registros_animais"]:
                                resposta = "📊 **Relatório Detalhado do Rebanho:** 📊\n\n"
                                for i, animal in enumerate(contexto["registros_animais"]):
                                    animal_id = animal.get("animal_id", "N/A")
                                    # Add more details if available (e.g., last vaccination, last weighing)
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
                                    resposta += "\n" # Add a newline for separation
                                
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
                                "1 para Cadastrar novo animal\n"
                                "2 para Controle de vacinação e vermifugação\n"
                                "3 para Controle reprodutivo\n"
                                "4 para Histórico de pesagens\n"
                                "5 para Consultar Animais\n" # New option
                                "6 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (gestão rebanho sub-menu): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (gestão rebanho sub-menu): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif cadastro_animal_ativo:
                        print(f"DEBUG_FLOW: Fluxo: cadastro_animal_ativo")
                        if "voltar" in mensagem_recebida:
                            contexto["cadastro_animal_ativo"] = False
                            contexto["registro_animal_etapa"] = None
                            contexto["dados_animal_registro"] = {}
                            contexto["gestao_rebanho_sub_fluxo"] = None # Return to Gestão de Rebanho main menu
                            resposta = (
                                f"Ok, {nome}, retornando ao menu de Gestão de Rebanho. 🐄\n\n"
                                "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                                "Digite:\n"
                                "1 para Cadastrar novo animal\n"
                                "2 para Controle de vacinação e vermifugação\n"
                                "3 para Controle reprodutivo\n"
                                "4 para Histórico de pesagens\n"
                                "5 para Consultar Animais\n" # New option
                                "6 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (cadastro animal voltar): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (cadastro animal voltar): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        if registro_animal_etapa == 1:
                            dados_animal_registro["animal_id"] = mensagem_recebida.strip()
                            # Placeholder for more questions
                            contexto["registro_animal_etapa"] = None # End of this sub-flow for now
                            contexto["cadastro_animal_ativo"] = False
                            contexto["gestao_rebanho_sub_fluxo"] = None # Return to Gestão de Rebanho main menu
                            contexto["registros_animais"].append(dados_animal_registro) # Save the new animal
                            resposta = f"✅ Animal '{dados_animal_registro['animal_id'].capitalize()}' cadastrado com sucesso, {nome}! 🎉"
                            resposta += f"\n\nO que você gostaria de fazer agora na Gestão de Rebanho, {nome}? 🐄\n\nDigite:\n1 para Cadastrar novo animal\n2 para Controle de vacinação e vermifugação\n3 para Controle reprodutivo\n4 para Histórico de pesagens\n5 para Consultar Animais\n6 para Gerar Relatório\nOu 'voltar' para o menu principal."
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (cadastro animal): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (cadastro animal): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    elif vacinacao_vermifugacao_ativo:
                        print(f"DEBUG_FLOW: Fluxo: vacinacao_vermifugacao_ativo")
                        if "voltar" in mensagem_recebida:
                            # If we are in a sub-sub-flow, go back to vac/verm sub-menu
                            if registro_vacinacao_etapa is not None or consulta_vacinacao_ativa or registro_vermifugacao_etapa is not None or consulta_vermifugacao_ativa or lembretes_vacinacao_ativo:
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
                                contexto["vacinacao_vermifugacao_opcao"] = None # Reset sub-sub-flow choice
                                resposta = (
                                    f"Ok, {nome}, retornando ao menu de Vacinação e Vermifugação. 💉🐛\n\n"
                                    "O que você gostaria de fazer?\n\n"
                                    "Digite:\n"
                                    "1 para Registrar vacinação\n"
                                    "2 para Consultar vacinação\n"
                                    "3 para Registrar vermifugação\n"
                                    "4 para Consultar vermifugação\n"
                                    "5 para Receber lembretes futuros\n"
                                    "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                )
                            else: # If we are in vac/verm sub-menu, go back to Gestão de Rebanho menu
                                contexto["vacinacao_vermifugacao_ativo"] = False
                                contexto["gestao_rebanho_sub_fluxo"] = None
                                resposta = (
                                    f"Ok, {nome}, retornando ao menu de Gestão de Rebanho. 🐄\n\n"
                                    "O que você gostaria de fazer agora na Gestão de Rebanho?\n\n"
                                    "Digite:\n"
                                    "1 para Cadastrar novo animal\n"
                                    "2 para Controle de vacinação e vermifugação\n"
                                    "3 para Controle reprodutivo\n"
                                    "4 para Histórico de pesagens\n"
                                    "5 para Consultar Animais\n" # New option
                                    "6 para Gerar Relatório\n" # New option
                                    "Ou 'voltar' para o menu principal."
                                )
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (vac/verm voltar): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (vac/verm voltar): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        if vacinacao_vermifugacao_opcao is None: # User just entered vac/verm sub-menu
                            if mensagem_recebida == "1": # Registrar vacinação
                                contexto["vacinacao_vermifugacao_opcao"] = 1
                                contexto["registro_vacinacao_etapa"] = 1
                                contexto["dados_vacinacao_registro"] = {}
                                resposta = f"✅ Informe o nome ou identificação do animal, {nome}: 🐮\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif mensagem_recebida == "2": # Consultar vacinação
                                contexto["vacinacao_vermifugacao_opcao"] = 2
                                contexto["consulta_vacinacao_ativa"] = True
                                contexto["awaiting_animal_id_consulta_vac"] = True
                                resposta = f"✅ Informe o nome ou identificação do animal que deseja consultar, {nome}: 🔍\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif mensagem_recebida == "3": # Registrar vermifugação
                                contexto["vacinacao_vermifugacao_opcao"] = 3
                                contexto["registro_vermifugacao_etapa"] = 1
                                contexto["dados_vermifugacao_registro"] = {}
                                resposta = f"✅ Informe o nome ou identificação do animal para vermifugação, {nome}: 🐛\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif mensagem_recebida == "4": # Consultar vermifugação
                                contexto["vacinacao_vermifugacao_opcao"] = 4
                                contexto["consulta_vermifugacao_ativa"] = True
                                contexto["awaiting_animal_id_consulta_verm"] = True
                                resposta = f"✅ Informe o nome ou identificação do animal que deseja consultar para vermifugação, {nome}: 🔍\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif mensagem_recebida == "5": # Receber lembretes futuros
                                contexto["vacinacao_vermifugacao_opcao"] = 5
                                contexto["lembretes_vacinacao_ativa"] = True
                                contexto["awaiting_lembretes_contato"] = True
                                resposta = f"✅ Informe seu telefone ou e-mail para envio de lembretes de próximas vacinações, {nome}: 🔔\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            else:
                                resposta = (
                                    f"Opção inválida, {nome}. Por favor, escolha uma das opções para Vacinação e Vermifugação: 💉🐛\n"
                                    "1 para Registrar vacinação\n"
                                    "2 para Consultar vacinação\n"
                                    "3 para Registrar vermifugação\n"
                                    "4 para Consultar vermifugação\n"
                                    "5 para Receber lembretes futuros\n"
                                    "Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                )
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (vac/verm sub-menu choice): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (vac/verm sub-menu choice): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif vacinacao_vermifugacao_opcao == 1: # Registro de vacinação
                            print(f"DEBUG_FLOW: Fluxo: registro_vacinacao_etapa {registro_vacinacao_etapa}")
                            if registro_vacinacao_etapa == 1:
                                dados_vacinacao_registro["animal_id"] = mensagem_recebida.strip()
                                contexto["registro_vacinacao_etapa"] = 2
                                resposta = f"✅ Qual foi a vacina aplicada, {nome}? 💉\nEx.: Aftosa, Brucelose, Raiva...\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vacinacao_etapa == 2:
                                dados_vacinacao_registro["vacina"] = mensagem_recebida.strip()
                                contexto["registro_vacinacao_etapa"] = 3
                                resposta = f"✅ Qual a data da vacinação, {nome}? 📅\nEx.: 27/05/2025\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vacinacao_etapa == 3:
                                dados_vacinacao_registro["data_vacinacao"] = mensagem_recebida.strip()
                                contexto["registro_vacinacao_etapa"] = 4
                                resposta = f"✅ Quando será a próxima dose ou reforço, {nome}? 🗓️\nEx.: 27/11/2025\n(Se não houver, responda \"não\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vacinacao_etapa == 4:
                                proxima_dose = mensagem_recebida.strip()
                                dados_vacinacao_registro["proxima_dose"] = proxima_dose if proxima_dose != "não" else "Não informado"
                                
                                # Add to vaccination records
                                contexto["registros_vacinacao"].append(dados_vacinacao_registro)

                                contexto["registro_vacinacao_etapa"] = None
                                contexto["vacinacao_vermifugacao_opcao"] = None # Reset sub-sub-flow
                                
                                # Format confirmation message
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
                                
                                # After confirmation, ask if they want to do another vaccination action or return to main menu
                                resposta += f"\n\nO que deseja fazer agora na seção de Vacinação e Vermifugação, {nome}? 💉🐛\nDigite:\n1 para Registrar outra vacinação\n2 para Consultar vacinação\n3 para Registrar vermifugação\n4 para Consultar vermifugação\n5 para Receber lembretes futuros\nOu 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                contexto["awaiting_post_completion_response"] = True # Use this flag to indicate a choice is needed
                                
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (registro vacinação etapa {registro_vacinacao_etapa}): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (registro vacinação etapa {registro_vacinacao_etapa}): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        
                        elif vacinacao_vermifugacao_opcao == 2: # Consulta de vacinação
                            print(f"DEBUG_FLOW: Fluxo: consulta_vacinacao_ativa")
                            if awaiting_animal_id_consulta_vac:
                                animal_id_consulta = mensagem_recebida.strip()
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
                                        resposta += f"{i+1}️⃣ {vacina.capitalize()} - {data_vacinacao} → Próxima: {proxima_dose}\n"
                                else:
                                    resposta = f"Não encontrei registros de vacinação para o animal '{animal_id_consulta.capitalize()}', {nome}. 🙁"
                                
                                resposta += f"\n✅ Deseja consultar outro animal, {nome}? Digite `sim` ou `não`.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                contexto["consulta_vacinacao_ativa"] = False # Deactivate this specific sub-flow
                                contexto["vacinacao_vermifugacao_opcao"] = None # Reset sub-sub-flow choice
                                contexto["awaiting_post_completion_response"] = True # Use this flag for choice
                            
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (consulta vacinação): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (consulta vacinação): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif vacinacao_vermifugacao_opcao == 3: # Registro de vermifugação
                            print(f"DEBUG_FLOW: Fluxo: registro_vermifugacao_etapa {registro_vermifugacao_etapa}")
                            if registro_vermifugacao_etapa == 1:
                                dados_vermifugacao_registro["animal_id"] = mensagem_recebida.strip()
                                contexto["registro_vermifugacao_etapa"] = 2
                                resposta = f"✅ Qual foi o vermífugo aplicado, {nome}? 🐛\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vermifugacao_etapa == 2:
                                dados_vermifugacao_registro["vermifugo"] = mensagem_recebida.strip()
                                contexto["registro_vermifugacao_etapa"] = 3
                                resposta = f"✅ Qual a data da vermifugação, {nome}? 📅\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vermifugacao_etapa == 3:
                                dados_vermifugacao_registro["data_vermifugacao"] = mensagem_recebida.strip()
                                contexto["registro_vermifugacao_etapa"] = 4
                                resposta = f"✅ Quando será a próxima dose ou reforço, {nome}? 🗓️ (Se não houver, responda \"não\")\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif registro_vermifugacao_etapa == 4:
                                proxima_dose_verm = mensagem_recebida.strip()
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
                                
                                resposta += f"\n\nO que deseja fazer agora na seção de Vacinação e Vermifugação, {nome}? 💉🐛\nDigite:\n1 para Registrar vacinação\n2 para Consultar vacinação\n3 para Registrar vermifugação\n4 para Consultar vermifugação\n5 para Receber lembretes futuros\nOu 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                contexto["awaiting_post_completion_response"] = True
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (registro vermifugação etapa {registro_vermifugacao_etapa}): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (registro vermifugação etapa {registro_vermifugacao_etapa}): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif vacinacao_vermifugacao_opcao == 4: # Consulta de vermifugação
                            print(f"DEBUG_FLOW: Fluxo: consulta_vermifugacao_ativa")
                            if awaiting_animal_id_consulta_verm:
                                animal_id_consulta = mensagem_recebida.strip()
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
                                        resposta += f"{i+1}️⃣ {vermifugo.capitalize()} - {data_vermifugacao} → Próxima: {proxima_dose}\n"
                                else:
                                    resposta = f"Não encontrei registros de vermifugação para o animal '{animal_id_consulta.capitalize()}', {nome}. 🙁"
                                
                                resposta += f"\n✅ Deseja consultar outro animal, {nome}? Digite `sim` ou `não`.\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                                contexto["consulta_vermifugacao_ativa"] = False
                                contexto["vacinacao_vermifugacao_opcao"] = None
                                contexto["awaiting_post_completion_response"] = True
                            
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (consulta vermifugação): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (consulta vermifugação): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif vacinacao_vermifugacao_opcao == 5: # Lembretes futuros
                            print(f"DEBUG_FLOW: Fluxo: lembretes_vacinacao_ativa")
                            if awaiting_lembretes_contato:
                                contato_lembretes = mensagem_recebida.strip()
                                contexto["contato_lembretes"] = contato_lembretes # Store contact for reminders
                                contexto["awaiting_lembretes_contato"] = False
                                contexto["lembretes_vacinacao_ativa"] = False # Deactivate this specific sub-flow
                                
                                resposta = f"✅ Pronto, {nome}! Você receberá lembretes sempre que um reforço de vacinação estiver próximo. 🐮📩"
                                
                                # After confirmation, ask if they want to do another vaccination action or return to main menu
                                resposta += f"\n\nO que deseja fazer agora na seção de Vacinação e Vermifugação, {nome}? 💉🐛\nDigite:\n1 para Registrar vacinação\n2 para Consultar vacinação\n3 para Registrar vermifugação\n4 para Consultar vermifugação\n5 para Receber lembretes futuros\nOu 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal."
                                contexto["awaiting_post_completion_response"] = True # Use this flag for choice
                            
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (lembretes vacinação): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (lembretes vacinação): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        
                        else: # Fallback for unexpected vac/verm sub-flow step
                            resposta = f"Ocorreu um erro no fluxo de vacinação/vermifugação, {nome}. Por favor, digite '2' para voltar ao menu de Vacinação e Vermifugação ou 'menu' para voltar ao menu principal."
                            contexto["vacinacao_vermifugacao_ativo"] = True # Keep active to allow choosing another sub-flow
                            contexto["vacinacao_vermifugacao_opcao"] = None # Reset sub-sub-flow choice
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (erro vac/verm sub-fluxo): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (erro vac/verm sub-fluxo): Status={send_status}, Resposta={send_resp}")
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
                                "1 para Cadastrar novo animal\n"
                                "2 para Controle de vacinação e vermifugação\n"
                                "3 para Controle reprodutivo\n"
                                "4 para Histórico de pesagens\n"
                                "5 para Consultar Animais\n" # New option
                                "6 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (controle reprodutivo voltar): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (controle reprodutivo voltar): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        # Placeholder for reproductive control logic
                        resposta = f"Você está no fluxo de Controle Reprodutivo, {nome}. Em breve teremos mais funcionalidades aqui! 🤰\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                        contexto["awaiting_post_completion_response"] = True # Reusing this flag for sub-menu return
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (controle reprodutivo): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (controle reprodutivo): Status={send_status}, Resposta={send_resp}")
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
                                "1 para Cadastrar novo animal\n"
                                "2 para Controle de vacinação e vermifugação\n"
                                "3 para Controle reprodutivo\n"
                                "4 para Histórico de pesagens\n"
                                "5 para Consultar Animais\n" # New option
                                "6 para Gerar Relatório\n" # New option
                                "Ou 'voltar' para o menu principal."
                            )
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (histórico pesagens voltar): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (histórico pesagens voltar): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        # Placeholder for weighing history logic
                        resposta = f"Você está no fluxo de Histórico de Pesagens, {nome}. Em breve teremos mais funcionalidades aqui! ⚖️\n\nDeseja voltar ao menu de Gestão de Rebanho? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu de Gestão de Rebanho, ou 'menu' para o principal)"
                        contexto["awaiting_post_completion_response"] = True # Reusing this flag for sub-menu return
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (histórico pesagens): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (histórico pesagens): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                    else: # Fallback for unexpected Gestão de Rebanho sub-flow step
                        resposta = f"Ocorreu um erro no fluxo de Gestão de Rebanho, {nome}. Por favor, digite '3' para iniciar a Gestão de Rebanho ou 'menu' para voltar ao menu principal."
                        contexto["gestao_rebanho_ativo"] = False
                        contexto["gestao_rebanho_sub_fluxo"] = None
                        contexto["gerar_relatorio_rebanho_ativo"] = False
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (erro gestão rebanho sub-fluxo): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (erro gestão rebanho sub-fluxo): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200


                elif registration_step: # Handles general registration flow, including editing
                    print(f"DEBUG_FLOW: Fluxo: registration_step (etapa: {registration_step})")
                    current_question_key = registration_step
                    
                    if "voltar" in mensagem_recebida:
                        if contexto.get("editing_registration"):
                            # If editing, go back to asking which field to edit
                            contexto["current_editing_field"] = None
                            contexto["awaiting_field_to_edit"] = True
                            resposta = f"Qual campo você gostaria de editar, {nome}? (Ex: 'nome completo', 'cpf', 'endereço', etc.) 📝\n\nSe preferir, posso te mostrar seus dados atuais. Diga 'meus dados'.\n(Ou 'voltar' para o menu principal)"
                        else:
                            # If in initial registration, cancel and go to main menu
                            contexto["registration_step"] = None
                            contexto["awaiting_continuation_choice"] = False
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
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (cadastro voltar): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (cadastro voltar): Status={send_status}, Resposta={send_resp}")
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
                                resposta = f"Ok, {nome}, qual é o novo valor para '{REGISTRATION_QUESTIONS[field_to_edit].replace('Qual é seu ', '').replace('Qual o seu ', '').replace('Qual a sua ', '').replace('Qual seu ', '').replace('Qual a ', '').replace('Qual o ', '').replace('Seu ', '').replace('Tem algum ', '').replace('Sua ', '').replace('Sua produção é de que tipo?', 'tipo de produção?').replace('Sua produção é orgânica?', 'produção orgânica?').replace('Utiliza irrigação?', 'utiliza irrigação?').replace('Você pode informar várias, ex: milho, feijão, mandioca...', '')}'? ✏️\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            elif "meus dados" in mensagem_recebida:
                                dados_atuais = f"Seus dados de cadastro atuais, {nome}: 📋\n"
                                for key, question in REGISTRATION_QUESTIONS.items():
                                    value = contexto.get(key, "Não preenchido")
                                    dados_atuais += f"- {question.replace('Qual é seu ', '').replace('Qual o seu ', '').replace('Qual a sua ', '').replace('Qual seu ', '').replace('Qual a ', '').replace('Qual o ', '').replace('Seu ', '').replace('Tem algum ', '').replace('Sua ', '').replace('Sua produção é de que tipo?', 'tipo de produção?').replace('Sua produção é orgânica?', 'produção orgânica?').replace('Utiliza irrigação?', 'utiliza irrigação?').replace('Você pode informar várias, ex: milho, feijão, mandioca...', '')}: {value}\n"
                                resposta = f"{dados_atuais}\nQual campo você gostaria de editar agora, {nome}? Ou diga 'concluído' para finalizar a edição. ✅\n(Ou 'voltar' para o menu principal)"
                            elif "concluído" in mensagem_recebida or "concluido" in mensagem_recebida:
                                contexto["editing_registration"] = False
                                contexto["awaiting_field_to_edit"] = False
                                contexto["current_editing_field"] = None
                                contexto["registration_step"] = None
                                contexto["awaiting_post_completion_response"] = True
                                resposta = f"Edição de cadastro concluída, {nome}! 🎉 Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                            else:
                                resposta = f"Não entendi qual campo você deseja editar, {nome}. Por favor, diga o nome do campo (ex: 'nome completo', 'cpf', 'email') ou diga 'meus dados' para ver o que já está preenchido. 🤔\n(Ou 'voltar' para o menu principal)"
                            save_conversation_context(numero, contexto)
                            print(f"DEBUG_FLOW: Resposta gerada (edição de cadastro): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (edição de cadastro): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200

                        elif contexto.get("current_editing_field"):
                            field_to_update = contexto["current_editing_field"]
                            contexto[field_to_update] = mensagem_recebida.strip()
                            contexto["current_editing_field"] = None # Reset
                            contexto["awaiting_field_to_edit"] = True # Go back to asking which field to edit
                            save_conversation_context(numero, contexto)
                            resposta = f"'{REGISTRATION_QUESTIONS[field_to_update].replace('Qual é seu ', '').replace('Qual o seu ', '').replace('Qual a sua ', '').replace('Qual seu ', '').replace('Qual a ', '').replace('Qual o ', '').replace('Seu ', '').replace('Tem algum ', '').replace('Sua ', '').replace('Sua produção é de que tipo?', 'tipo de produção?').replace('Sua produção é orgânica?', 'produção orgânica?').replace('Utiliza irrigação?', 'utiliza irrigação?').replace('Você pode informar várias, ex: milho, feijão, mandioca...', '')}' atualizado para: {mensagem_recebida.strip()}, {nome}. ✅\n\nDeseja editar outro campo ou diga 'concluído' para finalizar a edição? 🤔\n(Ou 'voltar' para o menu anterior, ou 'menu' para o principal)"
                            print(f"DEBUG_FLOW: Resposta gerada (campo editado): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (campo editado): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                        else: # Just entered editing mode, ask which field to edit
                            contexto["awaiting_field_to_edit"] = True
                            save_conversation_context(numero, contexto)
                            resposta = f"Qual campo você gostaria de editar, {nome}? (Ex: 'nome completo', 'cpf', 'endereço', etc.) 📝\n\nSe preferir, posso te mostrar seus dados atuais. Diga 'meus dados'.\n(Ou 'voltar' para o menu principal)"
                            print(f"DEBUG_FLOW: Resposta gerada (início da edição): {resposta}")
                            send_status, send_resp = send_whatsapp_message(numero, resposta)
                            print(f"DEBUG_FLOW: Resultado do envio (início da edição): Status={send_status}, Resposta={send_resp}")
                            return jsonify({"status": "sucesso", "resposta": resposta}), 200
                    
                    else: # Not editing, in initial registration flow
                        contexto[current_question_key] = mensagem_recebida.strip()
                        save_conversation_context(numero, contexto)

                        next_question_index = REGISTRATION_ORDER.index(current_question_key) + 1
                        if next_question_index < len(REGISTRATION_ORDER):
                            next_question_key = REGISTRATION_ORDER[next_question_index]
                            contexto["registration_step"] = next_question_key
                            save_conversation_context(numero, contexto)
                            resposta = f"{REGISTRATION_QUESTIONS[next_question_key]}\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                        else:
                            contexto["registration_step"] = None
                            contexto["awaiting_post_completion_response"] = True
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
                            # Novas flags de estoque
                            contexto["registro_entrada_estoque_ativo"] = False
                            contexto["registro_entrada_estoque_etapa"] = None
                            contexto["dados_entrada_estoque_registro"] = {}
                            contexto["registro_saida_estoque_ativo"] = False
                            contexto["registro_saida_estoque_etapa"] = None
                            contexto["dados_saida_estoque_registro"] = {}
                            contexto["consulta_estoque_ativa"] = False
                            save_conversation_context(numero, contexto)
                            resposta = f"Cadastro concluído com sucesso, {nome}! 🎉 Posso ajudar com mais alguma coisa? (Responda 'sim' ou 'não')"
                        print(f"DEBUG_FLOW: Resposta gerada (cadastro concluído): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                            
                        print(f"DEBUG_FLOW: Resultado do envio (cadastro concluído): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200
                
                elif awaiting_weather_location: # This must be after other flows, as it expects a city name
                    print(f"DEBUG_FLOW: Fluxo: awaiting_weather_location")
                    city_match_explicit = re.search(r"(?:clima|previsão|tempo)\s+(?:em|para)\s+([a-zA-Z\u00C0-\u017F\s-]+)", mensagem_recebida)
                    cidade_solicitada_from_message = ""

                    if mensagem_recebida.strip() and not mensagem_recebida.strip().isdigit():
                        cidade_solicitada_from_message = mensagem_recebida.strip()
                    
                    if city_match_explicit:
                        cidade_solicitada_from_message = city_match_explicit.group(1).strip()

                    if cidade_solicitada_from_message:
                        pais_solicitado = "BR" # Assuming Brazil for now, can be expanded
                        resposta_clima = format_weather_response(cidade_solicitada_from_message, pais_solicitado)
                        contexto["awaiting_weather_location"] = False
                        contexto["awaiting_weather_follow_up_choice"] = True
                        contexto["localizacao"] = {"cidade": cidade_solicitada_from_message, "estado": "", "pais": pais_solicitado} # State might be unknown, but city is key
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (clima por cidade): {resposta_clima}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta_clima)
                        print(f"DEBUG_FLOW: Resultado do envio (clima por cidade): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta_clima}), 200
                    else:
                        resposta = f"Não entendi, {nome}. Por favor, me diga o nome da cidade (ex: 'São Paulo') ou compartilhe sua localização atual pelo WhatsApp. 📍\n(Ou 'voltar' para o menu principal)"
                        save_conversation_context(numero, contexto)
                        print(f"DEBUG_FLOW: Resposta gerada (re-prompt localização): {resposta}")
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"DEBUG_FLOW: Resultado do envio (re-prompt localização): Status={send_status}, Resposta={send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # 2. Handle Main Menu Options (using exact match for numbers) - UPDATED ORDER
                # These should be checked *before* the initial greeting logic or general fallback.
                elif mensagem_recebida == "1" or "clima" in mensagem_recebida or "previsão climática" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 1 - Previsão Climática selecionada.")
                    # Verifica se já temos uma localização salva no contexto
                    if localizacao and localizacao.get("cidade"):
                        cidade_salva = localizacao["cidade"]
                        pais_salvo = localizacao["pais"]
                        resposta = format_weather_response(cidade_salva, pais_salvo)
                        contexto["awaiting_weather_location"] = False # Não precisa pedir novamente
                        contexto["awaiting_weather_follow_up_choice"] = True # Pergunta se quer outra consulta
                        # Resetar flags de outros fluxos
                        contexto["awaiting_menu_return_prompt"] = False
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
                        # Novas flags de estoque
                        contexto["registro_entrada_estoque_ativo"] = False
                        contexto["registro_entrada_estoque_etapa"] = None
                        contexto["dados_entrada_estoque_registro"] = {}
                        contexto["registro_saida_estoque_ativo"] = False
                        contexto["registro_saida_estoque_etapa"] = None
                        contexto["dados_saida_estoque_registro"] = {}
                        contexto["consulta_estoque_ativa"] = False
                    else:
                        resposta = f"Para qual cidade você gostaria da previsão climática, {nome}? Você também pode compartilhar sua localização. 📍\n(Ou 'voltar' para o menu principal)"
                        contexto["awaiting_weather_location"] = True
                        # Resetar flags de outros fluxos
                        contexto["awaiting_menu_return_prompt"] = False
                        contexto["awaiting_weather_follow_up_choice"] = False
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
                        # Novas flags de estoque
                        contexto["registro_entrada_estoque_ativo"] = False
                        contexto["registro_entrada_estoque_etapa"] = None
                        contexto["dados_entrada_estoque_registro"] = {}
                        contexto["registro_saida_estoque_ativo"] = False
                        contexto["registro_saida_estoque_etapa"] = None
                        contexto["dados_saida_estoque_registro"] = {}
                        contexto["consulta_estoque_ativa"] = False
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 1): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 1): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida == "2" or "controle de estoque" in mensagem_recebida or "estoque" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 2 - Controle de Estoque selecionada.")
                    # Reset other awaiting flags
                    contexto["awaiting_menu_return_prompt"] = False
                    contexto["awaiting_weather_location"] = False
                    contexto["awaiting_weather_follow_up_choice"] = False
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False
                    contexto["gerar_relatorio_estoque_ativo"] = False


                    contexto["controle_estoque_ativo"] = True
                    contexto["controle_estoque_sub_fluxo"] = None # Not yet in a sub-flow
                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                    save_conversation_context(numero, contexto)
                    resposta = (
                        f"📦 **Controle de Estoque, {nome}** 📦\n\n"
                        "O que você gostaria de fazer?\n\n"
                        "1 para Registrar Entrada de Insumos/Produtos\n"
                        "2 para Registrar Saída de Insumos/Produtos\n"
                        "3 para Consultar Estoque\n"
                        "4 para Avisos de estoque baixo\n"
                        "5 para Gerar Relatório\n" # New option
                        "Ou 'voltar' para o menu principal."
                    )
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 2 - controle de estoque): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 2 - controle de estoque): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida == "3" or "gestão de rebanho" in mensagem_recebida or "gestao de rebanho" in mensagem_recebida or "rebanho" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 3 - Gestão de Rebanho selecionada.")
                    # Reset other awaiting flags
                    contexto["awaiting_menu_return_prompt"] = False
                    contexto["awaiting_weather_location"] = False
                    contexto["awaiting_weather_follow_up_choice"] = False
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False


                    contexto["gestao_rebanho_ativo"] = True
                    contexto["gestao_rebanho_sub_fluxo"] = None # Not yet in a sub-flow
                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                    save_conversation_context(numero, contexto)
                    resposta = (
                        f"Olá, {nome}! 👋 Vamos gerenciar seu rebanho. 🐄\n\n"
                        "O que você gostaria de fazer?\n\n"
                        "1 para Cadastrar novo animal\n"
                        "2 para Controle de vacinação e vermifugação\n"
                        "3 para Controle reprodutivo\n"
                        "4 para Histórico de pesagens\n"
                        "5 para Consultar Animais\n" # New option
                        "6 para Gerar Relatório\n" # New option
                        "Ou 'voltar' para o menu principal."
                    )
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 3 - gestão de rebanho): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 3 - gestão de rebanho): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida == "4" or "simulação de safra" in mensagem_recebida or "safra" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 4 - Simulação de Safra selecionada.")
                    contexto["awaiting_menu_return_prompt"] = False
                    contexto["awaiting_weather_location"] = False
                    contexto["awaiting_weather_follow_up_choice"] = False
                    contexto["registration_step"] = None
                    contexto["editing_registration"] = False
                    contexto["awaiting_field_to_edit"] = False
                    contexto["current_editing_field"] = None
                    contexto["awaiting_post_completion_response"] = False
                    contexto["simulacao_safra_ativa"] = True # Keep this active to handle sub-menu
                    contexto["etapa_simulacao"] = None # Reset step for initial menu
                    contexto["dados_simulacao"] = {}
                    contexto["awaiting_safra_finalizacao"] = False
                    contexto["simulacao_sub_fluxo"] = None # Not yet in a sub-flow
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False

                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                    save_conversation_context(numero, contexto)
                    resposta = (
                        f"🌾 **Simulação de Safra, {nome}** 🌾\n\n"
                        "O que você gostaria de fazer?\n\n"
                        "1 para Iniciar nova simulação\n"
                        "2 para Consultar Simulações Anteriores\n" # New option
                        "3 para Gerar Relatório\n" # New option
                        "Ou 'voltar' para o menu principal."
                    )
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 4 - simulação de safra): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 4 - simulação de safra): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida == "5" or "cadastro" in mensagem_recebida or "cadastra-se" in mensagem_recebida or "editar dados" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 5 - Cadastro/Editar selecionada.")
                    contexto["awaiting_menu_return_prompt"] = False
                    contexto["awaiting_weather_location"] = False
                    contexto["awaiting_weather_follow_up_choice"] = False
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False

                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                    if usuario_cadastrado:
                        contexto["registration_step"] = "nome_completo"
                        contexto["editing_registration"] = True
                        resposta = f"Entendido, {nome}! Você deseja editar seus dados de cadastro. Qual campo você gostaria de editar? (Ex: 'nome completo', 'cpf', 'endereço', etc.) 📝\n\nSe preferir, posso te mostrar seus dados atuais. Diga 'meus dados'.\n(Ou 'voltar' para o menu principal)"
                    else:
                        # If user is not registered and explicitly chooses option 5, start full registration from scratch
                        contexto["registration_step"] = REGISTRATION_ORDER[0]
                        contexto["editing_registration"] = False
                        resposta = f"Ótimo, {nome}! Vamos começar seu cadastro. {REGISTRATION_QUESTIONS[contexto['registration_step']]}\n(Ou 'voltar' para cancelar o cadastro, ou 'menu' para o principal)"
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 5 - cadastrar/editar): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 5 - cadastrar/editar): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida == "6" or "alertas" in mensagem_recebida or "pragas" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 6 - Alertas de Pragas selecionada.")
                    resposta = f"Em breve teremos alertas de pragas para a sua região, {nome}! Fique ligado! 🐛\nDeseja voltar ao menu principal? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu principal)"
                    contexto["awaiting_menu_return_prompt"] = True
                    contexto["awaiting_weather_location"] = False
                    contexto["awaiting_weather_follow_up_choice"] = False
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False
                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 6): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 6): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida == "7" or "análise de mercado" in mensagem_recebida or "mercado" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 7 - Análise de Mercado selecionada.")
                    resposta = f"Em breve teremos análises de mercado para te ajudar a tomar as melhores decisões, {nome}! Aguarde! 📈\nDeseja voltar ao menu principal? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu principal)"
                    contexto["awaiting_menu_return_prompt"] = True
                    contexto["awaiting_weather_location"] = False
                    contexto["awaiting_weather_follow_up_choice"] = False
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False
                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 7): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 7): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif mensagem_recebida == "8" or "localização" in mensagem_recebida or "minha localização" in mensagem_recebida or "onde estou" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 8 - Localização selecionada.")
                    contexto["awaiting_menu_return_prompt"] = False
                    contexto["awaiting_weather_follow_up_choice"] = False
                    contexto["registration_step"] = None
                    contexto["editing_registration"] = False
                    contexto["awaiting_field_to_edit"] = False
                    contexto["current_editing_field"] = None
                    contexto["awaiting_post_completion_response"] = False
                    contexto["simulacao_safra_ativa"] = False
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False
    
                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                    if localizacao and localizacao.get("cidade"):
                        resposta = (
                            f"Sua localização atual registrada é: {localizacao['cidade']}, {localizacao['estado']}, {localizacao['pais']}, {nome}. 📍\n"
                            f"Deseja atualizar sua localização? Se sim, por favor, compartilhe sua localização atual ou me diga o nome da cidade.\n(Ou 'voltar' para o menu principal)"
                        )
                    else:
                        resposta = f"Não tenho sua localização registrada, {nome}. Por favor, me diga o nome da sua cidade ou compartilhe sua localização atual pelo WhatsApp para que eu possa te ajudar melhor. 📍\n(Ou 'voltar' para o menu principal)"
                    contexto["awaiting_weather_location"] = True # Reusing this flag to await location input
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 8 - localização): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 8 - localização): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200
                
                elif mensagem_recebida == "9" or "outras informações" in mensagem_recebida or "outras" in mensagem_recebida:
                    print(f"DEBUG_MAIN_MENU: Opção 9 - Outras Informações selecionada.")
                    resposta = f"Posso te ajudar com dúvidas gerais sobre agricultura, dicas de cultivo, ou qualquer outra informação que precisar, {nome}. Qual sua dúvida? 💡\nDeseja voltar ao menu principal? (Responda 'sim' ou 'não')\n(Ou 'voltar' para o menu principal)"
                    contexto["awaiting_menu_return_prompt"] = True
                    contexto["awaiting_weather_location"] = False
                    contexto["awaiting_weather_follow_up_choice"] = False
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
                    # Novas flags de estoque
                    contexto["registro_entrada_estoque_ativo"] = False
                    contexto["registro_entrada_estoque_etapa"] = None
                    contexto["dados_entrada_estoque_registro"] = {}
                    contexto["registro_saida_estoque_ativo"] = False
                    contexto["registro_saida_estoque_etapa"] = None
                    contexto["dados_saida_estoque_registro"] = {}
                    contexto["consulta_estoque_ativa"] = False
                    contexto["initial_greeting_step"] = "completed" # <<<< IMPORTANT CHANGE HERE
                    save_conversation_context(numero, contexto)
                    print(f"DEBUG_MAIN_MENU: Resposta gerada (opção 9): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_MAIN_MENU: Resultado do envio (opção 9): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200
                
                # 4. General OpenAI Fallback (if nothing else matched)
                else:
                    print(f"DEBUG_FALLBACK: Nenhum fluxo específico ativo. Tentando saudação ou OpenAI fallback.")
                    cumprimentos = ["bom dia", "boa tarde", "boa noite", "olá", "oi"]
                    is_greeting = any(c in mensagem_recebida for c in cumprimentos) or "tudo bem" in mensagem_recebida

                    # Define se algum fluxo específico está ativo (re-avaliado aqui para o caso de não ter entrado em nenhum dos 'elif' acima)
                    is_any_flow_active = (
                        awaiting_continuation_choice or
                        awaiting_weather_follow_up_choice or
                        awaiting_menu_return_prompt or
                        awaiting_weather_location or
                        registration_step is not None or
                        contexto.get("editing_registration", False) or
                        contexto.get("awaiting_field_to_edit", False) or
                        awaiting_post_completion_response or
                        simulacao_safra_ativa or
                        awaiting_safra_finalizacao or
                        simulacao_sub_fluxo is not None or
                        gerar_relatorio_simulacao_ativo or
                        gestao_rebanho_ativo or # Adicionado para gestão de rebanho
                        gestao_rebanho_sub_fluxo is not None or
                        gerar_relatorio_rebanho_ativo or
                        controle_estoque_ativo or # Adicionado para controle de estoque
                        controle_estoque_sub_fluxo is not None or
                        gerar_relatorio_estoque_ativo or
                        registro_entrada_estoque_ativo or
                        registro_saida_estoque_ativo or
                        consulta_estoque_ativa
                    )

                    # Only show full menu if it's a greeting and no other flow is active AND initial_greeting_step is "completed"
                    if is_greeting and not is_any_flow_active and initial_greeting_step == "completed":
                        resposta = (
                            f"Olá, {nome}! Eu sou a Iagro, agente de IA da Campo Inteligente. 👋 "
                            f"Estou aqui para ajudar você com sua produção agrícola!\n\n"
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
                    else: # General OpenAI fallback if no specific flow or menu option was matched
                        prompt = (
                            f"Você é a Iagro, assistente virtual da Campo Inteligente. "
                            f"O usuário disse: {mensagem_recebida}\n"
                        )
                        if localizacao and localizacao.get("cidade"):
                            prompt += f"A localização atual do usuário é: {localizacao['cidade']}, {localizacao['estado']}, {localizacao['pais']}.\n"
                        
                        prompt += (
                            f"Responda de forma amigável e útil, oferecendo ajuda com temas agrícolas ou direcionando para as opções do menu principal se a pergunta for genérica e não se encaixar em nenhum fluxo específico. "
                            f"Se a pergunta não se encaixar em nada, diga 'Posso te ajudar com mais alguma coisa? Se quiser ver as opções do menu principal, digite 'menu' ou 'opções'.'"
                        )
                        try:
                            response = openai.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=200,
                                temperature=0.7,
                            )
                            resposta = response.choices[0].message.content.strip()
                        except openai.APIError as e:
                            print(f"DEBUG_FALLBACK_ERROR: Erro na API do OpenAI: {e}")
                            resposta = "Desculpe, a API do OpenAI está temporariamente indisponível."
                        except Exception as e:
                            print(f"DEBUG_FALLBACK_ERROR: Erro ao chamar OpenAI: {e}")
                            resposta = "Desculpe, tive um problema ao processar sua mensagem."
                    
                    print(f"DEBUG_FALLBACK: Resposta gerada (resposta OpenAI ou menu inicial): {resposta}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"DEBUG_FALLBACK: Resultado do envio (resposta OpenAI ou menu inicial): Status={send_status}, Resposta={send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200
                
        return jsonify({"status": "ignorado", "motivo": "Evento não processado ou dados incompletos."}), 200

    except Exception as e:
        print(f"DEBUG_WEBHOOK_GLOBAL_ERROR: Erro inesperado no webhook: {e}")
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
