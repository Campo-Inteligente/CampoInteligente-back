#!/bin/bash

echo "📦 Pegando atualizações no github.com..."

# Garante que estamos no diretório correto
cd "$(dirname "$0")" || {
  echo "❌ Erro ao acessar diretório do projeto."
  exit 1
}

# Busca atualizações do GitHub
git fetch origin

# Reseta forçadamente para o estado mais recente da branch main
git reset --hard origin/main

echo "✅ Projeto local atualizado com sucesso!"

