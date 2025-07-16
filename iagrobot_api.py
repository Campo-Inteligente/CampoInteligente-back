# -*- coding: utf-8 -*-
# ARQUIVO: iagro_bot_api.py
# DESCRIÇÃO: Aplicação Flask principal do chatbot. Consome a campointeligente_api.

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv

# Carregando variáveis de ambiente
load_dotenv()
app = Flask(__name__)
CORS(app)

# --- CONFIGURAÇÃO ---
# URL da nossa API de serviços e a chave para se autenticar nela
CAMPOINTELIGENTE_API_URL = os.getenv(
    "CAMPOINTELIGENTE_API_URL", "http://localhost:5001")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

# Configurações da Evolution API para enviar mensagens
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

# --- FUNÇÕES CLIENTE DA API ---
# Estas funções agora fazem requisições HTTP para a nossa API de serviços


def load_context_from_api(phone_number):
    headers = {'X-API-Key': INTERNAL_API_KEY,
               'Content-Type': 'application/json'}
    payload = {'phone_number': phone_number}
    try:
        response = requests.post(
            f"{CAMPOINTELIGENTE_API_URL}/context/load", json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get('context', {})
    except requests.RequestException as e:
        print(f"API_CLIENT_ERROR: Falha ao carregar contexto: {e}")
        return {}


def save_context_to_api(phone_number, context):
    headers = {'X-API-Key': INTERNAL_API_KEY,
               'Content-Type': 'application/json'}
    payload = {'phone_number': phone_number, 'context': context}
    try:
        response = requests.post(
            f"{CAMPOINTELIGENTE_API_URL}/context/save", json=payload, headers=headers)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"API_CLIENT_ERROR: Falha ao salvar contexto: {e}")
        return False


def get_weather_from_api(cidade, pais):
    headers = {'X-API-Key': INTERNAL_API_KEY,
               'Content-Type': 'application/json'}
    payload = {'cidade': cidade, 'pais': pais}
    try:
        response = requests.post(
            f"{CAMPOINTELIGENTE_API_URL}/weather/current", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API_CLIENT_ERROR: Falha ao obter clima: {e}")
        return {"erro": str(e)}

# --- LÓGICA DO CHATBOT ---


def send_whatsapp_message(numero, mensagem, instance_name):
    """Envia uma mensagem de texto para um número de WhatsApp."""
    payload = {"number": numero, "textMessage": {"text": mensagem}}
    headers = {"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY}
    url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
    try:
        requests.post(url, json=payload, headers=headers)
    except requests.RequestException as e:
        print(f"WHATSAPP_ERROR: Erro ao enviar mensagem: {e}")


def process_message(numero, mensagem, instance_name):
    """Função principal que processa a mensagem recebida."""
    contexto = load_context_from_api(numero)

    # Exemplo de uso da API de clima
    if "clima" in mensagem.lower():
        # Supondo que a cidade está no contexto ou é extraída da mensagem
        cidade = contexto.get("cidade", "Jequié")
        clima = get_weather_from_api(cidade, "BR")
        if "erro" not in clima:
            resposta_bot = f"A previsão para {cidade} é: {clima.get('weather', [{}])[0].get('description')} com temperatura de {clima.get('main', {}).get('temp')}°C."
        else:
            resposta_bot = "Não consegui obter a previsão do tempo."
    else:
        # Lógica de conversa principal (cadastro, menus, etc.) iria aqui
        resposta_bot = f"Olá! Recebi sua mensagem: '{mensagem}'. A nova arquitetura de API está funcionando!"

    contexto['last_message_received'] = mensagem
    save_context_to_api(numero, contexto)
    send_whatsapp_message(numero, resposta_bot, instance_name)

# --- ROTA DO WEBHOOK ---


@app.route("/webhook", methods=["POST"])
def webhook_route():
    try:
        data = request.json
        event = data.get('event')
        instance_name = data.get('instance')

        if event != 'messages.upsert':
            return jsonify({"status": f"Evento {event} ignorado."}), 200

        message_data = data.get('data', {})
        if message_data.get('key', {}).get('fromMe', False):
            return jsonify({"status": "Mensagem própria ignorada."}), 200

        numero = message_data.get('key', {}).get('remoteJid')
        mensagem_recebida = message_data.get(
            'message', {}).get('conversation', '').strip()

        if not numero or not mensagem_recebida:
            return jsonify({"status": "ignorado"}), 200

        process_message(numero, mensagem_recebida, instance_name)
        return jsonify({"status": "sucesso"}), 200

    except Exception as e:
        print(f"WEBHOOK_ERROR: Erro inesperado: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "<h1>API do Chatbot Iagro (Cliente) está online!</h1>"

# --- EXECUÇÃO PRINCIPAL ---


if __name__ == "__main__":
    # Este servidor Flask roda na porta principal, ex: 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
