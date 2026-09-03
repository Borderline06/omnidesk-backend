import logging
from telegram.ext import ( Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters)
from bot.config import TELEGRAM_TOKEN
from bot.handlers import start_command, echo_message, button_click_handler

# Configuración de logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# 1. Instanciamos el bot de Telegram
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# 2. Registramos los handlers en orden
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CallbackQueryHandler(button_click_handler))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))

def main():
    """Permite ejecutar el bot de forma independiente si se arranca este archivo directo."""
    logger.info("Arrancando el motor de OmniDesk AI...")
    logger.info("Bot en línea y escuchando. Presiona Ctrl+C para detener.")
    telegram_app.run_polling()

if __name__ == "__main__":
    main()