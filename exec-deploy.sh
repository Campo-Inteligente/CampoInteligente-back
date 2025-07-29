#!/bin/bash

clear
set -e  # Para o script parar se qualquer comando falhar

echo "============================================"
echo "🚀 Iniciando processo de *Deploy Automático*"
echo "============================================"

# Parar containers atuais
echo "🛑 Finalizando containers atuais com 'docker compose down'..."
docker compose down

# Atualizar imagens
echo "📥 Atualizando imagens do docker..."
docker compose pull

# Recriar containers com build e iniciar em segundo plano
echo "🔨 Buildando e subindo containers com 'docker compose up -d --build'..."
docker compose up -d --build

# Mostrar status dos containers
echo "📋 Verificando status dos containers..."
docker compose ps

# Reiniciar serviço systemd
echo "🔁 Reiniciando serviço systemd: chatbot.service"
sudo systemctl daemon-reexec
sudo systemctl restart chatbot.service

# Mostrar status do serviço
echo "🩺 Verificando status do serviço chatbot.service..."
sudo systemctl status chatbot.service --no-pager

# Logs em tempo real
#echo "📖 Acompanhando logs do serviço (CTRL+C para sair)..."
#sudo journalctl -u chatbot.service -f

# INICIO CONFIGURANDO INSTANCIAS #------------------------------------------------

# --- Passo 1: Aplicando configurações de COMPORTAMENTO ---
# Usando o endpoint correto 'settings/set' que encontramos na documentação.
echo "Aplicando configurações de Comportamento..."
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

# --- Passo 2: Aplicando configurações de WEBHOOK ---
# Usando o endpoint para configurar o webhook.
# NOTA: Se este passo falhar, o endpoint '/webhook/set/' pode estar incorreto.
# Verifique o endpoint correto na documentação da API em http://localhost:21085/docs
echo "Aplicando configurações de Webhook..."
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

echo "✅ Script finalizado. As configurações foram enviadas para a instância campointeligente1."
echo "ℹ️ As alterações geralmente são aplicadas instantaneamente, sem necessidade de reiniciar."

# SUBINDO DJANGO #-------------------------------------------------------------
#✅ Criar ambiente virtual: 
#python -m venv venv
#source venv/bin/activate

#📦 Instalar Django:
#pip install django

#🏗️ Criar projeto:
#django-admin startproject nome_projeto
#cd nome_projeto

#🧱 Criar apps e modelos:
#python manage.py startapp nome_app

#🔄 Migrar banco de dados:
#python manage.py makemigrations
#python manage.py migrate

#🧪 Testar localmente:
#python manage.py runserver 0.0.0.0:21083

echo ""
echo "🌐 Deploy em Produção (ex: VPS ou nuvem)"
echo "🧪 Criar ambiente virtual no servidor:"
python3 -m venv venv
source venv/bin/activate

echo ""
echo "📦 Instalar dependências:"
pip install -r requirements.txt

echo ""
echo "🛠️ Configurar banco de dados no settings.py"
echo "🔐 Ajustar ALLOWED_HOSTS e DEBUG = False"
echo "📁 Coletar arquivos estáticos:"
python manage.py collectstatic

echo ""
echo "🔄 Migrar banco:"
python manage.py migrate

#echo ""
#echo "🧑‍💻 Criar superusuário (opcional):"
#python manage.py createsuperuser

echo ""
echo " Rodar com servidor de produção:"
gunicorn nome_projeto.wsgi:application 
daphne nome_projeto.asgi:application

echo " Reiniciando o Django"
./exec-restart-django.sh

# FIM CONFIGURANDO INSTANCIAS #------------------------------------------------

echo ""
echo "🌐 Acesso externo:"
echo "✅http://campointeligente.ddns.com.br:21081/ <------- website"
echo "✅http://campointeligente.ddns.com.br:21082/ <------- back"
echo "✅http://campointeligente.ddns.com.br:21083/ <------- django"
echo "✅http://campointeligente.ddns.com.br:21050/ <------- pgadmin"
echo "✅http://campointeligente.ddns.com.br:21085/docs <--- evolutionAPI"
echo "✅https://www.campointeligente.agr.br:3000 <--------- campointeligenteAPI"
echo "✅https://www.campointeligente.agr.br/ <------------- Produção"
echo "✅ Projeto atualizado e rodando localmente."
