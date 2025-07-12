#!/bin/bash

set -a
source .env
set +a

if ! docker ps | grep -q $CONTAINER_NAME; then
  echo "❌ Container '$CONTAINER_NAME' não está rodando."
  exit 1
fi

echo "📦 Verificando/criando banco '$DB_NAME_DOCKER'..."
docker exec -i $CONTAINER_NAME psql -U $DB_USER_DOCKER -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME_DOCKER'" | grep -q 1 || \
docker exec -i $CONTAINER_NAME psql -U $DB_USER_DOCKER -c "CREATE DATABASE $DB_NAME_DOCKER"

echo "📥 Importando schema para '$DB_NAME_DOCKER'..."
docker exec -i $CONTAINER_NAME psql -U $DB_USER_DOCKER -d $DB_NAME_DOCKER < $SCHEMA_PATH

echo "✅ Docker pronto!"
