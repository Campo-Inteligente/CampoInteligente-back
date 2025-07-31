#!/bin/bash

# 📅 Data e hora atual para nomear o arquivo
DATA_HORA=$(date +%Y%m%d_%H%M%S)

# 📁 Caminho para backup relativo à raiz do projeto
BACKUP_DIR="$(pwd)/backup-database"
mkdir -p "$BACKUP_DIR"

# 📄 Nome do arquivo de backup
BACKUP_FILE="${BACKUP_DIR}/backup_${DATA_HORA}.sql"

# 🔐 Credenciais do banco de dados
DB_NAME="campo_inteligente"
DB_HOST="localhost"
DB_PORT="5432"
DB_USER="campo_user"
DB_PASSWORD="cipass12bd"

# 🔐 Exporta a senha para uso temporário
export PGPASSWORD="${DB_PASSWORD}"

# 🐘 Executa o pg_dump
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -F p -d "$DB_NAME" -f "$BACKUP_FILE"

# ✅ Resultado
if [ $? -eq 0 ]; then
  echo "✅ Backup criado com sucesso em: $BACKUP_FILE"
else
  echo "❌ Falha ao criar backup"
fi

# 🔒 Limpa variável de ambiente
unset PGPASSWORD
