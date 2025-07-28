#!/bin/bash

# Carrega as variáveis do .env
set -a
source .env
set +a

echo "🔎 Testando conexão com PostgreSQL local ($DB_HOST_LOCAL:$DB_PORT_LOCAL) como usuário $DB_USER_POSTGRES..."

# Exporta senha para o usuário 'postgres' (superusuário) para criar usuário e banco
export PGPASSWORD=$DB_PASSWORD_POSTGRES

# Testa se o banco local está aceitando conexão
if ! pg_isready -h "$DB_HOST_LOCAL" -p "$DB_PORT_LOCAL" > /dev/null; then
  echo "❌ PostgreSQL local não está aceitando conexões na porta $DB_PORT_LOCAL."
  exit 1
fi

# Verifica se usuário local (campo_user) existe, cria se não existir
echo "👤 Verificando/criando usuário '$DB_USER_LOCAL'..."
if ! psql -U "$DB_USER_POSTGRES" -h "$DB_HOST_LOCAL" -p "$DB_PORT_LOCAL" -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER_LOCAL'" | grep -q 1; then
  psql -U "$DB_USER_POSTGRES" -h "$DB_HOST_LOCAL" -p "$DB_PORT_LOCAL" -c "CREATE USER $DB_USER_LOCAL WITH PASSWORD '$DB_PASSWORD_LOCAL';"
fi

# Verifica se banco existe, cria se não existir e atribui dono
echo "📦 Verificando/criando banco '$DB_NAME_LOCAL'..."
if ! psql -U "$DB_USER_POSTGRES" -h "$DB_HOST_LOCAL" -p "$DB_PORT_LOCAL" -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME_LOCAL'" | grep -q 1; then
  psql -U "$DB_USER_POSTGRES" -h "$DB_HOST_LOCAL" -p "$DB_PORT_LOCAL" -c "CREATE DATABASE $DB_NAME_LOCAL OWNER $DB_USER_LOCAL;"
fi

# Garante privilégios para o usuário local no banco
psql -U "$DB_USER_POSTGRES" -h "$DB_HOST_LOCAL" -p "$DB_PORT_LOCAL" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME_LOCAL TO $DB_USER_LOCAL;"

# Importa o schema usando o usuário local e a senha dele
echo "📥 Importando schema para '$DB_NAME_LOCAL'..."
export PGPASSWORD=$DB_PASSWORD_LOCAL
psql -U "$DB_USER_LOCAL" -h "$DB_HOST_LOCAL" -p "$DB_PORT_LOCAL" -d "$DB_NAME_LOCAL" < "$SCHEMA_PATH"

echo "✅ Importação concluída com sucesso!"
