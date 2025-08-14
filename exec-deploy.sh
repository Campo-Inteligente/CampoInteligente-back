#!/bin/bash

clear
set -e  # Para o script parar se qualquer comando falhar

echo "============================================"
echo "🚀 Iniciando processo de *Deploy Automático*"
echo "============================================"

PORT=21083
echo ""
echo "🔍 Verificando se porta $PORT está em uso..."
if lsof -i tcp:$PORT >/dev/null; then
    echo "⚠️ Porta $PORT está em uso! Finalizando processo antes de subir servidor..."
    PID=$(lsof -ti tcp:$PORT)
    kill -9 $PID
    echo "✅ Processo finalizado (PID: $PID)."
fi

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
# 📦 PARTE 3: Ambiente Python/Django para Produção
# ----------------------------------------------------------------------

echo ""
echo "📦 Instalando dependências:"
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "📁 Coletando arquivos estáticos:"
python manage.py collectstatic --noinput

echo ""
echo "🔄 Migrando banco de dados:"
python manage.py migrate
deactivate

# ----------------------------------------------------------------------
# 🚀 PARTE 4: Reiniciar Daphne via systemd
# ----------------------------------------------------------------------

echo ""
echo "🚀 Reiniciando Daphne via systemd..."
sudo systemctl restart daphne

# ----------------------------------------------------------------------
# 🔁 PARTE 5: Reinicialização auxiliar (exec-restart-django.sh)
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
