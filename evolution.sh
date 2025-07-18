#!/bin/bash

# === Mensagem de Boas-vindas ===
echo -e "\n\n\033[1;32m"
echo " █████████       ███████         █████████"
echo "███              ███   ██        ███      "
echo "███   █████      ███   ██        ███  ████"
echo "███     ███      ███████         ███    ██"
echo "███     ███      ███   ██        ███    ██"
echo " █████████       ███   ██        █████████"
echo ""
echo "           Projeto campo inteligente"
echo ""
echo -e "\033[0m\n"

# === Variáveis de Banco de Dados ===
pg_user="campo_user"
pg_password="cipass12bd"
pg_database="campo_inteligente"
pg_host="postgres-campoInteligente"

# === Instala Dependências ===
echo "Atualizando VPS e instalando dependências..."
sudo apt update -y && sudo apt upgrade -y
sudo apt install git docker-compose -y

# === Clona o Repositório ===
echo "Clonando Evolution API na branch v1.8.2..."
git clone -b v1.8.2 https://github.com/EvolutionAPI/evolution-api.git
cd evolution-api

# === Criação do .env ===
echo "Gerando arquivo .env..."
cat > .env <<EOL
SERVER_TYPE=http
SERVER_PORT=8080
SERVER_URL=http://localhost:8080

LOG_LEVEL=ERROR,WARN,DEBUG,INFO,LOG
LOG_COLOR=true

DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://${pg_user}:${pg_password}@${pg_host}:5432/${pg_database}
DATABASE_CONNECTION_CLIENT_NAME=evolution_exchange

DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=true
DATABASE_SAVE_MESSAGE_UPDATE=true
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
DATABASE_SAVE_DATA_LABELS=true
DATABASE_SAVE_DATA_HISTORIC=true

AUTHENTICATION_API_KEY=juan1403

WEBHOOK_EVENTS_QRCODE_UPDATED=true
WEBHOOK_EVENTS_MESSAGES_SET=true
WEBHOOK_EVENTS_MESSAGES_UPSERT=true
WEBHOOK_EVENTS_MESSAGES_EDITED=true
WEBHOOK_EVENTS_MESSAGES_UPDATE=true
WEBHOOK_EVENTS_MESSAGES_DELETE=true
WEBHOOK_EVENTS_SEND_MESSAGE=true
WEBHOOK_EVENTS_CONTACTS_SET=true
WEBHOOK_EVENTS_CONTACTS_UPSERT=true
WEBHOOK_EVENTS_CONTACTS_UPDATE=true
WEBHOOK_EVENTS_PRESENCE_UPDATE=true
WEBHOOK_EVENTS_CHATS_SET=true
WEBHOOK_EVENTS_CHATS_UPSERT=true
WEBHOOK_EVENTS_CHATS_UPDATE=true
WEBHOOK_EVENTS_CHATS_DELETE=true
WEBHOOK_EVENTS_GROUPS_UPSERT=true
WEBHOOK_EVENTS_GROUPS_UPDATE=true
WEBHOOK_EVENTS_GROUP_PARTICIPANTS_UPDATE=true
WEBHOOK_EVENTS_CONNECTION_UPDATE=true
WEBHOOK_EVENTS_CALL=true
EOL

# === docker-compose.yml ===
echo "Gerando docker-compose.yml..."
cat > docker-compose.yml <<EOL
version: '3.9'

services:
  evolution-api:
    container_name: evolution-api
    image: atendai/evolution-api:v1.8.2
    restart: always
    ports:
      - "21085:8080"
    volumes:
      - evolution_instances:/evolution/instances
    env_file:
      - .env
    networks:
      - evolution-net

  postgres-campoInteligente:
    container_name: postgres-campoInteligente
    image: postgres:15
    restart: always
    environment:
      POSTGRES_USER: ${pg_user}
      POSTGRES_PASSWORD: ${pg_password}
      POSTGRES_DB: ${pg_database}
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    command: -c 'listen_addresses=*'
    networks:
      - evolution-net

volumes:
  evolution_instances:
  pg_data:

networks:
  evolution-net:
    driver: bridge
EOL

# === Iniciando containers ===
echo "Iniciando containers com Docker Compose..."
docker-compose up -d

echo -e "\n\033[1;32mConfiguração concluída com sucesso! 🚀\033[0m\n"
