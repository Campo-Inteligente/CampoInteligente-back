#!/bin/bash

echo "🛑 Finaliza os containers atuais com down..."
docker compose down

echo "📥 Atualizando imagens..."
docker compose pull

echo "🛠️ Recriando e subindo containers com build..."
docker compose up -d --build

echo "📋 Status dos containers:"
docker compose ps
