from django.urls import path, re_path
from .views import webhook_view, webchat_view

urlpatterns = [
    # Rota para o webhook do WhatsApp
    re_path(r'^webhook(/.*)?$', webhook_view, name='webhook-catchall'),
    
    # Nova rota para o webchat do site
    path('webchat/', webchat_view, name='webchat'),
]
