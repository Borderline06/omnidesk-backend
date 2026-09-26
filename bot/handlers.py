from telegram import Update
from telegram.ext import ContextTypes
import sqlite3
import csv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from core.db import crear_ticket
from core.ai_service import analizar_incidente_ia, responder_seguimiento_ia

sesiones_activas = {}

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

def verificar_liberacion(user_id):
    try:
        conn = sqlite3.connect("omnidesk.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM liberaciones WHERE user_id = ?", (user_id,))
        liberado = cursor.fetchone() is not None
        if liberado:
            cursor.execute("DELETE FROM liberaciones WHERE user_id = ?", (user_id,))
            conn.commit()
        conn.close()
        return liberado
    except sqlite3.OperationalError:
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sesiones_activas.pop(str(update.message.from_user.id), None)
    mensaje = "¡Hola! Soy OmniDesk AI.\n\nDescribe tu problema tecnológico con detalle y lo procesaré."
    await update.message.reply_text(mensaje)

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "Usuario_Desconocido"
    
    if user_id in sesiones_activas:
        if verificar_liberacion(user_id):
            del sesiones_activas[user_id]
            await update.message.reply_text("✅ Su ticket anterior ha sido cerrado por el equipo técnico. ¿En qué nuevo problema puedo ayudarle?")
            return
            
        respuesta = await responder_seguimiento_ia(texto_usuario)
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        return

    if len(texto_usuario) < 15:
        await update.message.reply_text("⚠️ Por favor, detalla un poco más tu problema (mínimo 15 caracteres).")
        return
        
    categoria, urgencia, instruccion = await analizar_incidente_ia(texto_usuario)
    ticket_id = crear_ticket(user_id, username, texto_usuario, categoria, urgencia)
    
    sesiones_activas[user_id] = True
    
    # Ejecutar ambas automatizaciones en segundo plano
    automatizar_registro_csv(ticket_id, categoria, urgencia, texto_usuario)
    
    if "alta" in urgencia.lower() or "crítico" in urgencia.lower():
        enviar_email_urgente(ticket_id, urgencia, texto_usuario)
    
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

async def procesar_audio_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Definimos la variable al inicio de la función con la indentación base
    mensaje_espera = await update.message.reply_text("🎙️ Descargando y analizando audio...")
    ruta_temporal = f"temp_audio_{update.message.from_user.id}.ogg"
    
    try:
        # 2. Descargar el archivo
        archivo_voz = await context.bot.get_file(update.message.voice.file_id)
        await archivo_voz.download_to_drive(ruta_temporal)
        
        # 3. Leer los bytes en memoria
        with open(ruta_temporal, "rb") as f:
            datos_audio = {"mime_type": "audio/ogg", "data": f.read()}
        
        # 4. Procesar con Gemini 3.6 Flash
        import google.generativeai as genai
        import os
        from dotenv import load_dotenv
        
        # Cargamos la llave del .env y configuramos esta instancia
        load_dotenv()
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        modelo = genai.GenerativeModel('gemini-3.6-flash')
        respuesta = modelo.generate_content([
            "Eres el bot de soporte OmniDesk AI. Transcribe este problema del usuario y dale una solución técnica directa.", 
            datos_audio
        ])
        
        # 5. Editar el mensaje inicial con la respuesta exitosa
        await mensaje_espera.edit_text(f"✅ **Análisis de Audio:**\n\n{respuesta.text}", parse_mode="Markdown")
        
    except Exception as e:
        # 6. Si algo falla, usamos la misma variable para avisar del error
        await mensaje_espera.edit_text(f"❌ Error procesando el audio: {e}")
        
    finally:
        # 7. Limpieza del servidor
        import os
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)