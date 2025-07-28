@echo off
rem # 1. Vá até o diretório do seu repositório local
cd /caminho/do/seu/repositorio

rem # 2. Limpe todas as mudanças locais não comitadas
git reset --hard

rem # 3. Apague as alterações nos arquivos não monitorados (ex: novos arquivos)
git clean -fd

rem # 4. Atualize o repositório local com a versão do servidor (remoto)
git pull origin main --force
