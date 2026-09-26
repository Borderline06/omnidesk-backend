import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def enviar_email_urgente(ticket_id, descripcion, urgencia):
    # Configuración del servidor (Usando Gmail como ejemplo)
    remitente = os.getenv("EMAIL_REMITENTE") # Tu correo (ej. omnidesk.utp@gmail.com)
    password = os.getenv("EMAIL_PASSWORD")   # Contraseña de aplicación de Google
    destinatario = "admin_ti@empresa.com"    # Correo del jefe de TI (puedes poner el tuyo para probar)

    if not remitente or not password:
        print("Faltan credenciales de correo en el archivo .env")
        return False

    # Estructura del correo
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = f"🚨 URGENTE: Nuevo Ticket Crítico [ID: {ticket_id}]"

    cuerpo = f"""
    Se ha reportado una incidencia crítica en el sistema OmniDesk AI.
    
    Detalles del reporte:
    - Ticket ID: {ticket_id}
    - Nivel de Urgencia: {urgencia}
    - Descripción del usuario: {descripcion}
    
    Por favor, ingresar al dashboard para gestionar la solución.
    """
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Conexión y envío
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remitente, password)
        servidor.send_message(mensaje)
        servidor.quit()
        print(f"Alerta de email enviada para el ticket {ticket_id}")
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False