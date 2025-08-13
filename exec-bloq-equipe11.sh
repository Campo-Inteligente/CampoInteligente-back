#!/bin/bash

USER="equipe11"

# Bloqueia o login do usuário
sudo usermod -L "$USER"

# Opcional: expira a senha para impedir login
# sudo passwd -l "$USER"

echo "Usuário $USER bloqueado com sucesso."
