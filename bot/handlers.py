from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start."""
    mensaje_bienvenida = (
        "¡Hola! Soy OmniDesk AI, tu asistente de soporte técnico.\n\n"
        "Por ahora estoy en fase de prototipo, pero pronto podré procesar "
        "tus consultas con Inteligencia Artificial. ¿En qué te puedo ayudar hoy?"
    )
    await update.message.reply_text(mensaje_bienvenida)

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hace un eco del mensaje recibido para probar la conexión."""
    texto_usuario = update.message.text
    respuesta = f"Sistema (Prototipo) recibió tu mensaje: '{texto_usuario}'"
    await update.message.reply_text(respuesta)