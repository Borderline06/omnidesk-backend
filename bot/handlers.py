from telegram import Update
from telegram.ext import ContextTypes
import sqlite3
import asyncio
from datetime import datetime
from core.sheets_sync import enviar_ticket_a_sheets
from core.db import crear_ticket
from core.ai_service import analizar_incidente_ia, responder_seguimiento_ia, transcribir_audio

sesiones_activas = {}

def verificar_liberacion(user_id):
    """Consulta la base de datos para ver si el técnico ya resolvió el ticket del usuario."""
    try:
        conn = sqlite3.connect("omnidesk.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM liberaciones WHERE user_id = ?", (user_id,))
        liberado = cursor.fetchone() is not None
        if liberado:
            # Si el técnico lo liberó, borramos el registro para que pueda crear otro ticket futuro
            cursor.execute("DELETE FROM liberaciones WHERE user_id = ?", (user_id,))
            conn.commit()
        conn.close()
        return liberado
    except sqlite3.OperationalError:
        return False # La tabla liberaciones aún no existe

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sesiones_activas.pop(str(update.message.from_user.id), None)
    mensaje = "¡Hola! Soy OmniDesk AI.\n\nDescribe tu problema tecnológico con detalle (por texto o por audio) y lo procesaré."
    await update.message.reply_text(mensaje)


async def procesar_incidente(update: Update, context: ContextTypes.DEFAULT_TYPE, texto_usuario: str, user_id: str, username: str):
    """Lógica compartida entre mensajes de texto y audios ya transcritos."""

    # 1. Verificamos si el dashboard cerró el caso
    if user_id in sesiones_activas:
        if verificar_liberacion(user_id):
            # El técnico resolvió el ticket, liberamos al usuario de la memoria temporal
            del sesiones_activas[user_id]
            await update.message.reply_text("✅ Su ticket anterior ha sido cerrado por el equipo técnico. ¿En qué nuevo problema puedo ayudarle?")
            return

        respuesta = await responder_seguimiento_ia(texto_usuario)
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        return

    # 2. Validación Básica
    if len(texto_usuario) < 15:
        await update.message.reply_text("⚠️ Por favor, detalla un poco más tu problema (mínimo 15 caracteres).")
        return

    # 3. Procesamiento IA y Creación del Folio
    categoria, urgencia, instruccion = await analizar_incidente_ia(texto_usuario)
    ticket_id = crear_ticket(user_id, username, texto_usuario, categoria, urgencia)

    # Replicar el ticket en Google Sheets sin bloquear la respuesta al usuario
    asyncio.create_task(enviar_ticket_a_sheets(
        ticket_id, user_id, username, texto_usuario,
        categoria, urgencia, "Abierto",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    sesiones_activas[user_id] = True

    respuesta = (
        f"🛠️ **Asistencia Inmediata:**\n"
        f"{instruccion}\n\n"
        f"✅ **Ticket #{ticket_id} registrado:**\n"
        f"• Categoría: {categoria}\n"
        f"• Urgencia: {urgencia}\n"
        f"• Estado: Abierto\n\n"
        f"Un especialista tomará su caso a la brevedad."
    )
    await update.message.reply_text(respuesta, parse_mode="Markdown")


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "Usuario_Desconocido"
    await procesar_incidente(update, context, texto_usuario, user_id, username)


async def audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe notas de voz o archivos de audio, los transcribe con Gemini
    y sigue el mismo flujo que un mensaje de texto."""
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "Usuario_Desconocido"

    audio_obj = update.message.voice or update.message.audio
    if audio_obj is None:
        return

    aviso = await update.message.reply_text("🎙️ Transcribiendo tu audio, un momento...")

    try:
        archivo = await audio_obj.get_file()
        audio_bytes = bytes(await archivo.download_as_bytearray())
    except Exception:
        await aviso.edit_text("⚠️ No pude descargar el audio. Intenta enviarlo de nuevo.")
        return

    # Las notas de voz de Telegram son OGG/Opus; los archivos de audio pueden traer su propio mime_type
    mime_type = "audio/ogg" if update.message.voice else (audio_obj.mime_type or "audio/mpeg")

    texto_usuario = await transcribir_audio(audio_bytes, mime_type)

    if not texto_usuario:
        await aviso.edit_text("⚠️ No pude transcribir el audio. Intenta de nuevo o escribe tu problema en texto.")
        return

    await aviso.edit_text(f"📝 Transcripción:\n_{texto_usuario}_", parse_mode="Markdown")

    await procesar_incidente(update, context, texto_usuario, user_id, username)