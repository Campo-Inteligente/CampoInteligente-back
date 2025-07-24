#!/bin/bash

# Script para configurar a instância 'campointeligente1' da Evolution API

echo "⚙️  A configurar a instância: campointeligente1..."
echo ""

# --- Passo 1: Aplicando configurações de COMPORTAMENTO ---
# Usando o endpoint correto 'settings/set' que encontramos na documentação.
echo "-> A aplicar configurações de Comportamento..."
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

echo ""
echo ""

# --- Passo 2: Aplicando configurações de WEBHOOK ---
# Usando o endpoint para configurar o webhook.
# NOTA: Se este passo falhar, o endpoint '/webhook/set/' pode estar incorreto.
# Verifique o endpoint correto na documentação da API em http://localhost:21085/docs
echo "-> A aplicar configurações de Webhook..."
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
echo ""
echo "✨ Script finalizado. As configurações foram enviadas para a instância campointeligente1."
echo "As alterações geralmente são aplicadas instantaneamente, sem necessidade de reiniciar."

