# chatbot/services.py

import httpx
from openai import AsyncOpenAI
import re
import json
import logging
import asyncio
import subprocess
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
            "search_product_suggestions": self._tool_wrapper_search_product_suggestions,
            "get_product_prices_from_suggestion": self._tool_wrapper_get_product_prices,
        }

    # --- Funções de DB e Auxiliares (sem alterações) ---
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
        
    # --- Funções de APIs Externas (sem alterações) ---
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
        pass

    async def _run_node_script(self, command: List[str]) -> Dict[str, Any]:
        """
        Executa um script Node.js de forma assíncrona e retorna o resultado JSON.
        Usa um método compatível com o event loop do Windows.
        """
        node_service_path = settings.BASE_DIR / 'precodahora_service'

        try:
            logger.info(f"Executando comando síncrono em thread: '{' '.join(command)}' em '{node_service_path}'")
            
            # Usa subprocess.run (síncrono) dentro de uma thread para não bloquear o event loop
            def run_sync():
                return subprocess.run(
                    command,
                    cwd=node_service_path,
                    capture_output=True,
                    text=True,
                    check=True,  # Lança exceção em caso de erro
                    encoding='utf-8'
                )

            # Executa a função síncrona em uma thread separada
            process = await asyncio.to_thread(run_sync)
            
            return json.loads(process.stdout)

        except subprocess.CalledProcessError as e:
            error_output = e.stderr
            logger.error(f"Erro no script Node.js: {error_output}")
            try:
                return json.loads(error_output)
            except json.JSONDecodeError:
                return {"error": "Erro no script de consulta.", "details": error_output}
        except FileNotFoundError:
            logger.error(f"ERRO CRÍTICO: O comando 'node' não foi encontrado. Verifique se o Node.js está instalado e no PATH do sistema.")
            return {"error": "Dependência externa (Node.js) não encontrada no servidor."}
        except Exception as e:
            logger.error(f"Falha ao executar subprocesso Node.js: {e.__class__.__name__}: {e}")
            return {"error": f"Ocorreu um erro crítico no servidor ao tentar executar a consulta."}


    async def search_suggestions(self, item: str) -> Dict[str, Any]:
        command = ['node', 'consultar.js', 'sugestao', item]
        return await self._run_node_script(command)

    async def get_prices(self, gtin: str, latitude: float, longitude: float) -> Dict[str, Any]:
        command = ['node', 'consultar.js', 'produto', str(gtin), str(latitude), str(longitude)]
        return await self._run_node_script(command)

    # --- Wrappers de Ferramentas (sem alterações) ---
    async def _tool_wrapper_get_weather(self, city: str, **kwargs) -> str:
        data = await self.get_weather_data(city)
        if "error" in data: return data["error"]
        return (f"O tempo em {data['cidade']} é: {data['descricao'].capitalize()}.\n- **Temperatura**: {data['temperatura']:.1f}°C\n- **Sensação térmica**: {data['sensacao_termica']:.1f}°C\n- **Umidade**: {data['umidade']}%")
    
    async def _tool_wrapper_get_weather_for_coords(self, user: Usuario, **kwargs) -> str:
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

    async def _tool_wrapper_search_product_suggestions(self, user: Usuario, product_name: str, **kwargs) -> str:
        result = await self.search_suggestions(product_name)
        if result.get("codigo") != 80 or not result.get("resultado"):
            return "Não encontrei nenhum produto com esse nome. Pode tentar descrever de outra forma?"
        
        suggestions = result["resultado"]
        user.contexto['product_suggestions'] = suggestions
        await self.save_user(user)

        response_text = "Encontrei algumas opções. Qual destas você quer consultar?\n\n"
        for i, suggestion in enumerate(suggestions[:5], 1):
            response_text += f"{i}. {suggestion['descricao']}\n"
        
        response_text += "\nResponda com o número do item que você deseja."
        return response_text

    async def _tool_wrapper_get_product_prices(self, user: Usuario, option_number: int, **kwargs) -> str:
        if not user.cidade or not user.estado:
            return "Para buscar os preços, preciso que você cadastre sua cidade primeiro. Qual cidade você mora?"

        suggestions = user.contexto.get('product_suggestions')
        if not suggestions or not (0 < option_number <= len(suggestions)):
            return "Opção inválida. Por favor, primeiro peça para eu pesquisar um produto."
        
        selected_product = suggestions[option_number - 1]
        gtin = selected_product['gtin']
        
        location_details = await self.get_location_details_from_city(user.cidade)
        if 'error' in location_details:
             return "Não consegui obter as coordenadas da sua cidade cadastrada. Por favor, tente cadastrá-la novamente."
        
        latitude, longitude = location_details.get('lat'), location_details.get('lon')

        result = await self.get_prices(gtin, latitude, longitude)

        if result.get("codigo") != 80 or not result.get("resultado"):
            return f"Não encontrei preços recentes para '{selected_product['descricao']}' na sua região."
            
        prices = result["resultado"]
        response_text = f"Aqui estão os preços mais recentes para '{selected_product['descricao']}':\n\n"
        
        for price_info in prices[:3]:
            produto = price_info['produto']
            estabelecimento = price_info['estabelecimento']
            response_text += (
                f"- *Preço*: R$ {produto['precoLiquido']:.2f}\n"
                f"- *Local*: {estabelecimento['nomeEstabelecimento']} ({estabelecimento['bairro']})\n"
                f"- *Registrado*: {produto['intervalo']}\n\n"
            )
        
        # user.contexto['product_suggestions'] = None
        await self.save_user(user)
        
        return response_text

    # --- Processador Principal de Mensagens (sem alterações) ---
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

    # --- Definição das Ferramentas (sem alterações) ---
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": { "name": "complete_user_onboarding", "description": "Use esta ferramenta para finalizar o cadastro de um novo usuário APENAS depois de obter o nome completo e a cidade dele.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "O nome completo do usuário."}, "city": {"type": "string", "description": "A cidade de localização do usuário."}}, "required": ["name", "city"]}}},
            {"type": "function", "function": {"name": "get_weather_for_city", "description": "Obtém a previsão do tempo atual para uma cidade específica do Brasil.", "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "O nome da cidade. Ex: 'Jequié'"}},"required": ["city"]}}},
            {"type": "function", "function": {"name": "get_weather_for_current_location", "description": "Obtém o clima para a localização atual do usuário, se ele tiver compartilhado as coordenadas.", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "register_user_location", "description": "Valida e salva uma nova cidade e estado para o usuário. Use quando o usuário pedir para 'mudar', 'alterar' ou 'atualizar' sua localização.", "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "O nome da nova cidade a ser cadastrada."}}, "required": ["city"]}}},
            {"type": "function", "function": {"name": "get_user_registered_location", "description": "Informa ao usuário qual a sua localização (cidade e estado) atualmente cadastrada no sistema.", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {
                "name": "search_product_suggestions",
                "description": "Busca por produtos com base em um nome ou descrição. Use esta ferramenta quando o usuário perguntar o preço de algo. Retorna uma lista de opções para o usuário escolher.",
                "parameters": {
                    "type": "object",
                    "properties": { "product_name": { "type": "string", "description": "O nome do produto a ser pesquisado. Ex: 'Tomate', 'Leite em pó Ninho'"}},
                    "required": ["product_name"]
                }
            }},
            {"type": "function", "function": {
                "name": "get_product_prices_from_suggestion",
                "description": "Busca os preços de um produto específico que foi previamente selecionado de uma lista de sugestões. Use esta ferramenta quando o usuário responder com um número para escolher um item da lista.",
                "parameters": {
                    "type": "object",
                    "properties": { "option_number": { "type": "integer", "description": "O número da opção que o usuário escolheu da lista de sugestões."}},
                    "required": ["option_number"]
                }
            }},
        ]