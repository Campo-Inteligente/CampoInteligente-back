# -*- coding: utf-8 -*-
# ARQUIVO: campointeligente_api.py
# DESCRIÇÃO: API Flask independente que serve como backend de serviços.
# Lida com banco de dados e integrações externas.

from flask import Flask, request, jsonify
from functools import wraps
import os
import requests
import json
import psycopg2
from dotenv import load_dotenv
import openai

# Carregando variáveis de ambiente
load_dotenv()
app = Flask(__name__)

# --- CONFIGURAÇÃO ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY") # Chave para proteger esta API

DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5432)

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# --- DECORATOR DE SEGURANÇA ---
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-API-Key') and request.headers.get('X-API-Key') == INTERNAL_API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized"}), 401
    return decorated_function

# --- FUNÇÕES DE BANCO DE DADOS (INTERNAS) ---
# Estas funções são as mesmas, mas agora são usadas apenas por esta API.
def get_db_connection():
    try:
        conn = psycopg2.connect(
            database=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT, sslmode='require'
        )
        return conn
    except psycopg2.Error as e:
        print(f"DEBUG_DB_CONNECT_ERROR: {e}")
        return None

# --- ROTAS DA API DE SERVIÇOS ---

@app.route('/init_db', methods=['POST'])
@require_api_key
def init_db_route():
    # Esta rota pode ser chamada uma vez durante o deploy para criar as tabelas.
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        # O schema completo...
        schema_creation_query = """
            CREATE TABLE IF NOT EXISTS tb_conversation_contexts (
                whatsapp_id VARCHAR(50) PRIMARY KEY,
                context JSONB,
                last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
            -- Adicione aqui as outras tabelas (tb_usuarios, tb_safras, etc.)
        """
        cur.execute(schema_creation_query)
        conn.commit()
        cur.close()
        return jsonify({"message": "Database initialized successfully"}), 200
    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/context/load', methods=['POST'])
@require_api_key
def load_context_route():
    data = request.json
    phone_number = data.get('phone_number')
    if not phone_number:
        return jsonify({"error": "phone_number is required"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT context FROM tb_conversation_contexts WHERE whatsapp_id = %s;", (phone_number,))
        result = cur.fetchone()
        cur.close()
        context = result[0] if result else {}
        return jsonify({"context": context}), 200
    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/context/save', methods=['POST'])
@require_api_key
def save_context_route():
    data = request.json
    phone_number = data.get('phone_number')
    context = data.get('context')
    if not phone_number or context is None:
        return jsonify({"error": "phone_number and context are required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
        
    try:
        cur = conn.cursor()
        context_json = json.dumps(context)
        cur.execute("""
            INSERT INTO tb_conversation_contexts (whatsapp_id, context)
            VALUES (%s, %s)
            ON CONFLICT (whatsapp_id) DO UPDATE
            SET context = EXCLUDED.context, last_updated = CURRENT_TIMESTAMP;
        """, (phone_number, context_json))
        conn.commit()
        cur.close()
        return jsonify({"message": "Context saved successfully"}), 200
    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/weather/current', methods=['POST'])
@require_api_key
def get_weather_route():
    data = request.json
    cidade = data.get('cidade')
    pais = data.get('pais')
    if not cidade or not pais:
        return jsonify({"error": "cidade and pais are required"}), 400
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return jsonify(r.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/openai/chat', methods=['POST'])
@require_api_key
def openai_chat_route():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400
    
    if not OPENAI_API_KEY:
        return jsonify({"error": "OpenAI API key not configured"}), 500
        
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.5,
        )
        content = response.choices[0].message.content.strip()
        return jsonify({"response": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "<h1>API de Serviços - Campo Inteligente</h1><p>Esta API está online e pronta para receber requisições autenticadas.</p>"

if __name__ == "__main__":
    # Esta API deve rodar em uma porta diferente do chatbot, ex: 5001
    app.run(debug=True, host='0.0.0.0', port=5001)
