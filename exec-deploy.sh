#!/bin/bash

clear
set -e  # Para o script parar se qualquer comando falhar

echo "============================================"
echo "🚀 Iniciando processo de *Deploy Automático*"
echo "============================================"

# Parar containers atuais
echo ""
echo "🛑 Finalizando containers atuais com 'docker compose down'..."
docker compose down

# Atualizar imagens
echo ""
echo "📥 Atualizando imagens do docker..."
docker compose pull

# Recriar containers com build e iniciar em segundo plano
echo ""
echo "🔨 Buildando e subindo containers com 'docker compose up -d --build'..."
docker compose up -d --build

# Mostrar status dos containers
echo ""
echo "📋 Verificando status dos containers..."
docker compose ps



# --------- SERVIÇO DO ANTIGO PROJETO ----------------------------------
# Reiniciar serviço systemd
#echo ""
#echo "🔁 Reiniciando serviço systemd: chatbot.service"
#sudo systemctl daemon-reexec
#sudo systemctl restart chatbot.service

# Mostrar status do serviço
# echo ""
# python manage.py runserver 0.0.0.0:8010

#echo ""
#echo "🩺 Verificando status do serviço chatbot.service..."
#sudo systemctl status chatbot.service --no-pager

# Logs em tempo real
#echo "📖 Acompanhando logs do serviço (CTRL+C para sair)..."
#sudo journalctl -u chatbot.service -f
# --------- SERVIÇO DO ANTIGO PROJETO -----------------------------------------



# -------- INICIO CONFIGURANDO INSTANCIAS #------------------------------------
./exec-config_instancia.sh
# -------- INICIO CONFIGURANDO INSTANCIAS #------------------------------------

# -------- SUBINDO DJANGO #----------------------------------------------------
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

# Se já houver um ambiente virtual ativo, desativa
if [[ "$VIRTUAL_ENV" != "" ]]; then
    deactivate
fi

# Cria e ativa o novo ambiente virtual
python3 -m venv venv

if [[ -f "venv/bin/activate" ]]; then
    source /var/www/campointeligente-back/venv/bin/activate
else
    echo "⚠️ Script de ativação não encontrado!"
fi

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

# Detecta se o projeto usa Django Channels
if pip freeze | grep -iq "channels"; then
    echo "📡 Detecção: Django Channels encontrado. Usando Daphne (ASGI)..."
    daphne -b 0.0.0.0 -p 21083 campointeligente.asgi:application
else
    echo "🐘 Sem Channels instalado. Usando Gunicorn (WSGI)..."
    gunicorn campointeligente.wsgi:application --workers 3 --bind 0.0.0.0:21083
fi


echo " Reiniciando o Django"
./exec-restart-django.sh
# -------- SUBINDO DJANGO #----------------------------------------------------

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
