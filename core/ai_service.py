import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.6-flash')

async def analizar_incidente_ia(texto):
    """Clasifica el incidente y da una recomendación inmediata."""
    try:
        prompt_sistema = (
            "Eres un agente experto de soporte técnico (Help Desk Nivel 1). "
            "Tu misión es clasificar el problema y dar UNA instrucción técnica inmediata de seguridad o solución al usuario.\n"
            "Responde ESTRICTAMENTE en este formato exacto: Categoría|Urgencia|Instrucción\n"
            "Categorías permitidas: Redes, Hardware, Accesos, Soporte General.\n"
            "Urgencias permitidas: Alta (peligro, quemado, caída de sistema), Media (lentitud), Baja (dudas).\n\n"
            f"Problema del usuario: {texto}"
        )
        
        response = await model.generate_content_async(prompt_sistema)
        resultado = response.text.strip().split('|')
        
        if len(resultado) >= 3:
            return resultado[0].strip(), resultado[1].strip(), resultado[2].strip()
            
    except Exception as e:
        logger.error(f"Fallo en Gemini: {e}. Activando respaldo local.")

    # RESPALDO (Fallback) 
    t = texto.lower()
    if any(k in t for k in ["quemado", "humo", "fuego", "chispas"]):
        return "Hardware", "Alta", "¡PELIGRO! Desconecte el equipo de la corriente eléctrica inmediatamente y no intente encenderlo."
    elif any(k in t for k in ["router", "internet", "red", "wi-fi"]): 
        return "Redes", "Alta", "Por favor, verifique si las luces del router están parpadeando."
    elif any(k in t for k in ["laptop", "impresora", "teclado", "disco"]): 
        return "Hardware", "Media", "Guarde su trabajo si es posible y evite forzar el equipo."
    elif any(k in t for k in ["contraseña", "acceso", "login"]): 
        return "Accesos", "Alta", "Un administrador restablecerá sus credenciales en el sistema en breve."
    
    return "Soporte General", "Baja", "Hemos registrado su consulta. Un técnico la revisará pronto."

async def responder_seguimiento_ia(texto):
    """Genera una respuesta conversacional fluida sin crear ticket."""
    try:
        prompt = (
            "Eres un técnico de soporte de TI experto y empático. El usuario está haciendo una pregunta "
            f"de seguimiento sobre su incidente técnico que ya fue registrado. Responde brevemente:\n{texto}"
        )
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Fallo en Gemini (seguimiento): {e}")
        return "Mantenga la calma y siga las instrucciones iniciales. El técnico está en camino."