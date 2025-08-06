#!/bin/bash

# atualizado em 01/08/2025 19h40
clear
echo "🔄 Reiniciando Django Backend e Serviços Relacionados..."

# --- Configurações ---
PORT=21083
LOGFILE="./logs/restart_$(date +%F_%H-%M-%S).log"
mkdir -p ./logs
exec > >(tee -a "$LOGFILE") 2>&1

# ✅ Coleta de arquivos estáticos
echo ""
echo "📁 Coletando arquivos estáticos via venv:"
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    if python manage.py collectstatic --noinput; then
        echo "✅ Coleta concluída."
    else
        echo "❌ Erro na coleta de estáticos!"
    fi
    deactivate
else
    echo "⚠️ Ambiente virtual não encontrado. Pulei a coleta de estáticos."
fi

# 🚀 Reiniciar backend via systemd (Daphne)
echo ""
echo "🚀 Reiniciando Daphne (Django backend)..."
sudo systemctl restart campointeligente-back

echo ""
echo "📋 Verificando status do backend:"
backend_status=$(sudo systemctl is-active campointeligente-back)

if [[ "$backend_status" == "active" ]]; then
    echo "✅ Backend está ativo!"
else
    echo "❌ Backend falhou ao iniciar!"
    echo "💥 Verifique os logs com:"
    echo "   sudo journalctl -u campointeligente-back -n 30 --no-pager"
fi

# 🌐 Verificar e liberar porta antes de reiniciar Nginx
echo ""
echo "🌐 Verificando porta $PORT..."
PID=$(sudo lsof -t -i:$PORT)

if [[ -n "$PID" ]]; then
    echo "⚠️ Porta $PORT está em uso pelo processo $PID. Tentando encerramento gentil..."
    sudo kill $PID
    sleep 2
    if sudo lsof -i:$PORT; then
        echo "🔪 Processo ainda ativo. Forçando encerramento..."
        sudo kill -9 $PID
        echo "✅ Processo $PID finalizado à força. Porta liberada."
    else
        echo "✅ Processo encerrado com sucesso."
    fi
else
    echo "✅ Porta $PORT está livre."
fi

# 🌐 Reiniciar Nginx
echo ""
echo "📦 Reiniciando Nginx (proxy reverso)..."
sudo systemctl restart nginx

echo ""
echo "📋 Verificando status do Nginx:"
nginx_status=$(sudo systemctl is-active nginx)

if [[ "$nginx_status" == "active" ]]; then
    echo "✅ Nginx está ativo!"
else
    echo "❌ Nginx falhou ao iniciar!"
    echo "💥 Verifique os logs com:"
    echo "   sudo journalctl -u nginx -n 30 --no-pager"
fi

echo ""
echo "🎯 Finalizado! Backend reiniciado com as configurações mais recentes."

