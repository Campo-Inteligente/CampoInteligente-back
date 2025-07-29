# campointeligente/campointeligente/urls.py


from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Importe 'settings' e 'static' para servir arquivos estáticos em desenvolvimento
from django.conf import settings # <-- Adicione esta linha
from django.conf.urls.static import static # <-- Adicione esta linha

# Não é necessário importar AllowAny e BasicAuthentication diretamente aqui
# se você já está usando permissions.AllowAny na configuração do schema_view.
# from rest_framework.permissions import AllowAny
# from rest_framework.authentication import BasicAuthentication

from django.http import HttpResponse

def home(request):
    return HttpResponse("Olá, Campo Inteligente API está rodando!")

urlpatterns = [
    path('', home),  # rota raiz
    path('admin/', admin.site.urls),
    path('api/v1/chatbot/', include('chatbot.urls')),
    # ... restante das rotas
]

schema_view = get_schema_view(
    openapi.Info(
        title="API Campo Inteligente",
        default_version='v1',
        description="Documentação da API Backend para o projeto Campo Inteligente.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="startupcampointeligente@gmail.com"),
        license=openapi.License(name="Licença MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,), # Use permissions.AllowAny
    authentication_classes=[], # Mantenha vazio se não tiver autenticação para a doc
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/chatbot/', include('chatbot.urls')), # Suas URLs da app chatbot

    # URLs da documentação Swagger/Redoc
    re_path(r'^api/v1/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # linha para as rotas do painel
    path('api/v1/panel/', include('panel.urls')), 
]


# --- CONFIGURAÇÃO PARA SERVIR ARQUIVOS ESTÁTICOS EM AMBIENTE DE DESENVOLVIMENTO ---
# Este bloco é CRUCIAL para que o Redoc e outros arquivos estáticos sejam carregados
# quando DEBUG=True. Em produção, um servidor web como Nginx ou Apache faria isso.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Se você tiver arquivos de mídia (uploads de usuário) e um MEDIA_ROOT configurado,
    # adicione a linha abaixo também:
    # from django.conf import settings
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
