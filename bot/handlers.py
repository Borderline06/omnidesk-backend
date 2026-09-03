import httpx
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards import (
    menu_principal_keyboard, 
    faq_keyboard, 
    faq_respuesta_keyboard,
    solucion_confirmar_keyboard
)
from core.ai_service import AgenteSoporte
import bot.responses as resp

API_URL = "http://127.0.0.1:8000/api/tickets"
agente = AgenteSoporte()
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["esperando_problema"] = False
    context.user_data["ticket_activo_id"] = None
    context.user_data["intentos"] = 0
    
    await update.message.reply_text(
        resp.BIENVENIDA,
        reply_markup=menu_principal_keyboard()
    )


async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    data = query.data
    usuario = query.from_user.username or query.from_user.first_name or "Usuario Telegram"

    # Menú Principal
    if data == "menu_principal":
        context.user_data["esperando_problema"] = False
        await query.message.reply_text(resp.MENU_SELECCION, reply_markup=menu_principal_keyboard())

    # Acción: Reportar un Problema
    elif data == "reportar_problema":
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(API_URL, timeout=5.0)
                todos_los_tickets = res.json()
                
                # Buscar si el usuario ya tiene un ticket en proceso
                ticket_en_proceso = next(
                    (t for t in todos_los_tickets if t.get("Usuario") == usuario and t.get("Estado") == "En Proceso"), 
                    None
                )

                if ticket_en_proceso:
                    context.user_data["esperando_problema"] = False
                    context.user_data["ticket_activo_id"] = ticket_en_proceso.get("ID")
                    context.user_data["ultimo_problema"] = ticket_en_proceso.get("Mensaje")

                    await query.message.reply_text(
                        resp.formato_ticket_bloqueado(ticket_en_proceso.get("ID"), ticket_en_proceso.get("Mensaje")),
                        reply_markup=solucion_confirmar_keyboard()
                    )
                    return
        except httpx.HTTPError:
            pass

        context.user_data["esperando_problema"] = True
        context.user_data["intentos"] = 0
        await query.message.reply_text(resp.PEDIR_DETALLE_PROBLEMA)

    # Acción: Botón "Sí, se solucionó"
    elif data == "solucion_si":
        ticket_id = context.user_data.get("ticket_activo_id")
        
        if ticket_id:
            try:
                async with httpx.AsyncClient() as client:
                    await client.put(f"{API_URL}/{ticket_id}", json={"Estado": "Resuelto"}, timeout=5.0)
            except httpx.HTTPError as e:
                logger.error(f"Error al actualizar estado del ticket #{ticket_id}: {e}")

        context.user_data["esperando_problema"] = False
        context.user_data["ticket_activo_id"] = None
        context.user_data["intentos"] = 0

        await query.message.reply_text(
            resp.formato_ticket_resuelto(ticket_id),
            parse_mode="Markdown",
            reply_markup=menu_principal_keyboard()
        )

    # Acción: Botón "No, intentar otra solución"
    elif data == "solucion_no":
        context.user_data["intentos"] = context.user_data.get("intentos", 1) + 1
        intentos = context.user_data["intentos"]
        problema = context.user_data.get("ultimo_problema", "Problema de soporte")
        ticket_id = context.user_data.get("ticket_activo_id")

        diagnostico = await agente.generar_solucion(problema, intentos=intentos)

        await query.message.reply_text(
            resp.formato_sugerencia_alternativa(ticket_id, diagnostico['solucion']),
            parse_mode="Markdown",
            reply_markup=solucion_confirmar_keyboard()
        )

    # Mis Tickets
    elif data == "mis_tickets":
        context.user_data["esperando_problema"] = False
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(API_URL, timeout=5.0)
                todos_los_tickets = res.json()
                mis_tickets = [t for t in todos_los_tickets if t.get("Usuario") == usuario]

                await query.message.reply_text(
                    resp.formato_mis_tickets(usuario, mis_tickets), 
                    reply_markup=menu_principal_keyboard()
                )
        except httpx.HTTPError:
            await query.message.reply_text(resp.ERROR_API, reply_markup=menu_principal_keyboard())

    # Menú FAQs
    elif data == "menu_faq":
        context.user_data["esperando_problema"] = False
        await query.message.reply_text(resp.PREGUNTA_FAQ_CATEGORIA, reply_markup=faq_keyboard())

    elif data == "faq_red":
        await query.message.reply_text(resp.SOLUCION_FAQ_RED, reply_markup=faq_respuesta_keyboard())

    elif data == "faq_pc":
        await query.message.reply_text(resp.SOLUCION_FAQ_PC, reply_markup=faq_respuesta_keyboard())


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja los mensajes de texto del usuario:
    1. Si está en 'esperando_problema', crea el ticket inicial.
    2. Si ya tiene un ticket activo, responde conversacionalmente vía Gemini.
    3. Si no tiene acciones activas ni ticket en proceso, pide usar el menú.
    """
    usuario = update.effective_user.username or update.effective_user.first_name or "Usuario Telegram"
    texto_usuario = update.message.text
    ticket_activo_id = context.user_data.get("ticket_activo_id")

    # CASO 1: Creación inicial del ticket
    if context.user_data.get("esperando_problema"):
        context.user_data["intentos"] = 1
        context.user_data["ultimo_problema"] = texto_usuario
        diagnostico = await agente.generar_solucion(texto_usuario, intentos=1)

        ticket = {
            "Usuario": usuario,
            "Mensaje": texto_usuario,
            "Estado": "En Proceso",
            "Nivel_Gravedad": diagnostico["gravedad"]
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(API_URL, json=ticket, timeout=5.0)
                res.raise_for_status()
                datos = res.json()["ticket"]

                ticket_id = datos.get("ID")
                context.user_data["ticket_activo_id"] = ticket_id
                context.user_data["esperando_problema"] = False

                await update.message.reply_text(
                    resp.formato_ticket_creado(ticket_id, texto_usuario, diagnostico["gravedad"], diagnostico["solucion"]),
                    parse_mode="Markdown",
                    reply_markup=solucion_confirmar_keyboard()
                )
        except httpx.HTTPError:
            await update.message.reply_text(resp.ERROR_API, reply_markup=menu_principal_keyboard())
        return

    # CASO 2: Interacción conversacional por texto durante un ticket activo
    if ticket_activo_id:
        context.user_data["intentos"] = context.user_data.get("intentos", 1) + 1
        intentos = context.user_data["intentos"]
        
        # Le enviamos a Gemini la duda o respuesta que escribió el usuario por chat
        diagnostico = await agente.generar_solucion(
            f"El usuario dice sobre su ticket #{ticket_activo_id}: '{texto_usuario}'", 
            intentos=intentos
        )

        await update.message.reply_text(
            resp.formato_respuesta_chat_ia(ticket_activo_id, diagnostico["solucion"]),
            parse_mode="Markdown",
            reply_markup=solucion_confirmar_keyboard()
        )
        return

    await update.message.reply_text(resp.NO_USO_MENU, reply_markup=menu_principal_keyboard())