#!/bin/bash

clear
echo "🔄 Reiniciando serviços do Django..."

# Reiniciar Gunicorn
echo "🚀 Gunicorn..."
sudo systemctl restart gunicorn
sudo systemctl status gunicorn | grep Active

# Reiniciar Daphne
echo "🌐 Daphne..."
sudo systemctl restart daphne
sudo systemctl status daphne | grep Active

# Reiniciar Nginx
echo "📦 Nginx..."
sudo systemctl restart nginx
sudo systemctl status nginx | grep Active

echo "✅ Pronto! Todos os serviços foram reiniciados."

