# chatbot/services.py

import httpx
import openai
import re
import logging 
from datetime import timedelta
from django.utils import timezone
from typing import List, Dict

from django.conf import settings
from .models import Usuario, Prompt, State, Interacao
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.openai_client = None
        
        self.state_map_by_name: Dict[str, str] = {}
        self.state_map_by_abbr: List[str] = []

    async def _load_state_maps_if_needed(self):
        if not self.state_map_by_name:
            states = await self._get_all_states()
            self.state_map_by_name = {state.name: state.abbreviation for state in states}
            self.state_map_by_abbr = [state.abbreviation for state in states]

    @database_sync_to_async
    def _get_all_states(self) -> List[State]:
        return list(State.objects.all())

    async def _parse_city_from_input(self, text: str) -> str:
        await self._load_state_maps_if_needed()
        cleaned_text = re.split(r'[-/]', text)[0]
        words = cleaned_text.strip().split()
        if len(words) > 1 and words[-1].upper() in self.state_map_by_abbr:
            return " ".join(words[:-1]).strip()
        return cleaned_text.strip()

    @database_sync_to_async
    def _get_prompt(self, key: str) -> str:
        try:
            return Prompt.objects.get(key=key).text
        except Prompt.DoesNotExist:
            logger.warning(f"AVISO: Prompt com a chave '{key}' não encontrado no banco de dados.")
            return f"Prompt '{key}' não configurado."

    async def send_whatsapp_message(self, phone_number: str, text: str):
        logger.info(f"Tentando enviar mensagem para {phone_number} via Evolution API.")
        
        corrected_text = text.replace('\\n', '\n')
        
        url = f"{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE_NAME}"
        headers = {"apikey": settings.EVOLUTION_API_KEY}
        payload = {"number": phone_number, "textMessage": {"text": corrected_text}}
        
        logger.debug(f"URL da API: {url}")
        logger.debug(f"Payload de envio: {payload}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                logger.info(f"Mensagem enviada para {phone_number}. Status da API: {response.status_code}")
                logger.debug(f"Resposta da API: {response.text}")
        except Exception as e:
            logger.error(f"ERRO DE API: Falha ao enviar mensagem para {phone_number}. Erro: {e}")

    async def get_weather_data(self, city: str) -> dict:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": f"{city},BR", "appid": settings.OPENWEATHER_API_KEY, "units": "metric", "lang": "pt_br"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json() if response.status_code == 200 else {"error": f"Cidade '{city}' não encontrada."}

    async def get_location_details_from_coords(self, lat: float, lon: float) -> dict:
        await self._load_state_maps_if_needed()
        url = "http://api.openweathermap.org/geo/1.0/reverse"
        params = {"lat": lat, "lon": lon, "limit": 1, "appid": settings.OPENWEATHER_API_KEY}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200 and response.json():
                location = response.json()[0]
                state_abbr = self.state_map_by_name.get(location.get("state"), "")
                return {"city": location.get("name"), "state": state_abbr}
            return {}

    async def get_location_details_from_city(self, city: str) -> dict:
        await self._load_state_maps_if_needed()
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {"q": f"{city},BR", "limit": 1, "appid": settings.OPENWEATHER_API_KEY}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200 and response.json():
                location = response.json()[0]
                state_abbr = self.state_map_by_name.get(location.get("state"), "")
                return {"city": location.get("name"), "state": state_abbr, "lat": location.get("lat"), "lon": location.get("lon")}
            return {}

    @database_sync_to_async
    def get_or_create_user(self, user_identifier: str, push_name: str, channel: str):
        # AQUI ESTÁ A CORREÇÃO: A função agora retorna a tupla (user, created)
        return Usuario.objects.get_or_create(
            whatsapp_id=user_identifier,
            defaults={'nome': push_name if channel == 'whatsapp' else 'Visitante', 'organizacao_id': 1, 'contexto': {}}
        )

    @database_sync_to_async
    def save_user(self, user: Usuario):
        user.save()

    def _reset_all_flow_flags(self, context: dict) -> dict:
        keys_to_remove = [key for key in context if key.startswith('awaiting_')]
        for key in keys_to_remove:
            context.pop(key, None)
        return context

    async def _format_weather_response(self, cidade: str) -> str:
        cidade_limpa = await self._parse_city_from_input(cidade)
        clima_atual = await self.get_weather_data(cidade_limpa)

        if "error" in clima_atual or clima_atual.get("cod") != 200:
            prompt_template = await self._get_prompt('weather_city_not_found')
            return prompt_template.format(cidade=cidade_limpa)
        
        prompt_template = await self._get_prompt('weather_dynamic_response')
        return prompt_template.format(
            cidade=clima_atual.get('name', cidade_limpa),
            descricao=clima_atual['weather'][0]['description'].capitalize(),
            temperatura=f"{clima_atual['main']['temp']:.1f}",
            sensacao=f"{clima_atual['main']['feels_like']:.1f}",
            umidade=clima_atual['main']['humidity']
        )
        
    @database_sync_to_async
    def _get_last_interaction_time(self, user: Usuario):
        """Busca o timestamp da última interação do usuário."""
        last_interaction = Interacao.objects.filter(agricultor=user).order_by('-timestamp').first()
        return last_interaction.timestamp if last_interaction else None

    @database_sync_to_async
    def _log_interaction(self, user: Usuario, user_message: str, bot_response: str):
        """Salva a interação atual na base de dados."""
        # Não salva interações se o bot não deu resposta (ex: erro interno)
        if not bot_response:  
            return
        Interacao.objects.create(
            agricultor=user,
            mensagem_usuario=user_message,
            resposta_chatbot=bot_response
        )

    async def process_message(self, user_identifier: str, message_text: str, push_name: str, channel: str, location_data: dict = None) -> str:
        # 1. Variáveis iniciais
        final_response_text = ""
        user = None 
        
        try:
            # 2. Setup inicial: carrega mapas e obtém o usuário
            await self._load_state_maps_if_needed()
            user, created = await self.get_or_create_user(user_identifier, push_name, channel)
            context = user.contexto or {}
            message_lower = message_text.lower().strip()
            
            now = timezone.now()
            last_interaction_time = await self._get_last_interaction_time(user)

            # 3. Lógica de "Início de Sessão" (Saudação de boas-vindas)
            show_welcome_message = False
            if created or not last_interaction_time or (now - last_interaction_time > timedelta(hours=1)) or (last_interaction_time and now.date() != last_interaction_time.date()):
                show_welcome_message = True

            if show_welcome_message and user.nome:
                welcome_template = await self._get_prompt('welcome_first_interaction')
                menu_text = await self._get_prompt('main_menu_v2')
                final_response_text = welcome_template.format(user_nome=user.nome.split(' ')[0])
                user.contexto = self._reset_all_flow_flags(context)
                final_response_text = f"{final_response_text}\n\n{menu_text}"
                # Este é o único 'return' antecipado, para uma nova sessão limpa.
                return final_response_text 

            # 4. Processamento principal da conversa (Máquina de Estados)
            current_state = next((state for state in context if state.startswith('awaiting_')), None)

            # Comando de Reinício
             # 1. Trata o comando de reinício primeiro
            if message_lower in ['reiniciar', 'recomeçar', 'inicio']:
                user.nome = ""
                user.contexto = {'awaiting_initial_name': True}
                final_response_text = await self._get_prompt('welcome_ask_name')

            # 2. Se o utilizador é NOVO (acabou de ser criado), inicia o onboarding
            elif created or (not user.nome and not current_state):
                user.contexto = {'awaiting_initial_name': True}
                final_response_text = await self._get_prompt('welcome_ask_name')

            # 3. Se o bot está AGUARDANDO o nome, processa a resposta
            elif current_state == 'awaiting_initial_name':
                user.nome = message_text.strip().title()
                context.pop('awaiting_initial_name', None)
                context['awaiting_location'] = True
                prompt_key = 'welcome_ask_location_whatsapp' if channel == 'whatsapp' else 'welcome_ask_location_web'
                template = await self._get_prompt(prompt_key)
                final_response_text = template.format(user_nome=user.nome)
            
            # Estado: Aguardando localização
            elif current_state == 'awaiting_location':
                context.pop('awaiting_location', None)
                location_processed = False
                thank_you_message = ""
                
                if channel == 'whatsapp' and location_data:
                    details = await self.get_location_details_from_coords(location_data['latitude'], location_data['longitude'])
                    if details:
                        user.cidade, user.estado = details.get('city'), details.get('state')
                        template = await self._get_prompt('location_received_whatsapp')
                        thank_you_message = template.format(user_nome=user.nome)
                        location_processed = True
                elif message_text:
                    details = await self.get_location_details_from_city(await self._parse_city_from_input(message_text))
                    if details:
                        user.cidade, user.estado = details.get('city'), details.get('state')
                        template = await self._get_prompt('location_received_web')
                        thank_you_message = template.format(cidade=user.cidade, user_nome=user.nome)
                        location_processed = True
                    else:
                        final_response_text = (await self._get_prompt('location_not_found_web')).format(cidade=message_text)
                
                if location_processed:
                    main_menu_text = await self._get_prompt('main_menu_v2')
                    final_response_text = f"{thank_you_message}\n\n{main_menu_text}"
                elif not final_response_text:
                    final_response_text = await self._get_prompt('location_error')
            
            # Estado: Aguardando escolha no submenu de clima
            elif current_state == 'awaiting_weather_location_choice':
                context.pop('awaiting_weather_location_choice', None)
                if any(s in message_lower for s in ["1", "minha", "atual"]):
                    if user.cidade:
                        final_response_text = await self._format_weather_response(user.cidade)
                        context['awaiting_weather_followup'] = True
                    else:
                        context['awaiting_location'] = True
                        final_response_text = await self._get_prompt('weather_location_not_found')
                elif any(s in message_lower for s in ["2", "outra"]):
                    context['awaiting_weather_location'] = True
                    final_response_text = await self._get_prompt('weather_ask_another_city')
                else:
                    context['awaiting_weather_location_choice'] = True
                    final_response_text = await self._get_prompt('weather_choice_invalid')

            # Estado: Aguardando nome da cidade para o clima
            elif current_state == 'awaiting_weather_location':
                cidade_limpa = await self._parse_city_from_input(message_text)
                clima_atual = await self.get_weather_data(cidade_limpa)
                if "error" in clima_atual or clima_atual.get("cod") != 200:
                    prompt_template = await self._get_prompt('weather_city_not_found')
                    final_response_text = prompt_template.format(cidade=cidade_limpa)
                    context['awaiting_weather_location'] = True
                else:
                    prompt_template = await self._get_prompt('weather_dynamic_response')
                    final_response_text = prompt_template.format(
                        cidade=clima_atual.get('name', cidade_limpa),
                        descricao=clima_atual['weather'][0]['description'].capitalize(),
                        temperatura=f"{clima_atual['main']['temp']:.1f}",
                        sensacao=f"{clima_atual['main']['feels_like']:.1f}",
                        umidade=clima_atual['main']['humidity']
                    )
                    context.pop('awaiting_weather_location', None)
                    context['awaiting_weather_followup'] = True

            # Estado: Aguardando resposta de acompanhamento do clima
            elif current_state == 'awaiting_weather_followup':
                context.pop('awaiting_weather_followup', None)
                if any(s in message_lower for s in ["sim", "outra", "cidade"]):
                    context['awaiting_weather_location'] = True
                    final_response_text = await self._get_prompt('weather_ask_another_city')
                else:
                    final_response_text = await self._get_prompt('main_menu_v2')

            # Roteamento de Menu e Fallback final
            else:
                if any(s in message_lower for s in ["[1]", "1", "clima"]):
                    context['awaiting_weather_location_choice'] = True
                    final_response_text = await self._get_prompt('weather_submenu_choice')
                elif any(s in message_lower for s in ["[2]", "2", "plantio"]):
                    final_response_text = await self._get_prompt('feature_planting_wip')
                elif any(s in message_lower for s in ["[3]", "3", "preços"]):
                    final_response_text = await self._get_prompt('feature_prices_wip')
                elif any(s in message_lower for s in ["[4]", "4", "relatórios"]):
                    final_response_text = await self._get_prompt('feature_reports_wip')
                elif any(s in message_lower for s in ["[5]", "5", "safra"]):
                    final_response_text = await self._get_prompt('feature_harvest_wip')
                else:
                    fallback_template = await self._get_prompt('default_fallback')
                    menu_text = await self._get_prompt('main_menu_v2')
                    final_response_text = f"{fallback_template.format(user_nome=user.nome.split(' ')[0])}\n\n{menu_text}"
            
            # 5. Salva o estado do usuário antes de sair do 'try'
            user.contexto = context
            await self.save_user(user)
            
            # 6. Ponto de saída único
            return final_response_text

        finally:
            # 7. Bloco de Segurança: Salva a Interação no Final
            # Este código é executado sempre, garantindo que a conversa seja salva.
            if user:
                await self._log_interaction(user, message_text, final_response_text)
