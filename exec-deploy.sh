#!/bin/bash

clear
set -e  # Para o script parar se qualquer comando falhar

echo "============================================"
echo "🚀 Iniciando processo de *Deploy Automático*"
echo "============================================"

PORT=21084
echo ""
echo "🔍 Verificando se porta $PORT está em uso..."
if lsof -i tcp:$PORT >/dev/null; then
    echo "⚠️ Porta $PORT está em uso! Finalizando processo antes de subir servidor..."
    PID=$(lsof -ti tcp:$PORT)
    kill -9 $PID
    echo "✅ Processo finalizado (PID: $PID)."
fi

# ----------------------------------------------------------------------
# 🛠️ BLOCO OPCIONAL: Reinício de serviço SystemD (ex: chatbot.service)
# Esse bloco era usado em versões anteriores com systemd. Mantido aqui.
# ----------------------------------------------------------------------
# echo ""
# echo "🔁 Reiniciando serviço systemd: chatbot.service"
# sudo systemctl daemon-reexec
# sudo systemctl restart chatbot.service
# 
# echo ""
# echo "🩺 Verificando status do serviço chatbot.service..."
# sudo systemctl status chatbot.service --no-pager
# 
# echo "📖 Acompanhando logs do serviço (CTRL+C para sair)..."
# sudo journalctl -u chatbot.service -f

# ----------------------------------------------------------------------
# 🔧 PARTE 1: Containers Docker (serviços auxiliares como banco, frontend etc)
# ----------------------------------------------------------------------

echo ""
echo "🛑 Finalizando containers atuais com 'docker compose down'..."
docker compose down

echo ""
echo "📥 Atualizando imagens do docker..."
docker compose pull

echo ""
echo "🔨 Buildando e subindo containers com 'docker compose up -d --build'..."
docker compose up -d --build

echo ""
echo "📋 Verificando status dos containers..."
docker compose ps

# ----------------------------------------------------------------------
# ⚙️ PARTE 2: Execução de script interno de configuração da instância
# ----------------------------------------------------------------------
./exec-config_instancia.sh

# ----------------------------------------------------------------------
# 🧪 BLOCO OPCIONAL: Criar projeto Django do zero (caso novo projeto)
# Esse bloco pode ser usado se for iniciar um projeto Django novo do zero.
# ----------------------------------------------------------------------
# echo ""
# echo "✅ Criar ambiente virtual:"
# python -m venv venv
# source venv/bin/activate
#
# echo ""
# echo "📦 Instalar Django:"
# pip install django
#
# echo ""
# echo "🏗️ Criar projeto:"
# django-admin startproject nome_projeto
# cd nome_projeto
#
# echo ""
# echo "🧱 Criar apps e modelos:"
# python manage.py startapp nome_app
#
# echo ""
# echo "🔄 Migrar banco de dados:"
# python manage.py makemigrations
# python manage.py migrate
#
# echo ""
# echo "🧪 Testar localmente:"
# python manage.py runserver 0.0.0.0:21083

# ----------------------------------------------------------------------
# 📦 PARTE 3: Ambiente Python/Django para Produção
# ----------------------------------------------------------------------

# Desativar venv atual (se houver)
if [[ "$VIRTUAL_ENV" != "" ]]; then
    deactivate
fi

# Criar e ativar novo ambiente virtual
python3 -m venv venv
if [[ -f "venv/bin/activate" ]]; then
    source /var/www/campointeligente-back/venv/bin/activate
else
    echo "⚠️ Script de ativação não encontrado!"
fi

echo ""
echo "📦 Instalando dependências:"
pip install -r requirements.txt

echo ""
echo "🛠️ Lembrete: ajustar banco de dados, ALLOWED_HOSTS e DEBUG = False no settings.py"

echo ""
echo "📁 Coletando arquivos estáticos:"
python manage.py collectstatic --noinput

echo ""
echo "🔄 Migrando banco de dados:"
python manage.py migrate

# ----------------------------------------------------------------------
# 🔐 BLOCO OPCIONAL: Criar superusuário do Django
# ----------------------------------------------------------------------
# echo ""
# echo "🧑‍💻 Criar superusuário (opcional):"
# python manage.py createsuperuser

# ----------------------------------------------------------------------
# 🚀 PARTE 4: Subir Django com Daphne ou Gunicorn (sem logs)
# ----------------------------------------------------------------------

# Criar pasta de logs (opcional)
mkdir -p logs

echo ""
echo "🚀 Subindo Django em Produção na porta $PORT..."

# Detecta se o projeto usa Django Channels
if pip freeze | grep -iq "channels"; then
    echo "📡 Django Channels detectado. Usando Daphne (ASGI)..."
    nohup daphne -b 0.0.0.0 -p $PORT campointeligente.asgi:application > /dev/null 2>&1 &
else
    echo "🐘 Channels não encontrado. Usando Gunicorn (WSGI)..."
    nohup gunicorn campointeligente.wsgi:application --workers 3 --bind 0.0.0.0:$PORT > /dev/null 2>&1 &
fi

# ----------------------------------------------------------------------
# 🔁 PARTE 5: Reinicialização auxiliar (exec-restart-django.sh)
# Útil para recarregar qualquer outro serviço, cache ou dependência
# ----------------------------------------------------------------------
./exec-restart-django.sh

# ----------------------------------------------------------------------
# 🔗 PARTE 6: URLs do sistema e confirmação final
# ----------------------------------------------------------------------

echo ""
echo "🌐 Acesso externo:"
echo "✅ http://campointeligente.ddns.com.br:21081/ <------- Website Validação"
echo "✅ http://campointeligente.ddns.com.br:21082/ <------- Back off"
echo "✅ http://campointeligente.ddns.com.br:21083/ <------- API (Django)"
echo "✅ http://campointeligente.ddns.com.br:21050/ <------- PgAdmin"
echo "✅ http://campointeligente.ddns.com.br:21085/ <------- EvolutionAPI"
echo "✅ https://www.campointeligente.agr.br/ <------------- Website Produção"
echo "✅ Projeto atualizado e rodando com sucesso!"
