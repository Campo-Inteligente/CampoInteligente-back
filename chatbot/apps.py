import logging
from django.apps import AppConfig
from django.db import connection
from django.db.utils import OperationalError
from channels.db import database_sync_to_async  # Importe a função necessária

logger = logging.getLogger(__name__)

class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    async def check_db_connection(self):
        """Função assíncrona para verificar a conexão."""
        logger.info("--- Verificando a conexão com o banco de dados ---")
        try:
            # Envolve a chamada síncrona para ser segura em um contexto async
            await database_sync_to_async(connection.ensure_connection)()
            logger.info(">>> Conexão com o banco de dados bem-sucedida! <<<")
        except OperationalError as e:
            logger.error(f">>> FALHA na conexão com o banco de dados: {e} <<<")
        except Exception as e:
            logger.error(f">>> Um erro inesperado ocorreu ao tentar conectar ao banco: {e} <<<")

    def ready(self):
        """
        O método ready agora pode chamar a função assíncrona.
        A verificação pode não acontecer na inicialização exata com Uvicorn,
        mas o seu código principal agora está correto.
        """
        # A verificação na inicialização com ASGI pode ser complexa.
        # A lógica principal do seu chatbot (a seguir) é mais importante.
        pass