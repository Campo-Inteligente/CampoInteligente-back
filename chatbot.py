import openai
import requests
from datetime import datetime
import locale
import openpyxl
import os
from dotenv import load_dotenv

# Configurações
load_dotenv()

try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except:
    locale.setlocale(locale.LC_TIME, "")  # fallback

# Chaves de API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

client_openai = openai.Client(api_key=OPENAI_API_KEY)

# Funções auxiliares
def obter_data_hora():
    agora = datetime.now()
    data = agora.strftime("%d de %B de %Y")
    dias_semana = {
        "Monday": "segunda-feira", "Tuesday": "terça-feira", "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira", "Friday": "sexta-feira", "Saturday": "sábado", "Sunday": "domingo"
    }
    dia_semana = dias_semana.get(agora.strftime("%A"), agora.strftime("%A"))
    return data, dia_semana

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
    except Exception as e:
        return {"erro": str(e)}

def obter_previsao_tempo(cidade, pais):
    if not cidade or not pais:
        return {"erro": "Cidade e país são obrigatórios."}
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url)
        d = r.json()
        if r.status_code != 200:
            return {"erro": f"Não encontrei previsão para '{cidade}, {pais}'."}
        return {
            "cidade": cidade,
            "descricao": d['weather'][0]['description'],
            "temperatura": d['main']['temp'],
            "sensacao": d['main']['feels_like'],
            "umidade": d['main']['humidity'],
            "vento": d['wind']['speed']
        }
    except Exception as e:
        return {"erro": str(e)}

def obter_previsao_estendida(cidade, pais):
    if not cidade or not pais:
        return {"erro": "Cidade e país são obrigatórios."}
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={cidade},{pais}&cnt=3&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url)
        d = r.json()
        if r.status_code != 200:
            return {"erro": f"Não encontrei previsão para '{cidade}, {pais}'."}
        previsoes = []
        for dia in d["list"]:
            data = datetime.utcfromtimestamp(dia["dt"]).strftime("%d/%m/%Y")
            previsoes.append({
                "data": data,
                "descricao": dia["weather"][0]["description"],
                "min": dia["main"]["temp_min"],
                "max": dia["main"]["temp_max"]
            })
        return {"previsao": previsoes}
    except Exception as e:
        return {"erro": str(e)}

def enviar_mensagem_ia(mensagem):
    try:
        local = obter_localizacao_via_ip()
        clima = obter_previsao_tempo(local.get("cidade", "Salvador"), local.get("pais", "BR"))
        prompt = (
            "Você é um assistente agrícola no sistema Campo Inteligente.\n"
            f"📍 Local: {local}\n"
            f"🌦️ Clima: {clima}\n"
            f"❓ Pergunta: {mensagem}"
        )
        resposta = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4
        )
        conteudo = resposta.choices[0].message.content.strip() if resposta.choices else "Não consegui gerar uma resposta."
        return {"resposta": conteudo}
    except Exception as e:
        return {"erro": str(e)}

def salvar_planilha(dados):
    try:
        arquivo = "respostas_agricultores_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Respostas"
        ws.append(["Nome", "Localização", "Data", "Dia da Semana"])
        for linha in dados:
            ws.append(linha)
        wb.save(arquivo)
        return {"arquivo_criado": arquivo}
    except Exception as e:
        return {"erro": str(e)}

# Interação no terminal
def interagir_com_ia():
    while True:
        print("\n--- Sistema Campo Inteligente ---")
        mensagem = input("Digite sua pergunta para o assistente ou 'sair' para encerrar: ")
        
        if mensagem.lower() == "sair":
            print("Saindo do sistema...")
            break
        
        resposta_ia = enviar_mensagem_ia(mensagem)
        print("\nResposta da IA: ")
        print(resposta_ia.get("resposta", "Desculpe, não entendi sua pergunta."))

if __name__ == "__main__":
    interagir_com_ia()
