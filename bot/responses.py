BIENVENIDA = (
    "¡Hola! Soy OmniDesk AI, tu asistente de soporte técnico.\n\n"
    "Puedo ayudarte a diagnosticar y resolver problemas de TI mediante Inteligencia Artificial. "
    "¿En qué te puedo ayudar hoy?"
)

MENU_SELECCION = "Selecciona una opción del menú:"

PEDIR_DETALLE_PROBLEMA = "Escribe a continuación el detalle de tu problema o falla."

PREGUNTA_FAQ_CATEGORIA = "Selecciona la categoría de tu duda:"

SOLUCION_FAQ_RED = (
    "Solución para Red / Internet:\n\n"
    "1. Revisa que el cable de red esté firme en el equipo.\n"
    "2. Reinicia tu router o adaptador de Wi-Fi.\n\n"
    "¿No se solucionó tu problema?"
)

SOLUCION_FAQ_PC = (
    "Solución para PC / Equipos:\n\n"
    "1. Mantén presionado el botón de encendido por 10 segundos.\n"
    "2. Verifica los cables de alimentación.\n\n"
    "¿No se solucionó tu problema?"
)

SOPORTE_NO_SOLUCIONADO = "¿No se solucionó tu problema?"

NO_USO_MENU = "Por favor, selecciona una opción del menú para interactuar con el bot:"

ERROR_API = "No se pudo conectar con el servidor backend. Revisa que la API esté activa."


def formato_ticket_creado(ticket_id: int, problema: str, gravedad: str, solucion: str) -> str:
    return (
        f"Ticket #{ticket_id} creado correctamente.\n\n"
        f"Problema: {problema}\n"
        f"Estado: En Proceso\n"
        f"Gravedad: {gravedad}\n\n"
        f"**Diagnóstico y Solución Sugerida:**\n"
        f"{solucion}\n\n"
        f"¿Esta solución logró resolver tu problema?"
    )


def formato_ticket_bloqueado(ticket_id: int, problema: str) -> str:
    return (
        f"Tienes el Ticket #{ticket_id} en atención en este momento.\n\n"
        f"Problema: {problema}\n\n"
        f"Debes resolver o finalizar tu ticket activo antes de reportar un nuevo problema."
    )


def formato_ticket_resuelto(ticket_id: int) -> str:
    return (
        f"¡Excelente! Ticket #{ticket_id} marcado correctamente como **Resuelto / Finalizado**."
    )


def formato_sugerencia_alternativa(ticket_id: int, solucion: str) -> str:
    return (
        f"Entendido. Paso alternativo para el Ticket #{ticket_id}:\n\n"
        f"**Sugerencia de OmniDesk AI:**\n"
        f"{solucion}\n\n"
        f"¿Esta solución logró resolver tu problema?"
    )


def formato_respuesta_chat_ia(ticket_id: int, respuesta_ia: str) -> str:
    return (
        f"**OmniDesk AI (Ticket #{ticket_id}):**\n\n"
        f"{respuesta_ia}\n\n"
        f"¿Lograste solucionar el problema o necesitas intentar otra alternativa?"
    )


def formato_mis_tickets(usuario: str, tickets: list) -> str:
    if not tickets:
        return f"No tienes tickets registrados a nombre de @{usuario}."
    
    mensaje = f"Historial de Tickets (@{usuario}):\n\n"
    for t in tickets:
        mensaje += (
            f"• Ticket #{t.get('ID')}: {t.get('Mensaje')}\n"
            f"  Estado: {t.get('Estado', 'Abierto')} | Gravedad: {t.get('Nivel_Gravedad', 'Media')}\n\n"
        )
    return mensaje