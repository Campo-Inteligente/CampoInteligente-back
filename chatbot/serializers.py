# chatbot/serializers.py

from rest_framework import serializers

class WebchatPayloadSerializer(serializers.Serializer):
    """
    Serializer para o payload de mensagens recebidas do cliente web (frontend).
    """
    session_id = serializers.CharField(
        max_length=255, 
        required=True, 
        help_text="ID da sessão única do usuário no webchat."
    )
    message = serializers.CharField(
        max_length=1000, 
        required=True, 
        help_text="Conteúdo da mensagem de texto enviada pelo usuário."
    )
    latitude = serializers.FloatField(required=False, help_text="Latitude opcional do usuário.")
    longitude = serializers.FloatField(required=False, help_text="Longitude opcional do usuário.")


class WebhookPayloadSerializer(serializers.Serializer):
    """
    Serializer para o payload de webhooks da Evolution API.
    Contém toda a lógica para filtrar e validar apenas os eventos que nos interessam.
    """
    event = serializers.CharField(required=True)
    instance = serializers.CharField(required=True)
    data = serializers.JSONField(required=True)
    
    def validate(self, attrs):
        """
        Validação personalizada que lida com diferentes tipos de eventos.
        Só permite a passagem de eventos que são mensagens novas de utilizadores.
        """
        event_type = attrs.get('event')

        # 1. Se não for um evento de nova mensagem, falha a validação para ser ignorado pela view.
        if event_type != 'messages.upsert':
            raise serializers.ValidationError(f"Evento '{event_type}' não é uma mensagem de utilizador.")

        # --- CORREÇÃO: Lógica mais flexível para extrair o objeto da mensagem ---
        data_payload = attrs.get('data')
        message_object = None

        # A API pode enviar os dados como uma lista de um item ou como um objeto único.
        # Este código lida com ambos os casos.
        if isinstance(data_payload, list) and data_payload:
            message_object = data_payload[0]
        elif isinstance(data_payload, dict):
            message_object = data_payload
        
        # Se, após a verificação, não tivermos um objeto de mensagem, a validação falha.
        if not message_object or not isinstance(message_object, dict):
            raise serializers.ValidationError("Payload de 'messages.upsert' está vazio ou em formato incorreto.")

        # 2. Agora que temos o objeto da mensagem, validamos a sua estrutura.
        key_data = message_object.get('key', {})

        if key_data.get('fromMe', False):
            raise serializers.ValidationError("Mensagem do próprio bot, ignorada.")

        if not message_object.get('message'):
            raise serializers.ValidationError("Objeto 'message' ausente no evento 'messages.upsert'.")
        
        # 3. Se tudo estiver correto, simplificamos o payload para a view.
        attrs['data'] = message_object
        return attrs

class ChatbotResponseSerializer(serializers.Serializer):
    """
    Serializer para a estrutura de resposta padrão do chatbot.
    """
    response = serializers.CharField(help_text="A resposta gerada pelo chatbot.")
    session_id = serializers.CharField(
        max_length=255, 
        required=False, 
        help_text="O ID da sessão do usuário, retornado para persistência no frontend."
    )
