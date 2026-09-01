import requests

from telegram import Update
from telegram.ext import ContextTypes


API_URL = "http://127.0.0.1:8000/api/tickets"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start."""

    mensaje_bienvenida = (
        "¡Hola! Soy OmniDesk AI, tu asistente de soporte técnico.\n\n"
        "Por ahora estoy en fase de prototipo, pero pronto podré procesar "
        "tus consultas con Inteligencia Artificial. ¿En qué te puedo ayudar hoy?"
    )

    await update.message.reply_text(mensaje_bienvenida)


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el mensaje de Telegram y crea un ticket en el backend."""

    texto_usuario = update.message.text
    usuario = update.effective_user.username

    if not usuario:
        usuario = update.effective_user.first_name or "Usuario Telegram"

    ticket = {
        "Usuario": usuario,
        "Mensaje": texto_usuario,
        "Estado": "Abierto",
        "Nivel_Gravedad": "Media"
    }

    try:
        respuesta = requests.post(
            API_URL,
            json=ticket,
            timeout=5
        )

        respuesta.raise_for_status()

        datos = respuesta.json()
        ticket_creado = datos["ticket"]

        await update.message.reply_text(
            f"Ticket #{ticket_creado['ID']} creado correctamente.\n\n"
            f"Problema: {texto_usuario}\n"
            f"Estado: {ticket_creado['Estado']}\n"
            f"Gravedad: {ticket_creado['Nivel_Gravedad']}"
        )

    except requests.RequestException:
        await update.message.reply_text(
            "No pude registrar tu consulta en el sistema. "
            "Verifica que el backend esté funcionando."
        )
