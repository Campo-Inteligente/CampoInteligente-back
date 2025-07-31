#!/bin/bash
echo "🚀 Subindo o BACKEND..."

cd /var/www/campointeligente-back

source venv/bin/activate

# (Opcional) Atualizar dependências e aplicar migrations
# pip install -r requirements.txt
# python manage.py migrate

pm2 start daphne --name "campointeligente-back" --interpreter python3 -- -p 21083 campointeligente.asgi:application
pm2 save

echo "✅ Backend online!"
