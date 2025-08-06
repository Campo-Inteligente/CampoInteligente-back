# chatbot/views.py

import json
import logging
import re
from asgiref.sync import async_to_sync

from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt

from .serializers import WebchatPayloadSerializer, WebhookPayloadSerializer, ChatbotResponseSerializer
from .services import ChatbotService

logger = logging.getLogger(__name__)
chatbot_service = ChatbotService()

@swagger_auto_schema(
    method='post',
    request_body=WebchatPayloadSerializer,
    responses={200: ChatbotResponseSerializer}
)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def webchat_view(request):
    serializer = WebchatPayloadSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error("Erro de validação (Webchat): %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    session_id, message_text = data['session_id'], data['message']
    user_id = f"webchat_{session_id}"
    
    try:
        location_data = {"latitude": data['latitude'], "longitude": data['longitude']} if 'latitude' in data and 'longitude' in data else None
        
        response_text = async_to_sync(chatbot_service.process_message)(
            user_id, message_text, "Visitante", 'webchat', location_data
        )
        
        return Response({"response": response_text, "session_id": session_id}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Erro ao processar webchat para user_id: {user_id}")
        return Response(
            {"response": "Desculpe, ocorreu um erro no nosso servidor."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(method='post', request_body=WebhookPayloadSerializer)
@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def webhook_view(request):
    logger.info("Webhook recebido: %s", request.data)

    # A lógica de validação agora está centralizada no serializer.
    # A view apenas tenta validar e, se falhar, ignora o evento.
    serializer = WebhookPayloadSerializer(data=request.data)
    if not serializer.is_valid():
        # Se a validação falhar, é porque não é uma mensagem que nos interessa.
        # Retornamos 200 OK para que a API não continue a reenviar o webhook.
        logger.warning("Payload inválido ou ignorado: %s", serializer.errors)
        return Response({"status": "Evento ignorado ou inválido"}, status=status.HTTP_200_OK)

    validated_data = serializer.validated_data
    
    try:
        # O serializer já garantiu que 'data' é um dicionário (objeto da mensagem), não mais uma lista.
        data_payload = validated_data.get('data', {})
        
        key_data = data_payload.get('key', {})
        user_id = key_data.get('remoteJid')
        
        push_name = data_payload.get('pushName', 'Utilizador')
        message_data = data_payload.get('message', {})
        message_text = ""
        location_data = None

        if 'conversation' in message_data and message_data.get('conversation'):
            message_text = message_data['conversation']
        elif 'extendedTextMessage' in message_data:
            message_text = message_data.get('extendedTextMessage', {}).get('text', '')
        elif 'locationMessage' in message_data:
            loc_msg = message_data['locationMessage']
            if 'degreesLatitude' in loc_msg and 'degreesLongitude' in loc_msg:
                location_data = {"latitude": loc_msg['degreesLatitude'], "longitude": loc_msg['degreesLongitude']}
        else:
            logger.info(f"Tipo de mensagem não suportado recebido de {user_id}.")
            return Response({"status": "Tipo de mensagem não suportado"}, status=status.HTTP_200_OK)

        response_text = async_to_sync(chatbot_service.process_message)(
            user_id, message_text, push_name, 'whatsapp', location_data
        )

        if response_text:
            async_to_sync(chatbot_service.send_whatsapp_message)(user_id, response_text)
        
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception(f"Erro interno ao processar webhook: {e}")
        return Response({"error": "Erro interno do servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
