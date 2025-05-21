import os
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

load_dotenv()

def criar_conexao():
    try:
        conexao = psycopg2.connect(
            database=os.getenv("DB_NAME"),
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432"),
            sslmode="require"
        )
        print("Conexão estabelecida com sucesso.")
        return conexao
    except OperationalError as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None