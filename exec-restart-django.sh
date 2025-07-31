#atualizado em 31/07/2025 15h01
#!/bin/bash

clear
echo "🔄 Reiniciando Django Backend e Serviços Relacionados..."

# ✅ Coleta de arquivos estáticos
echo ""
echo "📁 Coletando arquivos estáticos via venv:"
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    python manage.py collectstatic --noinput
    deactivate
    echo "✅ Coleta concluída."
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
 
