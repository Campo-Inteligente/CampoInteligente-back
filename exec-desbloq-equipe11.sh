#!/bin/bash

USER="equipe11"

# Desbloqueia o login do usuário
sudo usermod -U "$USER"

# Opcional: desbloqueia a senha
# sudo passwd -u "$USER"

echo "Usuário $USER desbloqueado com sucesso."
