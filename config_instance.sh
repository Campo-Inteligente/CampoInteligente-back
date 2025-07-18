#!/bin/bash

# ==============================================================================
# Script para configurar a instância da Evolution API após um reinício.
# Este script define o webhook, os eventos e os comportamentos desejados.
# ==============================================================================

# --- VARIÁVEIS DE CONFIGURAÇÃO (Altere se necessário) ---
INSTANCE_NAME="campointeligente1"
API_KEY="juan1403" # A sua chave de API
WEBHOOK_URL="http://45.236.199.2:5000/webhook"
API_URL="http://localhost:21085"

# --- JSON de Configuração ---
# Aqui definimos todas as configurações que queremos aplicar.
# Baseado na sua interface gráfica e necessidades.
CONFIG_JSON=$(cat <<EOF
{
  "webhook": "${WEBHOOK_URL}",
  "settings": {
    "reject_call": true,
    "groups_ignore": true,
    "always_online": true,
    "read_messages": true,
    "read_status": true,
    "sync_full_history": true
  },
  "events": [
    "APPLICATION_STARTUP",
    "QRCODE_UPDATED",
    "MESSAGES_SET",
    "MESSAGES_UPSERT",
    "MESSAGES_UPDATE",
    "SEND_MESSAGE",
    "CONTACTS_SET",
    "CONTACTS_UPSERT",
    "CONTACTS_UPDATE",
    "CHATS_SET",
    "CHATS_DELETE",
    "CHATS_UPDATE",
    "GROUPS_UPSERT",
    "GROUP_UPDATE",
    "GROUP_PARTICIPANTS_UPDATE",
    "CALL"
  ]
}
EOF
)

# --- Execução do Comando ---
echo "⚙️  A configurar a instância: ${INSTANCE_NAME}..."

curl -X POST "${API_URL}/instance/update/${INSTANCE_NAME}" \
-H "apikey: ${API_KEY}" \
-H "Content-Type: application/json" \
-d "${CONFIG_JSON}"

echo -e "\n✅ Configuração enviada. A reiniciar a instância para aplicar as alterações..."

# --- Reiniciar a Instância para Garantir que as Alterações sejam Aplicadas ---
curl -X POST "${API_URL}/instance/restart/${INSTANCE_NAME}" \
-H "apikey: ${API_KEY}" \
-H "Content-Length: 0"

echo -e "\n✨ Instância ${INSTANCE_NAME} configurada e a reiniciar. Verifique o estado em breve."

