import os
import requests
import openai
import openpyxl
from datetime import datetime
import locale
from twilio.rest import Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Definir a localidade para português do Brasil
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

# Obter chaves de API das variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # Chave da OpenWeather

# Inicializar o cliente da OpenAI
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)

# Função para obter a data e hora no formato desejado
def obter_data_hora():
    data_atual = datetime.now()
    data_formatada = data_atual.strftime("%d de %B de %Y")
    dia_da_semana = data_atual.strftime("%A")
    dias_semana = {
        "Monday": "segunda-feira", "Tuesday": "terça-feira", "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira", "Friday": "sexta-feira", "Saturday": "sábado", "Sunday": "domingo"
    }
    return data_formatada, dias_semana.get(dia_da_semana, dia_da_semana)

# Função para obter a previsão do tempo atual
def obter_previsao_tempo():
    cidade = input("Informe a cidade: ").strip()
    pais = input("Informe o país (ex: BR para Brasil): ").strip().upper()
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        if resposta.status_code != 200:
            return f"Não encontrei a previsão para '{cidade}, {pais}'. Verifique a ortografia e tente novamente."
        temperatura = dados["main"]["temp"]
        sensacao = dados["main"]["feels_like"]
        umidade = dados["main"]["humidity"]
        vento = dados["wind"]["speed"]
        descricao = dados["weather"][0]["description"].capitalize()
        return (
            f"🌦️ Previsão para {cidade}, {pais}:\n"
            f"📌 {descricao}\n"
            f"🌡️ Temperatura: {temperatura}°C\n"
            f"🥵 Sensação térmica: {sensacao}°C\n"
            f"💧 Umidade: {umidade}%\n"
            f"🌬️ Vento: {vento} m/s"
        )
    except Exception as e:
        return f"Erro ao obter previsão do tempo: {e}"

# Função para previsão estendida de 3 dias
def obter_previsao_estendida():
    cidade = input("Informe a cidade: ").strip()
    pais = input("Informe o país (ex: BR para Brasil): ").strip().upper()
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={cidade},{pais}&cnt=3&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        if resposta.status_code != 200:
            return f"Não encontrei a previsão para '{cidade}, {pais}'. Verifique a ortografia e tente novamente."
        previsoes = []
        for dia in dados["list"]:
            data = datetime.utcfromtimestamp(dia["dt"]).strftime("%d/%m/%Y")
            descricao = dia["weather"][0]["description"].capitalize()
            temperatura_min = dia["main"]["temp_min"]
            temperatura_max = dia["main"]["temp_max"]
            previsoes.append(
                f"📅 {data}: {descricao}\n"
                f"🌡️ Mín: {temperatura_min}°C | Máx: {temperatura_max}°C"
            )
        return f"🌤️ Previsão estendida para {cidade}, {pais}:\n" + "\n\n".join(previsoes)
    except Exception as e:
        return f"Erro ao obter previsão estendida: {e}"

# Função para enviar mensagens para o modelo GPT
def enviar_mensagem(mensagem):
    prompt = f"Você está conversando com um agricultor no sistema do Campo Inteligente. Pergunta: {mensagem}"
    try:
        resposta = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro na API do OpenAI: {e}"

# Função para salvar dados em planilha
def salvar_planilha(dados):
    nome_arquivo = "respostas_agricultores_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Respostas"
    ws.append(["Nome", "Localização", "Data", "Dia da Semana"])
    for resposta in dados:
        ws.append(resposta)
    wb.save(nome_arquivo)

# Função para coletar dados do agricultor
def coletar_dados():
    dados = []
    while True:
        nome = input("Digite seu nome: ").strip()
        if not nome:
            print("Nome não pode ser vazio.")
            continue
        localizacao = input("Informe sua localização: ").strip()
        if not localizacao:
            print("Localização não pode ser vazia.")
            continue
        data, dia = obter_data_hora()
        dados.append([nome, localizacao, data, dia])
        if input("Adicionar mais? (s/n): ").strip().lower() != 's':
            break
    salvar_planilha(dados)
    print("Dados salvos com sucesso!")

# Perguntas frequentes
def respostas_frequentes(pergunta):
    perguntas_freq = {
        "como me cadastrar?": "Para se cadastrar, informe seu nome e localização.",
        "quais as funcionalidades do sistema?": "Cadastrar agricultores, interagir com o chatbot e obter previsões do tempo.",
        "que dia é hoje?": f"Hoje é {obter_data_hora()[0]}, {obter_data_hora()[1]}."
    }
    return perguntas_freq.get(pergunta.lower())

# Chatbot
def fluxo_perguntas():
    while True:
        pergunta = input("Pergunte algo: ").strip().lower()
        if pergunta == 'sair':
            print("Saindo do chatbot.")
            break
        resposta = respostas_frequentes(pergunta) or enviar_mensagem(pergunta)
        print(f"Chatbot: {resposta}")
        if input("Outra pergunta? (s/n): ").strip().lower() != 's':
            break

# Enviar WhatsApp
def enviar_mensagem_whatsapp(mensagem, numero):
    client_twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    mensagem_enviada = client_twilio.messages.create(
        body=mensagem,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f'whatsapp:{numero}'
    )
    return mensagem_enviada.sid

# Menu inicial
def menu_inicial():
    while True:
        print("\n1 - Cadastrar Agricultor")
        print("2 - Perguntar ao Chatbot")
        print("3 - Obter Previsão do Tempo")
        print("4 - Obter Previsão Estendida (3 dias)")
        print("5 - Enviar mensagem pelo WhatsApp")
        print("6 - Sair")
        escolha = input("Opção: ").strip()
        if escolha == "1":
            coletar_dados()
        elif escolha == "2":
            fluxo_perguntas()
        elif escolha == "3":
            print(obter_previsao_tempo())
        elif escolha == "4":
            print(obter_previsao_estendida())
        elif escolha == "5":
            numero_destino = input("Número do agricultor (formato +55...): ")
            mensagem = input("Mensagem a enviar: ")
            enviar_mensagem_whatsapp(mensagem, numero_destino)
            print("Mensagem enviada com sucesso!")
        elif escolha == "6":
            print("Até logo!")
            break
        else:
            print("Opção inválida.")

# Início do programa
if __name__ == "__main__":
    menu_inicial()
