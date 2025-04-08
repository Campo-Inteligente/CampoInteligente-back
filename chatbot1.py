import os
import requests
import openai
import openpyxl
from datetime import datetime
import locale
from twilio.rest import Client
from dotenv import load_dotenv


# Carregar variáveis de ambiente
load_dotenv()

# Definir localidade para datas
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

# Variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Inicializar APIs
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
client_twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Data e hora atual formatadas
def obter_data_hora():
    agora = datetime.now()
    data = agora.strftime("%d de %B de %Y")
    dias_semana = {
        "Monday": "segunda-feira", "Tuesday": "terça-feira", "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira", "Friday": "sexta-feira", "Saturday": "sábado", "Sunday": "domingo"
    }
    dia_semana = dias_semana.get(agora.strftime("%A"), agora.strftime("%A"))
    return data, dia_semana

# Localização via IP
def obter_localizacao_via_ip():
    try:
        r = requests.get("http://ip-api.com/json/")
        d = r.json()
        if d['status'] == 'success':
            return (
                f"📍 Sua localização aproximada:\n"
                f"🌎 País: {d['country']}\n"
                f"🏙️ Estado: {d['regionName']}\n"
                f"🏘️ Cidade: {d['city']}\n"
                f"📡 IP: {d['query']}"
            )
        return "Não foi possível determinar sua localização."
    except Exception as e:
        return f"Erro ao obter localização: {e}"

# Previsão do tempo atual
def obter_previsao_tempo():
    cidade = input("Informe a cidade: ").strip()
    pais = input("Informe o país (ex: BR): ").strip().upper()
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url)
        d = r.json()
        if r.status_code != 200:
            return f"Não encontrei previsão para '{cidade}, {pais}'."
        return (
            f"🌦️ Previsão para {cidade}:\n"
            f"📌 {d['weather'][0]['description'].capitalize()}\n"
            f"🌡️ Temp: {d['main']['temp']}°C | Sensação: {d['main']['feels_like']}°C\n"
            f"💧 Umidade: {d['main']['humidity']}%\n"
            f"🌬️ Vento: {d['wind']['speed']} m/s"
        )
    except Exception as e:
        return f"Erro: {e}"

# Previsão de 3 dias
def obter_previsao_estendida():
    cidade = input("Cidade: ").strip()
    pais = input("País (ex: BR): ").strip().upper()
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={cidade},{pais}&cnt=3&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url)
        d = r.json()
        if r.status_code != 200:
            return f"Não encontrei previsão para '{cidade}, {pais}'."
        previsoes = []
        for dia in d["list"]:
            data = datetime.utcfromtimestamp(dia["dt"]).strftime("%d/%m/%Y")
            previsoes.append(
                f"📅 {data}: {dia['weather'][0]['description'].capitalize()}\n"
                f"🌡️ Mín: {dia['main']['temp_min']}°C | Máx: {dia['main']['temp_max']}°C"
            )
        return "🌤️ Previsão Estendida:\n" + "\n\n".join(previsoes)
    except Exception as e:
        return f"Erro: {e}"

# Chatbot IA - OpenAI
# Chatbot IA - OpenAI
def enviar_mensagem(mensagem, incluir_localizacao=True, incluir_previsao=True):
    try:
        # Obter localização
        localizacao = obter_localizacao_via_ip() if incluir_localizacao else ""
        
        # Obter previsão do tempo (baseada na cidade detectada ou default)
        previsao = ""
        if incluir_previsao:
            try:
                # Tentativa de extrair cidade da localização
                r = requests.get("http://ip-api.com/json/")
                d = r.json()
                cidade = d.get('city', '')
                pais = d.get('countryCode', 'BR')
                if cidade:
                    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
                    tempo = requests.get(url).json()
                    if tempo.get('weather'):
                        previsao = (
                            f"\n📡 Clima Atual em {cidade}:\n"
                            f"{tempo['weather'][0]['description'].capitalize()}, "
                            f"{tempo['main']['temp']}°C, sensação de {tempo['main']['feels_like']}°C, "
                            f"umidade de {tempo['main']['humidity']}%, vento a {tempo['wind']['speed']} m/s.\n"
                        )
            except Exception:
                previsao = "\n⚠️ Não foi possível carregar os dados do clima.\n"

        # Montar prompt final com informações adicionais
        prompt = (
            "Você é um assistente agrícola no sistema Campo Inteligente.\n"
            f"{localizacao}\n"
            f"{previsao}\n"
            f"Pergunta: {mensagem}"
        )

        resposta = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro com o OpenAI: {e}"


# Respostas frequentes
def respostas_frequentes(pergunta):
    perguntas = {
        "como me cadastrar?": "Basta informar seu nome e localização.",
        "quais as funcionalidades do sistema?": "Cadastro, IA agrícola e previsão do tempo.",
        "que dia é hoje?": f"Hoje é {obter_data_hora()[0]}, {obter_data_hora()[1]}."
    }
    return perguntas.get(pergunta.lower())

# Salvar em planilha
def salvar_planilha(dados):
    arquivo = "respostas_agricultores_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Respostas"
    ws.append(["Nome", "Localização", "Data", "Dia da Semana"])
    for linha in dados:
        ws.append(linha)
    wb.save(arquivo)
    print(f"📁 Dados salvos em {arquivo}")

# Cadastro de agricultor
def coletar_dados():
    dados = []
    while True:
        nome = input("Nome: ").strip()
        if not nome: print("❌ Nome não pode ser vazio."); continue
        localizacao = input("Localização: ").strip()
        if not localizacao: print("❌ Localização não pode ser vazia."); continue
        data, dia = obter_data_hora()
        dados.append([nome, localizacao, data, dia])
        if input("Adicionar outro? (s/n): ").lower() != 's':
            break
    salvar_planilha(dados)

# Perguntas interativas
def fluxo_perguntas():
    while True:
        pergunta = input("Pergunte algo (ou 'sair'): ").strip()
        if pergunta.lower() == 'sair': break
        termos_localizacao = ["onde estou", "qual minha localização", "me localiza", "minha cidade"]
        resposta = (
            obter_localizacao_via_ip() if any(t in pergunta for t in termos_localizacao)
            else respostas_frequentes(pergunta) or enviar_mensagem(pergunta)
        )
        print(f"🤖 {resposta}")
        if input("Outra pergunta? (s/n): ").lower() != 's': break

# Enviar mensagem WhatsApp via Twilio
def enviar_mensagem_whatsapp(mensagem, numero_destino):
    try:
        resposta = enviar_mensagem(mensagem)
        client_twilio.messages.create(
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{numero_destino}",
            body=resposta
        )
        print("✅ Mensagem enviada com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar WhatsApp: {e}")

# Menu principal
def menu_inicial():
    while True:
        print("\n=== MENU CAMPO INTELIGENTE ===")
        print("1 - Cadastrar Agricultor")
        print("2 - Perguntar ao Chatbot")
        print("3 - Obter Previsão do Tempo")
        print("4 - Previsão Estendida (3 dias)")
        print("5 - Enviar Mensagem WhatsApp")
        print("6 - Ver Localização Atual")
        print("7 - Sair")
        escolha = input("Escolha: ").strip()
        if escolha == "1": coletar_dados()
        elif escolha == "2": fluxo_perguntas()
        elif escolha == "3": print(obter_previsao_tempo())
        elif escolha == "4": print(obter_previsao_estendida())
        elif escolha == "5":
            numero = input("Número (ex: +55...): ").strip()
            msg = input("Mensagem: ").strip()
            enviar_mensagem_whatsapp(msg, numero)
        elif escolha == "6": print(obter_localizacao_via_ip())
        elif escolha == "7": print("👋 Até logo!"); break
        else: print("❌ Opção inválida.")

# Iniciar programa
if __name__ == "__main__":
    menu_inicial()
