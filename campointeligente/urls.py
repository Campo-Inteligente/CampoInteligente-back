# Imports padrão da biblioteca Python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

# Imports de terceiros
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

# Imports locais (quando houver)
# from . import views


# Views simples para teste
def teste_view(request):
    return HttpResponse("Funcionando!")

def home(request):
    #return HttpResponse("Olá, Campo Inteligente API está rodando!")
    #return redirect('/admin/')
    logo_url = static('img/1.png')
    html = """
    <html>
        <head>
            <meta http-equiv="refresh" content="2; url=/admin/" />
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                }
                .container {
                    text-align: center;
                }
                .container img {
                    max-width: 80%%;
                    height: auto;
                    margin-bottom: 20px;
                }
                h2 {
                    color: #333;
                    font-size: 1.8em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="{logo_url}" alt="Logo">
                <h2>BEM-VINDO À CAMPO INTELIGENTE</h2>
            </div>
        </body>
    </html>
    """

    return HttpResponse(html)

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

    #path('grappelli/', include('grappelli.urls')), # tema
    path('', home),  # Rota raiz
    path('admin/', admin.site.urls),
    path('teste/', teste_view),  # Teste rápido

    # Ativar o fluxo de reset de senha do Django
    path('admin/password_reset/', auth_views.PasswordResetView.as_view(), name='admin_password_reset'),
    path('admin/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('admin/', admin.site.urls),

    # APIs principais
    path('api/v1/chatbot/', include('chatbot.urls')),
    path('api/v1/panel/', include('panel.urls')),

    # Swagger / Redoc

    re_path(
       r'^api/v1/swagger(?P<format>\.json|\.yaml)$',
       schema_view.without_ui(cache_timeout=0),
       name='schema-json'
    ),

    path('api/v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
]


# Arquivos estáticos durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Se tiver arquivos de mídia:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
