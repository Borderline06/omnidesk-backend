import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.config import TELEGRAM_TOKEN
from bot.handlers import start_command, echo_message

# Configurar log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Inicializa y ejecuta el bot."""
    logger.info("Arrancando el motor de OmniDesk AI...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    
    logger.info("Bot en línea y escuchando. Presiona Ctrl+C para detener.")
    app.run_polling()

if __name__ == "__main__":
    main()