# chatbot/services.py

import httpx
from openai import AsyncOpenAI
import re
import json
import logging
import asyncio
import subprocess
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pytz

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
            "get_product_prices_for_location": self._tool_wrapper_get_product_prices,
        }

    # --- Funções de DB e Auxiliares ---
    @database_sync_to_async
    def _get_prompt(self, key: str) -> str:
        try: return Prompt.objects.get(key=key).text
        except Prompt.DoesNotExist: return f"Prompt '{key}' não configurado."
    
    @database_sync_to_async
    def get_or_create_user(self, user_identifier: str, push_name: str, channel: str) -> Tuple[Usuario, bool]:
        user, created = Usuario.objects.get_or_create(
            whatsapp_id=user_identifier,
            defaults={'nome': 'Visitante', 'organizacao_id': 1}
        )
        if not isinstance(user.contexto, dict): user.contexto = {}
        return user, created

    @database_sync_to_async
    def save_user(self, user: Usuario): user.save()
    
    @database_sync_to_async
    def _log_interaction(self, user: Usuario, user_message: str, bot_response: str):
        if not bot_response: return
        Interacao.objects.create(agricultor=user, mensagem_usuario=user_message, resposta_chatbot=bot_response)
    
    @database_sync_to_async
    def _get_recent_interactions(self, user: Usuario, limit: int = 6) -> List[Dict[str, str]]:
        history = []
        interactions = Interacao.objects.filter(agricultor=user).order_by('-timestamp')[:limit][::-1]
        for interacao in interactions:
            if interacao.mensagem_usuario:
                history.append({"role": "user", "content": interacao.mensagem_usuario})
            if interacao.resposta_chatbot:
                history.append({"role": "assistant", "content": interacao.resposta_chatbot})
        return history

    # --- Funções de APIs Externas ---
    async def send_whatsapp_message(self, user_id: str, text: str):
        if not all([settings.EVOLUTION_API_URL, settings.EVOLUTION_INSTANCE_NAME, settings.EVOLUTION_API_KEY]):
            logger.error("As variáveis de ambiente da Evolution API não estão configuradas.")
            return

        is_group = "@g.us" in user_id
        recipient_number = user_id if is_group else user_id.split('@')[0]

        url = f"{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE_NAME}"
        headers = {"apikey": settings.EVOLUTION_API_KEY}
        
        payload = {
            "number": recipient_number,
            "options": {"delay": 1200},
            "textMessage": {"text": text}
        }
        
        if is_group:
            payload['options']['isGroup'] = True

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                if response.status_code in [200, 201]:
                    logger.info(f"Mensagem enviada com sucesso para {recipient_number}.")
                else:
                    logger.error(f"Falha ao enviar mensagem para {recipient_number}. Status: {response.status_code}, Resposta: {response.text}")
            except httpx.RequestError as e:
                logger.error(f"Erro de requisição ao enviar mensagem para {recipient_number}: {e}")

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

    async def get_city_from_coords(self, lat: float, lon: float) -> dict:
        url = "http://api.openweathermap.org/geo/1.0/reverse"
        params = {"lat": lat, "lon": lon, "limit": 1, "appid": settings.OPENWEATHER_API_KEY}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200 and response.json():
                    data = response.json()[0]
                    return {"cidade": data.get('name'), "estado": data.get('state', '')}
            except Exception: pass
        return {"error": "Não foi possível identificar a cidade a partir das coordenadas."}

    # --- Lógica da API Preço da Hora ---
    async def _run_node_script(self, command: List[str]) -> Dict[str, Any]:
        node_service_path = settings.BASE_DIR / 'precodahora_service'
        try:
            def run_sync():
                return subprocess.run(command, cwd=node_service_path, capture_output=True, text=True, check=True, encoding='utf-8')
            process = await asyncio.to_thread(run_sync)
            return json.loads(process.stdout)
        except subprocess.CalledProcessError as e:
            error_output = e.stderr
            logger.error(f"Erro no script Node.js: {error_output}")
            try: return json.loads(error_output)
            except json.JSONDecodeError: return {"error": "Erro no script de consulta.", "details": error_output}
        except Exception as e:
            logger.error(f"Falha ao executar subprocesso Node.js: {e.__class__.__name__}: {e}")
            return {"error": "Ocorreu um erro crítico no servidor."}

    async def search_suggestions(self, item: str) -> Dict[str, Any]:
        command = ['node', 'consultar.js', 'sugestao', item]
        return await self._run_node_script(command)

    async def get_prices(self, gtin: str, latitude: float, longitude: float) -> Dict[str, Any]:
        command = ['node', 'consultar.js', 'produto', str(gtin), str(latitude), str(longitude)]
        return await self._run_node_script(command)

    # --- Wrappers de Ferramentas ---
    async def _tool_wrapper_get_weather(self, user: Usuario, city: str, channel: str, **kwargs) -> str:
        data = await self.get_weather_data(city)
        if "error" in data:
            return data["error"]

        sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
        now = datetime.now(sao_paulo_tz)
        formatted_datetime = now.strftime("%d/%m/%Y às %H:%M")

        return (
            f"Clima em {data['cidade']} ({formatted_datetime}):\n\n"
            f"- *Condição*: {data['descricao'].capitalize()}\n"
            f"- *Temperatura*: {data['temperatura']:.1f}°C\n"
            f"- *Sensação térmica*: {data['sensacao_termica']:.1f}°C\n"
            f"- *Umidade*: {data['umidade']}%"
        )

    async def _tool_wrapper_register_location(self, user: Usuario, city: str, channel: str, **kwargs) -> str:
        details = await self.get_location_details_from_city(city)
        if "error" in details:
            return f"Não consegui encontrar detalhes para a cidade '{city}'."

        cidade = details.get('name')
        estado_completo = details.get('state', '')
        estado_abreviado = estado_completo[:2] if estado_completo else ''

        user.cidade = cidade
        user.estado = estado_abreviado
        
        await self.save_user(user)
        
        return f"Ok! A sua localização foi atualizada para {cidade}, {estado_completo}."

    async def _tool_wrapper_get_user_location(self, user: Usuario, channel: str, **kwargs) -> str:
        if user.cidade and user.estado: return f"A sua localização está registada como {user.cidade}, {user.estado}."
        
        base_message = "Você ainda não tem uma localização registada."
        if channel == 'whatsapp':
            base_message += "\n\nVocê pode me dizer a sua cidade ou usar o botão de anexo para enviar a sua localização atual."
        return base_message
        
    async def _tool_wrapper_complete_onboarding(self, user: Usuario, name: str, city: str, channel: str, **kwargs) -> str:
        user.nome = name.strip().title()
        details = await self.get_location_details_from_city(city)
        if "error" in details: 
            return f"Não consegui encontrar a cidade '{city}'. Por favor, tente novamente."

        cidade = details.get('name')
        estado_completo = details.get('state', '')
        estado_abreviado = estado_completo[:2] if estado_completo else ''

        user.cidade = cidade
        user.estado = estado_abreviado
        
        await self.save_user(user)
        
        return f"Obrigado, {user.nome}! Registei a sua localização como {cidade}, {estado_completo}. Como posso ajudar agora?"

    async def _tool_wrapper_get_product_prices(self, user: Usuario, product_name: str, city: str = None, channel: str = 'web', **kwargs) -> str:
        target_city = city or user.cidade
        
        if not target_city:
            base_message = "Para qual cidade na Bahia você gostaria de consultar o preço?"
            if channel == 'whatsapp':
                base_message += "\n\nDica: Você também pode usar o botão de anexo para enviar sua localização atual."
            return base_message

        # --- LÓGICA DE VALIDAÇÃO MELHORADA ---
        location_details = await self.get_location_details_from_city(target_city)
        
        # Caso 1: A API não encontrou a cidade de todo
        if 'error' in location_details:
             return f"Desculpe, não consegui encontrar a cidade '{target_city}'. Por favor, verifique se o nome está correto e tente novamente."

        # Caso 2: A cidade foi encontrada, mas não é na Bahia
        returned_state = location_details.get('state', 'Desconhecido')
        if returned_state.lower() != 'bahia':
            return f"Encontrei '{target_city}' no estado de {returned_state}, mas a consulta de preços só está disponível para cidades da Bahia."

        # Se passou nas validações, continua
        latitude, longitude = location_details.get('lat'), location_details.get('lon')

        suggestions_result = await self.search_suggestions(product_name)
        if suggestions_result.get("codigo") != 80 or not suggestions_result.get("resultado"):
            return f"Não encontrei nenhum produto correspondente a '{product_name}'."

        for suggestion in suggestions_result["resultado"][:3]:
            gtin = suggestion.get('gtin')
            if not gtin:
                continue

            prices_result = await self.get_prices(gtin, latitude, longitude)
            
            if prices_result.get("codigo") == 80 and prices_result.get("resultado"):
                prices = prices_result["resultado"]
                response_text = f"Aqui estão os preços mais recentes para '{suggestion['descricao']}' em {target_city}:\n\n"
                
                for price_info in prices[:3]:
                    produto = price_info['produto']
                    estabelecimento = price_info['estabelecimento']
                    response_text += (f"- *Preço*: R$ {produto['precoLiquido']:.2f}\n- *Local*: {estabelecimento['nomeEstabelecimento']} ({estabelecimento['bairro']})\n- *Registrado*: {produto['intervalo']}\n\n")
                
                return response_text

        return f"Não encontrei preços recentes para '{product_name}' em {target_city}."

    # --- Processador Principal de Mensagens ---
    async def process_message(self, user_identifier: str, message_text: str, push_name: str, channel: str, location_data: dict = None) -> str:
        MAX_MESSAGE_LENGTH = 500
        if len(message_text) > MAX_MESSAGE_LENGTH:
            final_response_text = f"Desculpe, sua mensagem é muito longa. Por favor, tente enviar uma mensagem com menos de {MAX_MESSAGE_LENGTH} caracteres."
        else:
            final_response_text = ""
            user = None
            try:
                if not self.openai_client: return "Desculpe, o serviço de inteligência artificial não está configurado."
                user, created = await self.get_or_create_user(user_identifier, push_name, channel)
                
                if location_data and 'latitude' in location_data and 'longitude' in location_data:
                    lat, lon = location_data['latitude'], location_data['longitude']
                    location_info = await self.get_city_from_coords(lat, lon)
                    if 'error' in location_info:
                        final_response_text = location_info['error']
                    else:
                        user.latitude, user.longitude = lat, lon
                        user.cidade = location_info.get('cidade')
                        estado_completo = location_info.get('estado', '')
                        user.estado = estado_completo[:2] if estado_completo else ''
                        await self.save_user(user)
                        final_response_text = f"Obrigado! A sua localização foi atualizada para {user.cidade}, {estado_completo}."
                    
                    await self._log_interaction(user, "[Localização enviada]", final_response_text)
                    
                    if channel == 'whatsapp':
                        await self.send_whatsapp_message(user_identifier, final_response_text)
                        return None
                    return final_response_text

                system_prompt = await self._get_prompt('system_prompt_tools')
                messages = [{"role": "system", "content": system_prompt}]
                
                user_context_info = f"Contexto do usuário: Nome: {user.nome}, Localização cadastrada: {user.cidade or 'Não definida'}, {user.estado or 'Não definido'}."
                messages.append({"role": "system", "content": user_context_info})

                recent_history = await self._get_recent_interactions(user)
                messages.extend(recent_history)
                
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
                        function_response = await function_to_call(user=user, channel=channel, **function_args)
                        final_response_text = function_response
                    else:
                        final_response_text = "Desculpe, não consegui processar o seu pedido."
                else:
                    final_response_text = response_message.content

            except Exception as e:
                logger.error(f"Erro inesperado no process_message: {e}")
                final_response_text = "Desculpe, ocorreu um erro inesperado. Tente novamente."
            finally:
                if user:
                    await self._log_interaction(user, message_text, final_response_text)

        # --- LÓGICA DE ENVIO PARA WHATSAPP ---
        if channel == 'whatsapp':
            await self.send_whatsapp_message(user_identifier, final_response_text)
            return None # Retorna None porque a mensagem já foi enviada
        
        # Retorna para o webchat
        return final_response_text.replace("\\n", "\n")

    # --- Definição das Ferramentas ---
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": { "name": "complete_user_onboarding", "description": "Use esta ferramenta para finalizar o cadastro de um novo usuário APENAS depois de obter o nome completo e a cidade dele.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "city": {"type": "string"}}, "required": ["name", "city"]}}},
            {"type": "function", "function": {"name": "get_weather_for_city", "description": "Obtém a previsão do tempo atual para uma cidade específica do Brasil.", "parameters": {"type": "object", "properties": {"city": {"type": "string"}},"required": ["city"]}}},
            {"type": "function", "function": {"name": "register_user_location", "description": "Valida e salva uma nova cidade e estado para o usuário.", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}},
            {"type": "function", "function": {"name": "get_user_registered_location", "description": "Informa ao usuário qual a sua localização cadastrada.", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {
                "name": "get_product_prices_for_location",
                "description": "Busca o preço de um produto numa cidade específica da Bahia. Use esta ferramenta quando o usuário perguntar o preço de algo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "O nome do produto a ser pesquisado. Ex: 'Tomate', 'Leite em pó Ninho'"
                        },
                        "city": {
                            "type": "string",
                            "description": "O nome da cidade para a consulta. Este campo é opcional se o usuário já tiver uma cidade cadastrada."
                        }
                    },
                    "required": ["product_name"]
                }
            }},
        ]
