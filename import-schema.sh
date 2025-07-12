#!/bin/bash

# 🚀 Carrega variáveis do .env
set -a
source .env
set +a

# 🧪 Verifica se o container está rodando
if ! docker ps | grep -q $CONTAINER_NAME; then
  echo "❌ Container '$CONTAINER_NAME' não está rodando."
  exit 1
fi

# 📨 Importa o schema
echo "📥 Importando '$SCHEMA_PATH' para o banco '$DB_NAME'..."
docker exec -i $CONTAINER_NAME psql -U $DB_USER_BD -d $DB_NAME_BD < $SCHEMA_PATH

echo "✅ Importação concluída!"
