from telegram import Update
from telegram.ext import ContextTypes
import sqlite3
from core.db import crear_ticket
from core.ai_service import analizar_incidente_ia, responder_seguimiento_ia

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
    mensaje = "¡Hola! Soy OmniDesk AI.\n\nDescribe tu problema tecnológico con detalle y lo procesaré."
    await update.message.reply_text(mensaje)

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "Usuario_Desconocido"
    
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