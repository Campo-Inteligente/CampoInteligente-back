#!/bin/bash

echo "⏳ Executando script de inicialização do banco de dados..."

# Configurações
DB_CONTAINER_NAME="postgres-campoInteligente"
DB_NAME="campo_inteligente"
DB_USER="campo_user"
DB_PASSWORD="cipass12bd"
SCHEMA_FILE_PATH="./initdb/schema.sql"

# Copia o arquivo schema.sql para dentro do container (opcional, pode usar com volume também)
docker cp "$SCHEMA_FILE_PATH" "$DB_CONTAINER_NAME":/schema.sql

# Executa o script dentro do container
docker exec -e PGPASSWORD=$DB_PASSWORD -i $DB_CONTAINER_NAME \
  psql -U $DB_USER -d $DB_NAME -f /schema.sql

echo "✅ Script de atualização da database executado com sucesso!"