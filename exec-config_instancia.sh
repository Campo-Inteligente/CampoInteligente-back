#!/bin/bash

# Script para configurar a instância 'campointeligente1' da Evolution API

echo "CONFIGURAÇÃO DE INSTÂNCIA: campointeligente1..."
echo "---------------------------------------------"

# --- Passo 1: Aplicando configurações de COMPORTAMENTO ---
# Usando o endpoint correto 'settings/set' que encontramos na documentação.
echo ""
echo "----------------------------------------------------------"
echo "✅ APLICANDO CONFIGURAÇÕES DE COMPORRTAMENTO..."

curl -X POST http://localhost:21085/settings/set/campointeligente1 \
-H "apikey: juan1403" \
-H "Content-Type: application/json" \
--data '{
    "always_online": true,
    "read_messages": true,
    "read_status": true,
    "groups_ignore": false,
    "reject_call": false,
    "sync_full_history": false
}'

# --- Passo 2: Aplicando configurações de WEBHOOK ---
# Usando o endpoint para configurar o webhook.
# NOTA: Se este passo falhar, o endpoint '/webhook/set/' pode estar incorreto.
# Verifique o endpoint correto na documentação da API em http://localhost:21085/docs
echo ""
echo "-------------------------------------------------------"
echo "✅ APLICANDO CONFIGURAÇÕES DE WEBHOOK..."
echo "🤖 Um webhook é uma forma de comunicação entre sistemas que permite o envio automático de informações quando um evento específico acontece. Em vez de um sistema ficar perguntando constantemente se algo mudou (como acontece com APIs tradicionais), o webhook envia uma notificação instantânea assim que o evento ocorre."
curl -X POST http://localhost:21085/webhook/set/campointeligente1 \
-H "apikey: juan1403" \
-H "Content-Type: application/json" \
--data '{
    "enabled": true,
    "url": "http://45.236.189.2:5000/webhook",
    "webhook_by_events": true,
    "events": [
        "APPLICATION_STARTUP", "QRCODE_UPDATED", "MESSAGES_SET", "MESSAGES_UPSERT",
        "MESSAGES_UPDATE", "MESSAGES_DELETE", "SEND_MESSAGE", "CONTACTS_UPSERT",
        "CONTACTS_SET", "PRESENCE_UPDATE", "CHATS_SET", "CHATS_UPSERT", "CHATS_UPDATE",
        "CHATS_DELETE", "GROUPS_UPSERT", "GROUP_UPDATE", "GROUP_PARTICIPANTS_UPDATE",
        "CONNECTION_UPDATE", "CALL"
    ]
}'
echo ""
echo "----------------------------------------------------"
echo "✅ PROCESSO CONCLUÍDO"
echo "As configurações foram enviadas para a instância campointeligente1."
echo "As alterações geralmente são aplicadas instantaneamente, sem necessidade de reiniciar."

