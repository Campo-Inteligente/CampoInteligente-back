#!/bin/bash

# atualizado em 14/08/2025 18h30
clear
echo "🔄 Reiniciando Django Backend e Serviços Relacionados..."

# --- Configurações ---
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
sudo systemctl restart daphne

echo ""
echo "📋 Verificando status do backend:"
backend_status=$(sudo systemctl is-active daphne)

if [[ "$backend_status" == "active" ]]; then
    echo "✅ Backend está ativo!"
else
    echo "❌ Backend falhou ao iniciar!"
    echo "💥 Verifique os logs com:"
    echo "   sudo journalctl -u daphne -n 30 --no-pager"
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
