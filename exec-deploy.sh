#!/bin/bash

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
echo "📖 Acompanhando logs do serviço (CTRL+C para sair)..."
sudo journalctl -u chatbot.service -f


echo ""
echo "✅ Projeto atualizado e rodando localmente na porta 3000"
echo "🌐 Acesso externo:"
echo "✅http://campointeligente.ddns.com.br:21081/ <------- website"
echo "✅http://campointeligente.ddns.com.br:21082/ <------- back"
echo "✅http://campointeligente.ddns.com.br:21050/ <------- pgadmin"
echo "✅http://campointeligente.ddns.com.br:21085/docs <--- API"
echo "  https://www.campointeligente.agr.br/ <------------- Produção"
