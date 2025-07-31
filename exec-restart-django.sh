#!/bin/bash

clear
echo "🔄 Reiniciando Django Backend e Serviços Relacionados..."

# Ativa o venv temporariamente para rodar collectstatic
echo "📁 Coletando arquivos estáticos:"
source /var/www/campointeligente-back/venv/bin/activate
python manage.py collectstatic --noinput
deactivate

# Reiniciar backend
echo "🚀 Reiniciando Gunicorn (Django backend)..."
sudo systemctl restart gunicorn
sudo systemctl status gunicorn | grep Active

# Reiniciar nginx
echo "📦 Reiniciando Nginx (proxy reverso)..."
sudo systemctl restart nginx
sudo systemctl status nginx | grep Active

echo "✅ Pronto! Django e Nginx reiniciados com sucesso."
