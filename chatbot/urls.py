from django.urls import path
from .views import webhook_view, webchat_view

urlpatterns = [
    # Rota para o webhook do WhatsApp
    path('webhook', webhook_view, name='webhook'),
    
    # Nova rota para o webchat do site
    path('webchat/', webchat_view, name='webchat'),
]
