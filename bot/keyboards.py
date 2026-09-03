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
    """Se muestra tras dar la respuesta rápida si no se solucionó el problema."""
    keyboard = [
        [InlineKeyboardButton(" Reportar este Problema", callback_data="reportar_problema")],
        [InlineKeyboardButton("« Volver al Menú", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(keyboard)