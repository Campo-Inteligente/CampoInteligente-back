from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Views simples para teste
def teste_view(request):
    return HttpResponse("Teste Funcionando!")

def home(request):
    return HttpResponse("Olá, Campo Inteligente API está rodando!")

# Swagger / Redoc
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
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

# Todas as URLs reunidas em um único bloco
urlpatterns = [

    #path('grappelli/', include('grappelli.urls')),  # Grappelli URLs
    #path('jazzmin/', include('jazzmin.urls')),  # Jazzmin URLs
    path('', home),  # Rota raiz
    path('admin/', admin.site.urls),

    # O /?$ torna a barra final opcional
    #re_path(r'^teste/?$', views.teste_view, name='teste'),
    path('teste/', teste_view),  # Teste rápido

    # APIs principais
    path('api/v1/chatbot/', include('chatbot.urls')),
    path('api/v1/panel/', include('panel.urls')),

    # Swagger / Redoc
    re_path(r'^api/v1/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Arquivos estáticos durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Se tiver arquivos de mídia:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
