from telegram import ReplyKeyboardRemove, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes
import csv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from core.db import (
    crear_ticket, obtener_ticket_activo, guardar_mensaje,
    actualizar_estado_ticket, actualizar_nombre_tickets_activos,
    actualizar_detalles_ticket, confirmar_inicio_bot, usuario_requiere_start,
    obtener_historial_tickets,
)
from core.ai_service import (
    analizar_incidente_ia, responder_seguimiento_ia,
    requiere_intervencion_tecnica, usuario_pide_tecnico, es_nuevo_incidente,
    detectar_emergencia, generar_contenido_ia,
)

MENSAJE_REQUIERE_START = (
    "✅ Tu ticket anterior ya está cerrado. Para iniciar una nueva consulta, "
    "envía /start y después descríbeme tu problema."
)

async def responder_ticket_inicial(update, ticket_id, categoria, urgencia, instruccion, escalado):
    encabezado = "🚨 **URGENCIA ALTA**\n\n" if urgencia == "Alta" else ""
    respuesta = (
        f"{encabezado}🛠️ **Asistencia inmediata:**\n{instruccion}\n\n"
        f"✅ **Ticket #{ticket_id} registrado:**\n"
        f"• Categoría: {categoria}\n"
        f"• Urgencia: {urgencia}\n"
    )

    if escalado:
        respuesta += (
            "• Estado: Esperando técnico\n\n"
            "Por la urgencia o el tipo de problema, el caso se pasó a un técnico. "
            "Te responderá por este chat."
        )
    else:
        respuesta += (
            "• Estado: Esperando tu elección\n\n"
            "¿Cómo quieres continuar?\n"
            "1. Seguir hablando conmigo. Cuéntame detalladamente qué pasa para buscar una solución.\n"
            "2. Hablar con un técnico.\n\n"
            "Responde 1 o 2."
        )

    guardar_mensaje(ticket_id, 'bot', respuesta)
    try:
        await update.message.reply_text(respuesta, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    except BadRequest:
        # La instrucción de la IA puede traer símbolos que rompen el Markdown de Telegram
        await update.message.reply_text(respuesta.replace("**", ""), reply_markup=ReplyKeyboardRemove())

def notificar_si_urgente(ticket_id, categoria, urgencia, texto):
    """Registra en CSV y envía el correo cuando el ticket es de urgencia Alta."""
    automatizar_registro_csv(ticket_id, categoria, urgencia, texto)
    if urgencia == "Alta":
        enviar_email_urgente(ticket_id, urgencia, texto)

# --- AUTOMATIZACIÓN 1: REPORTE CSV ---
def automatizar_registro_csv(ticket_id, categoria, urgencia, texto):
    archivo = "reporte_automatizado.csv"
    es_nuevo = not os.path.exists(archivo)
    with open(archivo, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if es_nuevo:
            writer.writerow(["Fecha", "ID Ticket", "Categoría", "Urgencia", "Problema"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ticket_id, categoria, urgencia, texto])

# --- AUTOMATIZACIÓN 2: ALERTA EMAIL REAL ---
def enviar_email_urgente(ticket_id, urgencia, texto):
    remitente = os.getenv("EMAIL_REMITENTE")
    password = os.getenv("EMAIL_PASSWORD")
    destinatario = remitente # Te lo envías a ti mismo para la demostración
    
    if not remitente or not password:
        print("Faltan credenciales de correo en el archivo .env")
        return

    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = f"🚨 URGENTE: Nuevo Ticket Crítico [ID: {ticket_id}]"

    cuerpo = f"""Se ha reportado una incidencia en OmniDesk AI.
    
Detalles del reporte:
- Nivel de Urgencia: {urgencia}
- Descripción del usuario: {texto}

Por favor, ingresar al dashboard para gestionar la solución."""
    
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remitente, password)
        servidor.send_message(mensaje)
        servidor.quit()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error enviando correo: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    confirmar_inicio_bot(user.id)
    nombre = f"@{user.username}" if user.username else (user.full_name or str(user.id))
    actualizar_nombre_tickets_activos(user.id, nombre)
    mensaje = (
        "¡Hola! Soy OmniDesk AI. Cuéntame qué problema tecnológico tienes y te ayudaré a resolverlo. "
        "Si quieres consultar tus tickets anteriores, escribe /historial."
    )
    await update.message.reply_text(mensaje)

async def historial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía al usuario su historial, buscando por su ID único de Telegram."""
    user_id = update.effective_user.id
    tickets = obtener_historial_tickets(user_id)

    if not tickets:
        await update.effective_message.reply_text(
            "Todavía no tienes tickets registrados. Envíame /start para iniciar una consulta."
        )
        return

    lineas = ["📋 Tus últimos tickets:"]
    for ticket_id, descripcion, categoria, urgencia, estado, fecha in tickets:
        descripcion_corta = " ".join((descripcion or "Sin descripción").split())
        if len(descripcion_corta) > 160:
            descripcion_corta = descripcion_corta[:157].rstrip() + "..."
        lineas.append(
            f"\n🎫 Ticket #{ticket_id} · {estado}\n"
            f"📅 {fecha}\n"
            f"🗂️ {categoria or 'Sin categoría'} · {urgencia or 'Sin urgencia'}\n"
            f"📝 {descripcion_corta}"
        )

    lineas.append("\nPara iniciar una consulta nueva, envía /start.")
    await update.effective_message.reply_text("\n".join(lineas))

async def _atender_emergencia(update, ticket_id, texto):
    """Mensaje de peligro con un ticket ya abierto: instrucción de seguridad inmediata y aviso por correo."""
    _, urgencia, instruccion = await analizar_incidente_ia(texto)
    actualizar_estado_ticket(ticket_id, 'Esperando técnico')
    enviar_email_urgente(ticket_id, urgencia, texto)
    respuesta = (
        f"🚨 URGENCIA ALTA\n{instruccion}\n\n"
        f"Escalé el ticket #{ticket_id} a un técnico, que continuará contigo por este chat."
    )
    guardar_mensaje(ticket_id, 'bot', respuesta)
    await update.message.reply_text(respuesta, reply_markup=ReplyKeyboardRemove())

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _procesar_texto(update, update.message.text)

async def _procesar_texto(update: Update, texto_usuario: str):
    user_id = str(update.message.from_user.id)
    telegram_user = update.message.from_user
    username = f"@{telegram_user.username}" if telegram_user.username else (telegram_user.full_name or str(user_id))
    actualizar_nombre_tickets_activos(user_id, username)

    if usuario_requiere_start(user_id):
        await update.message.reply_text(MENSAJE_REQUIERE_START)
        return
    
    ticket_activo = obtener_ticket_activo(user_id)

    if ticket_activo:
        ticket_id, estado, descripcion_actual = ticket_activo
        # Un reporte de peligro (humo, fuego...) tiene prioridad sobre cualquier estado del flujo
        if detectar_emergencia(texto_usuario) and estado != 'Esperando detalles':
            guardar_mensaje(ticket_id, 'usuario', texto_usuario)
            await _atender_emergencia(update, ticket_id, texto_usuario)
            return

        if estado in ('Esperando técnico', 'En atención'):
            guardar_mensaje(ticket_id, 'usuario', texto_usuario)
            return

        opcion = texto_usuario.strip().lower()
        eligio_tecnico = opcion in ('2', '2.', '2. hablar con un técnico', '2. hablar con un tecnico')
        eligio_asistente = opcion in ('1', '1.', '1. continuar con el asistente')
        if estado == 'Esperando decisión':
            guardar_mensaje(ticket_id, 'usuario', texto_usuario)
            if eligio_tecnico or usuario_pide_tecnico(texto_usuario):
                actualizar_estado_ticket(ticket_id, 'Esperando técnico')
                respuesta = "🧑‍💻 Un técnico continuará contigo por este chat. Puedes enviar los detalles adicionales mientras se conecta."
                guardar_mensaje(ticket_id, 'sistema', respuesta)
                await update.message.reply_text(respuesta, reply_markup=ReplyKeyboardRemove())
                return
            if eligio_asistente:
                actualizar_estado_ticket(ticket_id, 'Esperando detalles')
                respuesta = "Perfecto. Cuéntame con más detalle qué sucede: qué estabas haciendo, qué mensaje aparece y desde cuándo ocurre."
                guardar_mensaje(ticket_id, 'bot', respuesta)
                await update.message.reply_text(respuesta, reply_markup=ReplyKeyboardRemove())
                return

            respuesta = "Responde 1 para seguir con el asistente o 2 para hablar con un técnico."
            guardar_mensaje(ticket_id, 'bot', respuesta)
            await update.message.reply_text(respuesta, reply_markup=ReplyKeyboardRemove())
            return

        if estado == 'Esperando detalles':
            guardar_mensaje(ticket_id, 'usuario', texto_usuario)
            if eligio_tecnico or usuario_pide_tecnico(texto_usuario):
                actualizar_estado_ticket(ticket_id, 'Esperando técnico')
                respuesta = "🧑‍💻 Un técnico continuará contigo por este chat. Puedes enviar los detalles adicionales mientras se conecta."
                guardar_mensaje(ticket_id, 'sistema', respuesta)
                await update.message.reply_text(respuesta, reply_markup=ReplyKeyboardRemove())
                return

            descripcion_completa = f"{descripcion_actual}\nDetalle del usuario: {texto_usuario}"
            categoria, urgencia, instruccion = await analizar_incidente_ia(descripcion_completa)
            escalado = await requiere_intervencion_tecnica(descripcion_completa)
            nuevo_estado = 'Esperando técnico' if escalado else 'Esperando decisión'
            actualizar_detalles_ticket(
                ticket_id, descripcion_completa, categoria, urgencia, nuevo_estado
            )
            if urgencia == "Alta":
                enviar_email_urgente(ticket_id, urgencia, descripcion_completa)

            if escalado:
                respuesta = (
                    f"🧑‍💻 Gracias, agregué los detalles al ticket #{ticket_id}. "
                    "Por este problema, continuará contigo un técnico por este chat."
                )
                if urgencia == "Alta":
                    respuesta = f"🚨 URGENCIA ALTA\n{instruccion}\n\n{respuesta}"
                sender = 'sistema'
            else:
                respuesta = (
                    f"📝 Agregué los detalles al ticket #{ticket_id}.\n"
                    f"🛠️ Orientación: {instruccion}\n"
                    f"• Categoría: {categoria}\n• Urgencia: {urgencia}\n\n"
                    "¿Cómo quieres continuar?\n"
                    "1. Seguir hablando conmigo.\n"
                    "2. Hablar con un técnico.\n\nResponde 1 o 2."
                )
                sender = 'bot'
            guardar_mensaje(ticket_id, sender, respuesta)
            await update.message.reply_text(respuesta, reply_markup=ReplyKeyboardRemove())
            return

        if usuario_pide_tecnico(texto_usuario):
            guardar_mensaje(ticket_id, 'usuario', texto_usuario)
            actualizar_estado_ticket(ticket_id, 'Esperando técnico')
            respuesta = "🧑‍💻 Entiendo. Ahora te atenderá un técnico por este chat. Puedes escribir aquí y el equipo verá tus mensajes."
            guardar_mensaje(ticket_id, 'sistema', respuesta)
            await update.message.reply_text(respuesta)
            return

        nuevo_incidente = await es_nuevo_incidente(descripcion_actual, texto_usuario)
        if not nuevo_incidente:
            escalado = await requiere_intervencion_tecnica(texto_usuario)
            guardar_mensaje(ticket_id, 'usuario', texto_usuario)
            if escalado:
                actualizar_estado_ticket(ticket_id, 'Esperando técnico')
                respuesta = "🧑‍💻 Entiendo. Ahora te atenderá un técnico por este chat. Puedes escribir aquí y el equipo verá tus mensajes."
                guardar_mensaje(ticket_id, 'sistema', respuesta)
                await update.message.reply_text(respuesta)
                return

            respuesta = await responder_seguimiento_ia(texto_usuario)
            guardar_mensaje(ticket_id, 'bot', respuesta)
            await update.message.reply_text(respuesta)
            return

    escalado = await requiere_intervencion_tecnica(texto_usuario)
    # Un mensaje corto como "humo" o "fuego" no pide más detalle: es una emergencia
    if len(texto_usuario) < 15 and not escalado and not detectar_emergencia(texto_usuario):
        await update.message.reply_text("⚠️ Por favor, detalla un poco más tu problema (mínimo 15 caracteres).")
        return
        
    categoria, urgencia, instruccion = await analizar_incidente_ia(texto_usuario)
    estado = 'Esperando técnico' if escalado else 'Esperando decisión'
    ticket_id = crear_ticket(user_id, username, texto_usuario, categoria, urgencia, estado)
    guardar_mensaje(ticket_id, 'usuario', texto_usuario)
    
    notificar_si_urgente(ticket_id, categoria, urgencia, texto_usuario)

    await responder_ticket_inicial(update, ticket_id, categoria, urgencia, instruccion, escalado)

async def procesar_audio_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Definimos la variable al inicio de la función con la indentación base
    user_id = str(update.message.from_user.id)
    telegram_user = update.message.from_user
    username = f"@{telegram_user.username}" if telegram_user.username else (telegram_user.full_name or user_id)
    actualizar_nombre_tickets_activos(user_id, username)

    if usuario_requiere_start(user_id):
        await update.message.reply_text(MENSAJE_REQUIERE_START)
        return

    ticket_activo = obtener_ticket_activo(user_id)
    en_atencion_humana = ticket_activo and ticket_activo[1] in ('Esperando técnico', 'En atención')
    mensaje_espera = await update.message.reply_text(
        "🎙️ Recibí tu audio; lo estoy preparando para el técnico..." if en_atencion_humana
        else "🎙️ Descargando y analizando audio..."
    )
    ruta_temporal = f"temp_audio_{user_id}.ogg"
    
    try:
        # 2. Descargar el archivo
        archivo_voz = await context.bot.get_file(update.message.voice.file_id)
        await archivo_voz.download_to_drive(ruta_temporal)
        
        # 3. Leer los bytes en memoria
        with open(ruta_temporal, "rb") as f:
            datos_audio = {"mime_type": "audio/ogg", "data": f.read()}
        
        # 4. Transcribir con Gemini (misma IA y mismo cliente que el resto del bot, sin bloquear el loop)
        transcripcion = (await generar_contenido_ia([
            "Transcribe literalmente el mensaje de voz. Devuelve solo la transcripción, sin responder ni resumir.",
            datos_audio,
        ])).strip()
        if not transcripcion:
            await mensaje_espera.edit_text("❌ No pude entender el audio. Intenta de nuevo o escríbeme el problema.")
            return

        if en_atencion_humana:
            guardar_mensaje(ticket_activo[0], 'usuario', f"🎙️ Transcripción de audio: {transcripcion}")
            await mensaje_espera.edit_text("✅ Envié la transcripción al técnico. Puedes seguir escribiendo aquí.")
            if detectar_emergencia(transcripcion):
                await _atender_emergencia(update, ticket_activo[0], transcripcion)
        else:
            # 5. La transcripción sigue el mismo flujo (y las mismas reglas de urgencia) que un mensaje de texto
            await mensaje_espera.edit_text(f"🎙️ Entendí: {transcripcion}")
            await _procesar_texto(update, transcripcion)

    except Exception as e:
        # 6. Si algo falla, usamos la misma variable para avisar del error
        await mensaje_espera.edit_text(f"❌ Error procesando el audio: {e}")
        
    finally:
        # 7. Limpieza del servidor
        import os
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
