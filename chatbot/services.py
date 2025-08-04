# chatbot/services.py

import httpx
from openai import AsyncOpenAI
import re
import json
import logging
from typing import List, Dict, Any, Tuple

from django.conf import settings
from .models import Usuario, Prompt, State, Interacao
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

OPENAI_MODEL = "gpt-4o-mini"

class ChatbotService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.openai_client = None

        self.state_map_by_name: Dict[str, str] = {}
        
        self.tools = self._get_tool_definitions()
        self.tool_dispatcher = {
            "get_weather_for_city": self._tool_wrapper_get_weather,
            "register_user_location": self._tool_wrapper_register_location,
            "get_user_registered_location": self._tool_wrapper_get_user_location,
            "complete_user_onboarding": self._tool_wrapper_complete_onboarding,
            "get_weather_for_current_location": self._tool_wrapper_get_weather_for_coords,
        }

    # --- Funções de DB e Auxiliares ---
    @database_sync_to_async
    def _get_all_states(self) -> List[State]: return list(State.objects.all())
    @database_sync_to_async
    def _get_prompt(self, key: str) -> str:
        try: return Prompt.objects.get(key=key).text
        except Prompt.DoesNotExist: return f"Prompt '{key}' não configurado."
    @database_sync_to_async
    def get_or_create_user(self, user_identifier: str, push_name: str, channel: str) -> Tuple[Usuario, bool]:
        user, created = Usuario.objects.get_or_create(whatsapp_id=user_identifier, defaults={'nome': push_name if channel == 'whatsapp' else 'Visitante', 'organizacao_id': 1})
        if not isinstance(user.contexto, dict): user.contexto = {}
        return user, created
    @database_sync_to_async
    def save_user(self, user: Usuario): user.save()
    @database_sync_to_async
    def _log_interaction(self, user: Usuario, user_message: str, bot_response: str):
        if not bot_response: return
        Interacao.objects.create(agricultor=user, mensagem_usuario=user_message, resposta_chatbot=bot_response)
        
    # --- Funções de APIs Externas ---
    async def get_weather_data(self, city: str) -> dict:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": f"{city},BR", "appid": settings.OPENWEATHER_API_KEY, "units": "metric", "lang": "pt_br"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return {"cidade": data.get('name'), "descricao": data['weather'][0]['description'], "temperatura": data['main']['temp'], "sensacao_termica": data['main']['feels_like'], "umidade": data['main']['humidity']}
            except Exception: pass
        return {"error": f"Cidade '{city}' não encontrada."}
    async def get_location_details_from_city(self, city: str) -> dict:
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {"q": f"{city},BR", "limit": 1, "appid": settings.OPENWEATHER_API_KEY}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200 and response.json():
                    return response.json()[0]
            except Exception: pass
        return {"error": f"Não foi possível encontrar detalhes para a cidade '{city}'."}
    async def get_weather_data_from_coords(self, lat: float, lon: float) -> dict:
        # Implementação omitida por brevidade
        pass

    # --- Wrappers de Ferramentas ---
    async def _tool_wrapper_get_weather(self, city: str, **kwargs) -> str:
        data = await self.get_weather_data(city)
        if "error" in data:
            return data["error"]
        return (
            f"O tempo em {data['cidade']} é: {data['descricao'].capitalize()}.\n"
            f"- **Temperatura**: {data['temperatura']:.1f}°C\n"
            f"- **Sensação térmica**: {data['sensacao_termica']:.1f}°C\n"
            f"- **Umidade**: {data['umidade']}%"
        )
    
    async def _tool_wrapper_get_weather_for_coords(self, user: Usuario, **kwargs) -> str:
        # Implementação simplificada
        return "Para obter o clima da sua localização atual, por favor, envie-a novamente."

    async def _tool_wrapper_register_location(self, user: Usuario, city: str, **kwargs) -> str:
        details = await self.get_location_details_from_city(city)
        if "error" in details: return json.dumps(details)
        user.cidade, user.estado = details.get('name'), details.get('state', '')
        await self.save_user(user)
        return f"Ok! A sua localização foi atualizada para {details.get('name')}, {details.get('state', '')}."

    async def _tool_wrapper_get_user_location(self, user: Usuario, **kwargs) -> str:
        if user.cidade and user.estado: return f"A sua localização está registada como {user.cidade}, {user.estado}."
        return "Você ainda não tem uma localização registada."
        
    async def _tool_wrapper_complete_onboarding(self, user: Usuario, name: str, city: str, **kwargs) -> str:
        user.nome = name.strip().title()
        details = await self.get_location_details_from_city(city)
        if "error" in details: return f"Não consegui encontrar a cidade '{city}'. Por favor, tente novamente."
        user.cidade, user.estado = details.get('name'), details.get('state', '')
        await self.save_user(user)
        return f"Obrigado, {user.nome}! Registei a sua localização como {user.cidade}. Como posso ajudar agora?"

    # --- Processador Principal de Mensagens ---
    async def process_message(self, user_identifier: str, message_text: str, push_name: str, channel: str, location_data: dict = None) -> str:
        final_response_text = ""
        user = None
        try:
            if not self.openai_client: return "Desculpe, o serviço de inteligência artificial não está configurado."
            user, created = await self.get_or_create_user(user_identifier, push_name, channel)
            
            system_prompt = await self._get_prompt('system_prompt_tools')
            messages = [{"role": "system", "content": system_prompt}]
            
            user_context_info = f"Contexto do usuário: Nome: {user.nome}, Localização cadastrada: {user.cidade or 'Não definida'}, {user.estado or 'Não definido'}."
            messages.append({"role": "system", "content": user_context_info})

            messages.append({"role": "user", "content": message_text})

            response = await self.openai_client.chat.completions.create(model=OPENAI_MODEL, messages=messages, tools=self.tools, tool_choice="auto")
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                tool_call = tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                function_to_call = self.tool_dispatcher.get(function_name)
                if function_to_call:
                    function_response = await function_to_call(user=user, **function_args)
                    final_response_text = function_response
                else:
                    final_response_text = "Desculpe, não consegui processar o seu pedido."
            else:
                final_response_text = response_message.content

            await self.save_user(user)
            return final_response_text.replace("\\n", "\n")
        finally:
            if user:
                await self._log_interaction(user, message_text, final_response_text)

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": { "name": "complete_user_onboarding", "description": "Use esta ferramenta para finalizar o cadastro de um novo usuário APENAS depois de obter o nome completo e a cidade dele.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "O nome completo do usuário."}, "city": {"type": "string", "description": "A cidade de localização do usuário."}}, "required": ["name", "city"]}}},
            {"type": "function", "function": {"name": "get_weather_for_city", "description": "Obtém a previsão do tempo atual para uma cidade específica do Brasil.", "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "O nome da cidade. Ex: 'Jequié'"}},"required": ["city"]}}},
            {"type": "function", "function": {"name": "get_weather_for_current_location", "description": "Obtém o clima para a localização atual do usuário, se ele tiver compartilhado as coordenadas.", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "register_user_location", "description": "Valida e salva uma nova cidade e estado para o usuário. Use quando o usuário pedir para 'mudar', 'alterar' ou 'atualizar' sua localização.", "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "O nome da nova cidade a ser cadastrada."}}, "required": ["city"]}}},
            {"type": "function", "function": {"name": "get_user_registered_location", "description": "Informa ao usuário qual a sua localização (cidade e estado) atualmente cadastrada no sistema.", "parameters": {"type": "object", "properties": {}}}}
        ]