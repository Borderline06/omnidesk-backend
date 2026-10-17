import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import procesar_audio_telegram

from bot.config import TELEGRAM_TOKEN
from bot.handlers import start_command, historial_command, echo_message
from core.db import init_db
from core.mqtt_config import MQTT_ENABLED, MQTT_HOST, MQTT_PORT, MQTT_TOPIC
from core.mqtt_subscriber import iniciar_suscriptor

# Configurar logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def main():
    """Inicializa y ejecuta el bot."""
    # 1. Crear la base de datos local
    init_db()
    logger.info("Base de datos SQLite lista y conectada.")

    # Suscriptor MQTT (hilo propio de paho): guarda la temperatura IoT en iot_metrics
    if MQTT_ENABLED:
        iniciar_suscriptor()
        logger.info(f"Suscriptor MQTT iniciado hacia {MQTT_HOST}:{MQTT_PORT} (tópico {MQTT_TOPIC}).")

    # 2. Forzar el bucle de eventos
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    logger.info("Arrancando el motor de OmniDesk AI...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 3. Registrar los manejadores
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler(["historial", "mis_tickets"], historial_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))

    app.add_handler(MessageHandler(filters.VOICE, procesar_audio_telegram))
    
    logger.info("Bot en línea y escuchando. Presiona Ctrl+C para detener.")
    app.run_polling()

if __name__ == "__main__":
    main()
