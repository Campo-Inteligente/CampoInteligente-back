import os
from pathlib import Path
from dotenv import load_dotenv

# --- Diretório Base ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Carregar variáveis do .env ---
load_dotenv(BASE_DIR / '.env')

# --- Segurança e Debug ---
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = [
    'd60fa466aac5.ngrok-free.app',
    '127.0.0.1',
    'localhost',
    'campointeligente.ddns.com.br'
]

CSRF_TRUSTED_ORIGINS = [
    "http://campointeligente.ddns.com.br:21083",
    "https://campointeligente.ddns.com.br",
    "http://localhost",
    "http://127.0.0.1",
]
# serve para evitar erros 404 quando uma URL não termina com uma barra (/).
APPEND_SLASH = True

# --- Aplicações Instaladas ---
INSTALLED_APPS = [
    #'grappelli',
    'jazzmin',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'chatbot',
]

# --- ASGI ---
ASGI_APPLICATION = 'campointeligente.asgi.application'

# --- Middleware ---
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise logo após CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- URLs e Templates ---
ROOT_URLCONF = 'campointeligente.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'campointeligente.wsgi.application'

# --- Banco de Dados ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'client_encoding': 'UTF8'
        },
    }
}

# --- Validação de Senhas ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internacionalização ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# --- Arquivos Estáticos ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise: serve arquivos estáticos em produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Tipo padrão de campo automático ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configurações Personalizadas ---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL')
EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME')

# --- CORS ---
CORS_ALLOW_ALL_ORIGINS = True

# --- Configurações de Email ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER



JAZZMIN_SETTINGS = {
    "site_logo": "img/logo.png",  	# Caminho relativo ao diretório static
    #"site_logo_classes": "img-circle", # Estilo opcional
    "site_icon": "img/favicon.ico",  	# Caminho para o favicon

    "site_title": "API CampoI",
    "site_header": "API CampoI",
    "site_brand": "API CampoI",
    "welcome_sign": "Bem-vindo ao Painel de Controle da API CampoI",
    "copyright": "© 2025 Campo Inteligente. Todos os direitos reservados",
    "show_sidebar": True,
    "navigation_expanded": True,
    "changeform_format": "horizontal_tabs",
    "show_ui_builder": True,
}


JAZZMIN_UI_TWEAKS = {
    #"theme": "minty",  			# Base verde claro e agradável
    #"dark_mode_theme": "darkly",  		# Se quiser opção escura
    #"navbar": "navbar-light",     		# Fundo claro para destacar o logo
    #"accent": "accent-success",   		# Verde como cor de destaque
    #"sidebar": "sidebar-light-success",  	# Verde claro na lateral
    #"button_classes": {
    #    "primary": "btn-success",       	# Botões com tom agro
    #    "secondary": "btn-outline-success",
    #},
    #"brand_colour": "success",  		# Verde personalizado
}


