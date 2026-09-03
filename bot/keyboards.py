from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def menu_principal_keyboard():
    keyboard = [
        [InlineKeyboardButton(" Soluciones Rápidas", callback_data="menu_faq")],
        [InlineKeyboardButton(" Reportar un Problema", callback_data="reportar_problema")],
        [InlineKeyboardButton(" Mis Tickets", callback_data="mis_tickets")]
    ]
    return InlineKeyboardMarkup(keyboard)

def faq_keyboard():
    keyboard = [
        [InlineKeyboardButton("Sin Internet / Wi-Fi", callback_data="faq_red")],
        [InlineKeyboardButton("PC no enciende / Lenta", callback_data="faq_pc")],
        [InlineKeyboardButton("« Volver al Menú", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def faq_respuesta_keyboard():
    keyboard = [
        [InlineKeyboardButton(" Reportar este Problema", callback_data="reportar_problema")],
        [InlineKeyboardButton("« Volver al Menú", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def solucion_confirmar_keyboard():
    """Teclado de validación tras una propuesta de la IA."""
    keyboard = [
        [InlineKeyboardButton(" Sí, se solucionó", callback_data="solucion_si")],
        [InlineKeyboardButton(" No, intentar otra solución", callback_data="solucion_no")]
    ]
    return InlineKeyboardMarkup(keyboard)