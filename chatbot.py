from flask import Flask, request, jsonify
from datetime import datetime
import locale
import os
import requests
import openpyxl
from dotenv import load_dotenv
import openai
import re
import json  # Importe o módulo json

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
EVOLUTION_API_URL = "https://1f27-45-169-217-33.ngrok-free.app"  # Removi a barra extra

# Inicializando a API do OpenAI
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)

# Dicionário para armazenar o contexto da conversa por número de telefone
conversa_contextos = {}

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
    except requests.RequestException as e:  # Captura erros de requisição
        return {"erro": f"Erro de requisição: {e}"}
    except Exception as e:
        return {"erro": f"Erro geral: {e}"}


# Função para obter previsão do tempo
def obter_previsao_tempo(cidade, pais):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url)
        r.raise_for_status()  # Lança exceção para status de erro
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
    except KeyError:  # Captura erro se a chave não existir
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
                    "data_hora": [data_hora_utc]  # Armazena a lista de horários
                }
            else:
                previsoes_diarias[data]["min"] = min(previsoes_diarias[data]["min"], item["main"]["temp_min"])
                previsoes_diarias[data]["max"] = max(previsoes_diarias[data]["max"], item["main"]["temp_max"])
                previsoes_diarias[data]["data_hora"].append(data_hora_utc)  # Adiciona o horário à lista

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
        r.raise_for_status()  # Verifica se a requisição foi bem-sucedida
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
    except json.JSONDecodeError:  # Trata resposta JSON inválida
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
    url = f"http://127.0.0.1:8080/message/sendText/campointeligente"  # verificar a url
    try:
        resposta = requests.post(url, json=payload, headers=headers)
        resposta.raise_for_status()
        if resposta.status_code == 200:
            return resposta.status_code, resposta.json()
        else:
            return resposta.status_code, {"erro": resposta.text}
    except requests.RequestException as e:
        return None, {"erro": f"Erro de requisição ao enviar mensagem: {e}"}
    except Exception as e:
        return None, {"erro": f"Erro geral ao enviar mensagem: {e}"}


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
            print(f"Erro na API do OpenAI: {e}")
            resposta = "Desculpe, a API do OpenAI está temporariamente indisponível."
        except Exception as e:
            print(f"Erro ao chamar OpenAI: {e}")
            resposta = "Desculpe, tive um problema ao processar sua mensagem."

        return jsonify({"resposta": resposta})

    except Exception as e:
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
            return jsonify({"erro": "Dados não fornecidos."}), 400
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
        return jsonify({"erro": str(e)}), 500


# Rota inicial
@app.route("/", methods=["GET"])
def home():
    return "API Campo Inteligente está online!"


# Rota do webhook para receber e responder mensagens
@app.route("/webhook", methods=["POST"])
def webhook_route():
    try:
        data = request.json
        print(f"Dados recebidos: {data}")
        event = data.get('event')

        if event == 'messages.upsert':
            mensagem_recebida = data.get('data', {}).get('message', {}).get('conversation', '').lower()
            numero = data.get('data', {}).get('key', {}).get('remoteJid', '')

            if mensagem_recebida and numero:
                # Tenta obter o contexto da conversa
                contexto = conversa_contextos.get(numero, {})
                nome = contexto.get("nome", "Usuário")  # Obtém o nome do contexto, se existir
                localizacao = contexto.get("localizacao")  # Obtem a localização do contexto

                # Verifica se a mensagem é um cumprimento
                cumprimentos = ["bom dia", "boa tarde", "boa noite", "olá", "oi"]
                if any(cumprimento in mensagem_recebida for cumprimento in cumprimentos):
                    resposta = f"Olá! Sou a Iagro, assistente virtual da Campo Inteligente. Como posso ajudar você hoje?"
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"Status do envio (cumprimento): {send_status}, resposta: {send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # Verifica se a mensagem é um "tudo bem?"
                elif "tudo bem" in mensagem_recebida:
                    resposta = "Tudo bem, sim! Sou a Iagro, como posso ajudar você?"
                    send_status, send_resp = send_whatsapp_message(numero, resposta)
                    print(f"Status do envio (tudo bem): {send_status}, resposta: {send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # Tenta extrair coordenadas da mensagem
                coordenadas = re.findall(r"(-?\d+\.\d+)[, ]+\s*(-?\d+\.\d+)", mensagem_recebida)

                if coordenadas:
                    lat, lon = coordenadas[0]
                    local = obter_localizacao_por_coordenadas(lat, lon)
                    if "erro" in local:
                        resposta = "Desculpe, não consegui identificar sua localização a partir das coordenadas."
                    else:
                        cidade = local.get("cidade", "")
                        estado = local.get("estado", "")
                        pais = local.get("pais", "")
                        localizacao = {"cidade": cidade, "estado": estado, "pais": pais}  # armazena a localização
                        conversa_contextos[numero] = {"nome": nome, "localizacao": localizacao}  # Atualiza o contexto com a localização
                        clima_atual = obter_previsao_tempo(cidade, pais)
                        clima_estendido = obter_previsao_estendida(cidade, pais)

                        # Envia para o GPT para gerar a resposta
                        prompt = (
                            f"Você é a Iagro, assistente virtual da Campo Inteligente.\n"
                            f"O usuário está em {cidade}, {estado}, {pais}.\n"
                            f"O clima atual é: {clima_atual}.\n"
                            f"A previsão estendida é: {clima_estendido}.\n"
                            f"O usuário disse: {mensagem_recebida}\n"
                            "Gere uma resposta amigável e informativa sobre o clima e recomendações de plantio para a região, com base nos dados fornecidos.  Se o usuário perguntar sobre o clima ou o melhor plantio, forneça informações sobre o clima atual e uma recomendação de plantio concisa e apropriada para a região. Não liste toda a previsão estendida, apenas destaque o período mais favorável, se possível."
                        )
                        try:
                            resposta_gpt = ""  # Inicializa a resposta do GPT
                            response = openai.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=300,
                                temperature=0.4,
                            )
                            resposta = response.choices[0].message.content.strip()
                        except openai.APIError as e:
                            print(f"Erro na API do OpenAI: {e}")
                            resposta = "Desculpe, a API do OpenAI está temporariamente indisponível."
                            resposta_gpt = "Desculpe, a API do OpenAI está temporariamente indisponível."  # define resposta para o usuario
                        except Exception as e:
                            print(f"Erro ao chamar OpenAI: {e}")
                            resposta = "Desculpe, tive um problema ao processar sua mensagem."
                            resposta_gpt = "Desculpe, tive um problema ao processar sua mensagem."  # define resposta para o usuario
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"Status do envio (coordenadas): {send_status}, resposta: {send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                # Verifica se a mensagem contém palavras-chave de localização e clima
                elif any(palavra in mensagem_recebida for palavra in ["localização", "clima", "tempo", "onde estou", "qual a minha localização"]):
                    local = obter_localizacao_via_ip()
                    if "erro" in local:
                        resposta = "Desculpe, não consegui determinar sua localização."
                    else:
                        cidade = local.get("cidade", "")
                        estado = local.get("estado", "")
                        pais = local.get("pais", "")
                        localizacao = {"cidade": cidade, "estado": estado, "pais": pais}  # armazena localização
                        conversa_contextos[numero] = {"nome": nome, "localizacao": localizacao}  # atualiza o contexto
                        clima_atual = obter_previsao_tempo(cidade, pais)
                        clima_estendido = obter_previsao_estendida(cidade, pais)
                        # Envia para o GPT para gerar a resposta
                        prompt = (
                            f"Você é a Iagro, assistente virtual da Campo Inteligente.\n"
                            f"O usuário está em {cidade}, {estado}, {pais}.\n"
                            f"O clima atual é: {clima_atual}.\n"
                            f"A previsão estendida é: {clima_estendido}.\n"
                            f"O usuário perguntou sobre a localização: {mensagem_recebida}.\n"  # adicionado a mensagem do usuario ao prompt
                            "Gere uma resposta amigável e informativa sobre a localização do usuário, o clima e recomendações de plantio para a região, com base nos dados fornecidos. Se o usuário perguntar sobre o clima ou o melhor plantio, forneça informações sobre o clima atual e uma recomendação de plantio concisa e apropriada para a região. Não liste toda a previsão estendida, apenas destaque o período mais favorável, se possível."
                        )
                        try:
                            resposta_gpt = ""  # Inicializa a resposta do GPT
                            response = openai.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=300,
                                temperature=0.4,
                            )
                            resposta = response.choices[0].message.content.strip()
                        except openai.APIError as e:
                            print(f"Erro na API do OpenAI: {e}")
                            resposta = "Desculpe, a API do OpenAI está temporariamente indisponível."
                            resposta_gpt = "Desculpe, a API do OpenAI está temporariamente indisponível."  # define resposta para o usuario
                        except Exception as e:
                            print(f"Erro ao chamar OpenAI: {e}")
                            resposta = "Desculpe, tive um problema ao processar sua mensagem."
                            resposta_gpt = "Desculpe, tive um problema ao processar sua mensagem."  # define resposta para o usuario
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"Status do envio (clima por IP): {send_status}, resposta: {send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                elif "melhor plantio" in mensagem_recebida:
                    if localizacao:
                        cidade = localizacao["cidade"]
                        estado = localizacao["estado"]
                        pais = localizacao["pais"]
                        clima_atual = obter_previsao_tempo(cidade, pais)
                        clima_estendido = obter_previsao_estendida(cidade, pais)
                        # Envia para o GPT para gerar a resposta
                        prompt = (
                            f"Você é a Iagro, assistente virtual da Campo Inteligente.\n"
                            f"O usuário está em {cidade}, {estado}, {pais}.\n"
                            f"O clima atual é: {clima_atual}.\n"
                            f"A previsão estendida é: {clima_estendido}.\n"
                            f"O usuário perguntou sobre o melhor plantio: {mensagem_recebida}.\n"  # adicionado a mensagem do usuario ao prompt
                            "Gere uma resposta amigável e informativa sobre o melhor período de plantio para a região do usuário, com base nos dados fornecidos. Se o usuário perguntar sobre o clima ou o melhor plantio, forneça informações sobre o clima atual e uma recomendação de plantio concisa e apropriada para a região. Não liste toda a previsão estendida, apenas destaque o período mais favorável, se possível."
                        )
                        try:
                            resposta_gpt = ""  # Inicializa a resposta do GPT
                            response = openai.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=300,
                                temperature=0.4,
                            )
                            resposta = response.choices[0].message.content.strip()
                        except openai.APIError as e:
                            print(f"Erro na API do OpenAI: {e}")
                            resposta = "Desculpe, a API do OpenAI está temporariamente indisponível."
                            resposta_gpt = "Desculpe, a API do OpenAI está temporariamente indisponível."  # define resposta para o usuario
                        except Exception as e:
                            print(f"Erro ao chamar OpenAI: {e}")
                            resposta = "Desculpe, tive um problema ao processar sua mensagem."
                            resposta_gpt = "Desculpe, tive um problema ao processar sua mensagem."  # define resposta para o usuario
                        send_status, send_resp = send_whatsapp_message(numero, resposta)
                        print(f"Status do envio (melhor plantio): {send_status}, resposta: {send_resp}")
                        return jsonify({"status": "sucesso", "resposta": resposta}), 200

                else:
                    # Se não tem coordenadas nem palavras-chave de clima, usa o GPT
                    prompt = (
                        f"Você é a Iagro, assistente virtual da Campo Inteligente.\n"
                        f"Usuário disse: {mensagem_recebida}\n"
                        "Responda de forma amigável e clara, fornecendo a informação solicitada e perguntando se o usuário precisa de mais alguma informação."
                    )
                    try:
                        resposta_gpt = ""  # Inicializa a resposta do GPT
                        response = openai.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=300,
                            temperature=0.4,
                        )
                        resposta_gpt = response.choices[0].message.content.strip()
                    except openai.APIError as e:
                        print(f"Erro na API do OpenAI: {e}")
                        resposta_gpt = "Desculpe, a API do OpenAI está temporariamente indisponível."
                    except Exception as e:
                        print(f"Erro ao chamar OpenAI: {e}")
                        resposta_gpt = "Desculpe, tive um problema ao processar sua mensagem."

                    print(f"Resposta gerada pelo GPT: {resposta_gpt}")
                    send_status, send_resp = send_whatsapp_message(numero, resposta_gpt)
                    print(f"Status do envio (GPT): {send_status}, resposta: {send_resp}")
                    return jsonify({"status": "sucesso", "resposta": resposta_gpt}), 200

            else:
                return jsonify({"erro": "Mensagem ou número não encontrados."}), 400

        elif event == 'presence.update':
            presence_data = data.get('data', {})
            print(f"Atualização de presença: {presence_data}")
            return jsonify({"status": "presença atualizada"}), 200

        else:
            print(f"Evento não tratado: {event}")
            return jsonify({"status": f"Evento {event} não tratado"}), 200

    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
