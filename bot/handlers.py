import httpx
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards import (
    menu_principal_keyboard, 
    faq_keyboard, 
    faq_respuesta_keyboard
)

API_URL = "http://127.0.0.1:8000/api/tickets"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["esperando_problema"] = False
    
    mensaje_bienvenida = (
        "¡Hola! Soy OmniDesk AI, tu asistente de soporte técnico.\n\n"
        "Por ahora estoy en fase de prototipo, pero pronto podré procesar "
        "tus consultas con Inteligencia Artificial. ¿En qué te puedo ayudar hoy?"
    )
    
    await update.message.reply_text(
        mensaje_bienvenida,
        reply_markup=menu_principal_keyboard()
    )

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # 1. Elimina los botones del mensaje previo para mantener limpia la conversación
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    data = query.data
    usuario = query.from_user.username or query.from_user.first_name or "Usuario Telegram"

    # Menú Principal
    if data == "menu_principal":
        context.user_data["esperando_problema"] = False
        await query.message.reply_text(
            "Selecciona una opción del menú:",
            reply_markup=menu_principal_keyboard()
        )

    # Reportar un Problema
    elif data == "reportar_problema":
        context.user_data["esperando_problema"] = True
        await query.message.reply_text(
            "Escribe a continuación el detalle de tu problema o falla."
        )

    # Mis Tickets
    elif data == "mis_tickets":
        context.user_data["esperando_problema"] = False
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(API_URL, timeout=5.0)
                res.raise_for_status()
                todos_los_tickets = res.json()

                mis_tickets = [t for t in todos_los_tickets if t.get("Usuario") == usuario]

                if not mis_tickets:
                    mensaje = f"No tienes tickets registrados a nombre de @{usuario}."
                else:
                    mensaje = f"Historial de Tickets (@{usuario}):\n\n"
                    for t in mis_tickets:
                        mensaje += (
                            f"• Ticket #{t['ID']}: {t['Mensaje']}\n"
                            f"  Estado: {t.get('Estado', 'Abierto')} | Gravedad: {t.get('Nivel_Gravedad', 'Media')}\n\n"
                        )

                await query.message.reply_text(
                    mensaje, 
                    reply_markup=menu_principal_keyboard()
                )
        except httpx.HTTPError:
            await query.message.reply_text(
                "No se pudo consultar la lista de tickets. Revisa que la API esté activa.",
                reply_markup=menu_principal_keyboard()
            )

    # Menú FAQs
    elif data == "menu_faq":
        context.user_data["esperando_problema"] = False
        await query.message.reply_text(
            "Selecciona la categoría de tu duda:",
            reply_markup=faq_keyboard()
        )

    # Respuestas Rápidas con Botón para Crear Ticket si no se solucionó
    elif data == "faq_red":
        solucion = (
            "Solución para Red / Internet:\n\n"
            "1. Revisa que el cable de red esté firme en el equipo.\n"
            "2. Reinicia tu router o adaptador de Wi-Fi.\n\n"
            "¿No se solucionó tu problema?"
        )
        await query.message.reply_text(solucion, reply_markup=faq_respuesta_keyboard())

    elif data == "faq_pc":
        solucion = (
            "Solución para PC / Equipos:\n\n"
            "1. Mantén presionado el botón de encendido por 10 segundos.\n"
            "2. Verifica los cables de alimentación.\n\n"
            "¿No se solucionó tu problema?"
        )
        await query.message.reply_text(solucion, reply_markup=faq_respuesta_keyboard())

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("esperando_problema"):
        await update.message.reply_text(
            "Por favor, selecciona una opción del menú para interactuar con el bot:",
            reply_markup=menu_principal_keyboard()
        )
        return

    texto_problema = update.message.text
    usuario = update.effective_user.username or update.effective_user.first_name or "Usuario Telegram"

    texto_lower = texto_problema.lower()
    if "internet" in texto_lower or "wifi" in texto_lower or "red" in texto_lower:
        gravedad = "Alta"
    else:
        gravedad = "Media"

    ticket = {
        "Usuario": usuario,
        "Mensaje": texto_problema,
        "Estado": "Abierto",
        "Nivel_Gravedad": gravedad
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(API_URL, json=ticket, timeout=5.0)
            res.raise_for_status()
            datos = res.json()["ticket"]

            context.user_data["esperando_problema"] = False

            respuesta_formateada = (
                f"Ticket #{datos['ID']} creado correctamente.\n\n"
                f"Problema: {texto_problema}\n"
                f"Estado: {datos.get('Estado', 'Abierto')}\n"
                f"Gravedad: {gravedad}"
            )

            await update.message.reply_text(
                respuesta_formateada,
                reply_markup=menu_principal_keyboard()
            )
    except httpx.HTTPError:
        await update.message.reply_text(
            "No pude registrar tu consulta en el sistema. Verifica que el backend esté funcionando.",
            reply_markup=menu_principal_keyboard()
        )