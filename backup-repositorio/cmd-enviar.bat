@echo off
rem # 1. Vá até o diretório do seu repositório local
cd /caminho/do/seu/repositorio

rem # 2. Adiciona todos os arquivos modificados e novos
git add .

rem # 3. Faz o commit com uma mensagem personalizada
git commit -m "Atualizações enviadas pelo script"

rem # 4. Envia para a branch main do repositório remoto
git push origin main
