# 🌾 API Campo Inteligente (Backend Django)

Este repositório contém o backend do projeto **Campo Inteligente**, desenvolvido em **Django** com **Django REST Framework**. A API serve a duas funcionalidades principais:

1. **Chatbot Inteligente**: Processa mensagens de múltiplos canais (web e WhatsApp), integra-se com serviços externos (OpenAI, OpenWeather) e gerencia os dados dos usuários agrícolas.

2. **Painel de Controle**: Fornece endpoints seguros para um painel administrativo (desenvolvido separadamente em Next.js) visualizar dados, gerir usuários, extrair insights e e lidar com autenticação e recuperação de contas.
---

## 🚀 Funcionalidades Principais

✅ Módulo Chatbot:
- Integração com webchat e WhatsApp (via Evolution API).
- Fluxo de conversa dinâmico com mensagens gerenciadas pelo banco de dados.
- Respostas inteligentes com a API da OpenAI.
- Previsão do tempo com dados do OpenWeather.

✅ Módulo Painel de Controle (panel):
- Endpoints de API seguros para autenticação de administradores.
- Funcionalidade completa de troca e recuperação de senha via API.
- Gestão de Organizações e Administradores (Criar, Listar, Editar, Excluir) por superusuários.
- Rotas protegidas para fornecer dados de usuários e outras métricas ao frontend.

✅ Gerenciamento de Dados:
- Registro e atualização de usuários e suas propriedades.
- Estrutura extensível para novas funções (ex: estoque, safras).

---

## 🛠 Tecnologias Utilizadas

- **Python 3.8+**
- **Django** + **Django REST Framework**
- **Django Channels** + **ASGI** (suporte a WebSockets)
- **PostgreSQL**
- **Uvicorn** + **Daphne** (servidores assíncronos)
- **httpx** (requisições HTTP assíncronas)
- **python-dotenv** (variáveis de ambiente)
- **openai** (integração com GPT)
- **drf-yasg** (documentação Swagger/OpenAPI)
- **django-cors-headers** (suporte a CORS)
- **psycopg2-binary** (conector PostgreSQL)

---

## ⚙️ Como Rodar Localmente

### 📋 Pré-requisitos

- Python 3.8+
- pip
- PostgreSQL
- Git

### 1. Clone o Repositório

```bash
git clone https://github.com/giselegomes431/API_campointeligente.git
cd API_campointeligente
```

### 2. Crie um Ambiente Virtual

```bash
python -m venv venv

# Windows:
.
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

---

## 📦 Exemplo de `requirements.txt`

```txt
Django>=3.2
djangorestframework
django-cors-headers
django-channels
uvicorn
daphne
httpx
python-dotenv
openai
asgiref
drf-yasg
psycopg2-binary
djangorestframework-simplejwt
```

---

### 4. Configure o `.env`

Crie um arquivo `.env` na mesma pasta onde está o `manage.py` com o seguinte conteúdo:

```ini
SECRET_KEY='sua_chave_secreta_aqui'
DEBUG=True

DB_NAME='campo_inteligente'
DB_USER='postgres'
DB_PASSWORD='sua_senha'
DB_HOST='localhost'
DB_PORT='5432'

OPENAI_API_KEY='sua_chave_openai'
OPENWEATHER_API_KEY='sua_chave_openweather'
EVOLUTION_API_KEY='sua_chave_evolution'
EVOLUTION_API_URL='http://localhost:8080'
EVOLUTION_INSTANCE_NAME='nome_da_instancia'

EMAIL_HOST_USER='seu_email@gmail.com'
EMAIL_HOST_PASSWORD='sua_senha_de_app_do_gmail'
```

> ⚠️ **Importante:** não suba esse arquivo para o GitHub. Adicione `.env` ao seu `.gitignore`.

---

### 5. Configure o Banco de Dados

Certifique-se de que o banco está criado e acessível:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 6. Crie um Superusuário (para o Painel)

```bash
python manage.py createsuperuser
```

---

### 7. Coleta de Arquivos Estáticos

```bash
python manage.py collectstatic
```

---

### 8. Rode o Servidor (ASGI/Uvicorn)

```bash
uvicorn campointeligente.asgi:application --reload
```

Acesse: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📨 Endpoints e Documentação

| Recurso                               | Endpoint                                   |
|---------------------------------------|--------------------------------------------|
| **Chatbot**                                                                        |
| Webhook WhatsApp (POST)               | `/api/v1/chatbot/webhook/`                 |
| Webchat (POST)                        | `/api/v1/chatbot/webchat/`                 |
| **Painel de Controle: Autenticação**                                               |
| Login de Administrador (POST)         | `/api/v1/panel/login/`                     |
| Logout de Administrador (POST)        | `/api/v1/panel/logout/`                    |
| Dados do Usuário Logado (GET)         | `/api/v1/panel/user-data/`                 |
| Trocar Senha (POST, autenticado)      | `/api/v1/panel/password/change/`           |
| Pedido de Recuperação de Senha (POST) | `/api/v1/panel/password/reset/`            |
| Confirmar Nova Senha (POST)           | `/api/v1/panel/password/reset/confirm/`    |
| **Painel de Controle: Gestão**                                                     |
| Listar/Criar Organizações (GET, POST) | `/api/v1/panel/organizacoes/`              |
| Detalhe/Editar/Excluir Organização (GET, PUT, PATCH, DELETE) | `/api/v1/panel/organizacoes/<id>/`      |
| Listar Administradores (GET)          | `/api/v1/panel/administradores/list/`                 |
| Criar Administrador (POST)            | `/api/v1/panel/administradores/create/`    |
| Detalhe/Editar/Excluir Administrador (GET, PUT, PATCH, DELETE) | `/api/v1/panel/administradores/<id>/`   |
| **Documentação**                                                                   |
| Swagger (UI interativa)               | `/api/v1/swagger/`                         |
| Redoc (Documentação limpa)            | `/api/v1/redoc/`                           |

---

## 🧪 Estrutura do Projeto

```
API_campointeligente/
│
├── campointeligente/ # Configurações principais (settings.py, asgi.py, etc.)
│
├── chatbot/          # App do chatbot (views, models, services, etc.)
│
├── panel/            # App do painel de controle (views de auth, models, etc.)
│
├── staticfiles/      # Arquivos estáticos coletados
│
├── manage.py         # Entrada do projeto
│
├── .env              # Configurações sensíveis (NÃO versionar)
│
└── requirements.txt  # Dependências do projeto
```

---

## 👤 Contato

Desenvolvido por **Gisele Gomes**

- 📧 belagisa14@gmail.com  
- 💼 [LinkedIn](https://www.linkedin.com/in/gisele-gomes-oliveira-037bb1128)  
- 📸 [Instagram](https://www.instagram.com/belagisa13)  
- 🐙 [GitHub](https://github.com/giselegomes431)

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**.  
Veja o arquivo [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/giselegomes431/API_campointeligente/blob/main/LICENSE)
 para mais detalhes.
