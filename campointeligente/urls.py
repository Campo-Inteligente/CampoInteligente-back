# campointeligente/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static  # <-- A única importação correta para esta função
from django.http import HttpResponse
from django.templatetags.static import static as static_template_tag # <-- Renomeado para evitar conflito
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

# Views simples
def home(request):
    # Usamos o 'static_template_tag' que renomeamos
    logo_url = request.build_absolute_uri(static_template_tag('img/1.png'))
    html = f"""
    <html>
        <head>
            <meta http-equiv="refresh" content="2; url=/admin/" />
            <style>
                body {{ display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .container {{ text-align: center; }}
                img {{ max-width: 80%; height: auto; margin-bottom: 20px; }}
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

def teste_view(request):
    return HttpResponse("Funcionando!")

# Configuração do Swagger
schema_view = get_schema_view(
   openapi.Info(
        title="API Campo Inteligente",
        default_version='v1',
        description="Documentação da API Backend para o projeto Campo Inteligente.",
        contact=openapi.Contact(email="startupcampointeligente@gmail.com"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Bloco de URLs principal
urlpatterns = [
    # Página inicial e testes
    path('', home, name='home'),
    path('teste/', teste_view, name='teste'),

    # Admin
    path('admin/', admin.site.urls),
    path('admin/login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='admin_login'),
    path('admin/logout/', auth_views.LogoutView.as_view(template_name='admin/logged_out.html'), name='admin_logout'),

    # Reset de senha (admin)
    path('admin/password_reset/', auth_views.PasswordResetView.as_view(), name='admin_password_reset'),
    path('admin/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='admin_password_reset_done'),
    path('admin/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='admin_password_reset_confirm'),
    path('admin/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='admin_password_reset_complete'),

    # APIs
    path('api/v1/chatbot/', include('chatbot.urls')),
    path('api/v1/panel/', include('panel.urls')),

    # Swagger / Redoc
    re_path(r'^api/v1/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Adiciona as URLs para servir arquivos estáticos APENAS em modo de desenvolvimento (DEBUG=True)
# if settings.DEBUG:
#    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)