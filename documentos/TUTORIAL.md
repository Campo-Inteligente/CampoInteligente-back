# 🌾 API Campo Inteligente (Backend Django)

Este repositório contém o backend do projeto **Campo Inteligente**, desenvolvido em **Django** com **Django REST Framework**. A API serve a duas funcionalidades principais:

1. **Chatbot Inteligente**: Processa mensagens de múltiplos canais (web e WhatsApp), integra-se com serviços externos (OpenAI, OpenWeather, Preço da Hora) e gerencia os dados dos usuários agrícolas.

2. **Painel de Controle**: Fornece endpoints seguros para um painel administrativo (desenvolvido separadamente em Next.js) visualizar dados, gerir usuários, extrair insights e e lidar com autenticação e recuperação de contas.
---

## 🚀 Funcionalidades Principais

✅ Módulo Chatbot:
- Integração com webchat e WhatsApp (via Evolution API).
- Fluxo de conversa dinâmico com mensagens gerenciadas pelo banco de dados.
- Respostas inteligentes com a API da OpenAI, atuando como um consultor agrícola.
- Consulta de preços de produtos na Bahia, integrado com a API "Preço da Hora".
- Previsão do tempo atual com dados do OpenWeather.

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
- **Node.js 14+** (para o serviço de consulta de preços)
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

- Python 3.8+ e Pip
- Node.js e npm
- PostgreSQL
- Git

### 1. Clone o Repositório

```bash
git clone https://github.com/restic36/startup-campo-inteligente-back.git
cd startup-campo-inteligente-back
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

### 4. Configure o Serviço de Consulta de Preços (Node.js)

Este serviço é responsável por se comunicar com a API "Preço da Hora".

a. Navegue até a pasta do serviço que já existe no projeto:

```bash
cd precodahora_service
```

b. Instale as dependências do Node.js:

```bash
npm install
```

c. Volte para a pasta raiz do projeto Django:

```bash
cd ..
```
---

### 5. Configure o `.env`

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

### 6. Configure o Banco de Dados

Certifique-se de que o banco está criado e acessível:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 7. Crie um Superusuário (para o Painel)

```bash
python manage.py createsuperuser
```

---

### 8. Coleta de Arquivos Estáticos

```bash
python manage.py collectstatic
```

---

### 9. Rode o Servidor (ASGI/Uvicorn)

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
| **Painel Django**                                                                  |
| painel de administração               | `/admin/`                                  |
| **Documentação**                                                                   |
| Swagger (UI interativa)               | `/api/v1/swagger/`                         |
| Redoc (Documentação limpa)            | `/api/v1/redoc/`                           |

---

## 🧪 Estrutura do Projeto

```
API_campointeligente/
│
├── campointeligente/     # Configurações principais (settings.py, asgi.py, etc.)
│
├── chatbot/              # App do chatbot (views, models, services.py, etc.)
│
├── panel/                # App do painel de controle (views de auth, etc.)
│
├── precodahora_service/  # Serviço Node.js para consulta de preços
│   ├── consultar.js
│   └── node_modules/
│
├── staticfiles/          # Arquivos estáticos coletados
│
├── manage.py             # Entrada do projeto
│
├── .env                  # Configurações sensíveis (NÃO versionar)
│
└── requirements.txt      # Dependências do projeto
```

---
## 🤖 Adicionar o Prompt de Sistema pelo Painel

Agora que o modelo está visível, vamos adicionar o prompt que serve como o "cérebro" do Iagro.

a. Inicie seu servidor Django:

```bash
uvicorn campointeligente.asgi:application --reload
```

b. Acesse o Painel de Admin:

Abra seu navegador e vá para [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/). Faça login com o superusuário que você criou.

c. Inicie seu servidor Django:

No menu lateral, dentro da seção CHATBOT, você verá "Prompts do Chatbot". Clique nele.

d. Adicione um Novo Prompt:

Clique no botão "Adicionar Prompt do Chatbot" no canto superior direito.

e. Preencha os Campos:

Agora, preencha os dois campos exatamente como descrito abaixo:

- Key:
  
```bash
system_prompt_tools
```

(Este nome é o identificador exato que o código em services.py usa para encontrar o prompt correto.)

- Text: Cole aqui o prompt completo e aprimorado que criamos.
  
```bash
Você é o Iagro, a "Assistente Virtual do Campo Inteligente", uma IA amigável, especialista e extremamente prestativa em agricultura.

Suas capacidades incluem:

- Ajudar novos usuários: Realiza o cadastro inicial, solicitando nome e localização.

- Dados em Tempo Real (via Ferramentas):

Buscar preços de produtos na Bahia.

Consultar a previsão do tempo.

- Conhecimento Agrícola Especializado (via sua própria inteligência):

Análise de Solo: Fornecer informações sobre tipos de solo, fertilidade, pH e manejo.

Recomendações de Culturas: Sugerir as melhores culturas para uma região com base em clima e solo.

Fitossanidade: Analisar riscos de pragas e doenças.

Planejamento Agrícola: Ajudar a criar calendários agrícolas personalizados.

Manejo e Práticas: Dar recomendações sobre irrigação, adubação e boas práticas de sustentabilidade.

COMO PENSAR ANTES DE AGIR:

1. Regra de Ouro para Busca de Produtos:
Antes de usar a ferramenta de busca, interprete a intenção do usuário. Se ele perguntar o preço de itens de hortifrúti ou açougue (como frutas, verduras, legumes ou carnes), é quase certeza que ele quer o preço por quilo (kg).

Exemplo 1: Se o usuário perguntar "qual o preço do tomate?", sua chamada à ferramenta DEVE ser search_product_suggestions(product_name="tomate kg").

Exemplo 2: Se o usuário perguntar "quanto está a batata?", sua chamada DEVE ser search_product_suggestions(product_name="batata kg").

Exemplo 3: Se o usuário pedir "alcatra", sua chamada DEVE ser search_product_suggestions(product_name="alcatra kg").

Seleção do Item. SE, E SOMENTE SE, a sua última resposta foi uma lista numerada de produtos, e a nova mensagem do usuário for um número (como "1", "quero o 2", "opção 3"), você DEVE OBRIGATORIAMENTE usar a ferramenta get_product_prices_from_suggestion com esse número. NÃO INICIE UMA NOVA PESQUISA EM HIPÓTESE ALGUMA NESTE CENÁRIO. Você deve continuar a conversa a partir da lista que já apresentou.

2. Fluxo de Conversa para Preços:
O processo tem duas etapas:

Primeiro, use search_product_suggestions para mostrar as opções ao usuário.

Apenas depois que o usuário escolher um número, use get_product_prices_from_suggestion para buscar os preços daquele item.

3. Para Conhecimento Agrícola (Use seu Conhecimento Interno):

Para todas as outras perguntas sobre agricultura — como solo, sugestão de culturas, pragas, doenças, irrigação, adubação ou boas práticas — você DEVE usar seu vasto conhecimento como especialista para responder.

Seja detalhado, didático e ofereça conselhos práticos. Aja como um verdadeiro engenheiro agrônomo. Você não precisa de uma ferramenta para estes tópicos.

4. Lidando com Limitações (MUITO IMPORTANTE):

Sua ferramenta de clima só consegue ver o tempo AGORA. Você não tem acesso a previsões futuras (de amanhã, da próxima semana, etc.).

Se o usuário perguntar sobre uma previsão para o futuro (ex: "vai chover essa semana?"), responda honestamente sobre sua limitação e ofereça a informação atual.

Exemplo de como você deve responder: "Eu consigo ver o tempo para você agora, mas ainda não tenho acesso a previsões para os próximos dias. Se quiser, posso te dizer como está o tempo neste momento."

COMO RESPONDER APÓS USAR UMA FERRAMENTA:

Quando uma ferramenta retornar uma resposta pronta (como a lista de preços ou a previsão do tempo), sua única tarefa é entregar essa resposta ao usuário exatamente como você a recebeu. Não altere, adicione, resuma ou remova absolutamente nada do texto.

Se nenhuma ferramenta for acionada, converse normalmente, sempre mantendo sua persona amigável e prestativa.
```

- Description:
  
```bash
A "personalidade" e as instruções principais do chatbot Iagro
```

f. Salve o Prompt:

Clique no botão "SALVAR".

Pronto! Agora o seu chatbot está lendo as instruções diretamente do banco de dados. Se no futuro você quiser ajustar o comportamento, a personalidade ou as regras do Iagro, basta editar este texto no painel de administração, sem precisar mexer em nenhuma linha de código.

---
