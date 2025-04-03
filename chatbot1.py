import os
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

# Obter as chaves de API da variável de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Inicializar o cliente da OpenAI
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)

# Função para obter a data e hora no formato desejado
def obter_data_hora():
    data_atual = datetime.now()
    data_formatada = data_atual.strftime("%d de %B de %Y")  # Ex: 24 de março de 2025
    dia_da_semana = data_atual.strftime("%A")  # Ex: domingo

    # Garantindo que o dia da semana esteja em português
    dias_semana = {
        "Monday": "segunda-feira",
        "Tuesday": "terça-feira",
        "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira",
        "Friday": "sexta-feira",
        "Saturday": "sábado",
        "Sunday": "domingo"
    }
    dia_da_semana = dias_semana.get(dia_da_semana, dia_da_semana)  # Converte se necessário

    return data_formatada, dia_da_semana

# Função para enviar mensagens para o modelo GPT
def enviar_mensagem(mensagem):
    prompt_personalizado = f"Você está conversando com um agricultor no sistema do Campo Inteligente. Responda de forma clara e objetiva sobre cadastro, funcionalidades do sistema, ou uso agrícola. Pergunta: {mensagem}"
    try:
        resposta = client_openai.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt_personalizado}],
            max_tokens=150,
            temperature=0.5
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro na API do OpenAI: {e}"

# Função para salvar dados em uma planilha Excel com nome único
def salvar_planilha(dados):
    nome_arquivo = "respostas_agricultores_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Respostas"
    ws.append(["Nome", "Localização", "Data", "Dia da Semana"])
    for resposta in dados:
        ws.append(resposta)
    wb.save(nome_arquivo)

# Função para coletar os dados do agricultor com validação
def coletar_dados():
    dados = []
    while True:
        nome = input("Digite seu nome: ").strip()
        if not nome:
            print("Nome não pode ser vazio. Tente novamente.")
            continue
        localizacao = input("Informe sua localização: ").strip()
        if not localizacao:
            print("Localização não pode ser vazia. Tente novamente.")
            continue
        data_atual, dia_da_semana = obter_data_hora()
        dados.append([nome, localizacao, data_atual, dia_da_semana])
        if input("Adicionar mais? (s/n): ").strip().lower() != 's':
            break
    salvar_planilha(dados)
    print("Dados salvos com sucesso!")

# Função para respostas frequentes
def respostas_frequentes(pergunta):
    perguntas_freq = {
        "como me cadastrar?": "Para se cadastrar, basta fornecer seu nome, localização e outras informações solicitadas.",
        "quais as funcionalidades do sistema?": "O sistema permite cadastrar agricultores, visualizar relatórios e interagir com o chatbot para tirar dúvidas.",
        "como usar o sistema?": "Após o cadastro, você pode acessar funcionalidades como visualização de dados, cadastro de novos agricultores e obtenção de relatórios.",
        "que dia é hoje?": f"Hoje é {obter_data_hora()[0]}, {obter_data_hora()[1]}."
    }
    return perguntas_freq.get(pergunta.lower(), None)

# Função para fluxo de perguntas do chatbot
def fluxo_perguntas():
    while True:
        pergunta = input("Pergunte algo: ").strip().lower()
        if pergunta == 'sair':
            print("Saindo do chatbot.")
            break
        resposta = respostas_frequentes(pergunta) or enviar_mensagem(pergunta)
        print(f"Chatbot: {resposta}\n")
        if input("Fazer outra pergunta? (s/n): ").strip().lower() != 's':
            break

# Função para enviar mensagem pelo WhatsApp (via Twilio)
def enviar_mensagem_whatsapp(mensagem, numero):
    client_twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    mensagem_enviada = client_twilio.messages.create(
        body=mensagem,
        from_=TWILIO_WHATSAPP_NUMBER,  # Número da Twilio para WhatsApp
        to=f'whatsapp:{numero}'
    )
    return mensagem_enviada.sid

# Menu inicial
def menu_inicial():
    while True:
        print("\n1 - Cadastrar Agricultor")
        print("2 - Perguntar ao Chatbot")
        print("3 - Enviar mensagem pelo WhatsApp")
        print("4 - Sair")
        escolha = input("Opção: ").strip()
        if escolha == "1":
            coletar_dados()
        elif escolha == "2":
            fluxo_perguntas()
        elif escolha == "3":
            numero_destino = input("Informe o número do agricultor no formato +55XXXXXXXXXXX: ")
            mensagem = input("Digite a mensagem para enviar: ")
            enviar_mensagem_whatsapp(mensagem, numero_destino)
            print("Mensagem enviada com sucesso!")
        elif escolha == "4":
            print("Até logo!")
            break
        else:
            print("Opção inválida.")

# Inicia o menu inicial
if __name__ == "__main__":
    menu_inicial()
