import os
import logging
import re
import unicodedata
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.6-flash')

def _normalizar(texto):
    texto = unicodedata.normalize('NFKD', texto.lower())
    return ''.join(caracter for caracter in texto if not unicodedata.combining(caracter))

def usuario_pide_tecnico(texto):
    texto = _normalizar(texto)
    solicitudes = (
        'hablar con un tecnico', 'hablar con tecnico', 'quiero un tecnico',
        'necesito un tecnico', 'contactar con un tecnico', 'con un humano',
        'hablar con una persona', 'operador humano', 'agente humano',
        'asesor humano', 'persona real', 'hablar con alguien',
        'necesito hablar con alguien', 'hablar con soporte',
        'quiero un agente', 'quiero un asesor'
    )
    return any(frase in texto for frase in solicitudes)

async def es_nuevo_incidente(descripcion_actual, mensaje):
    """Compara el mensaje con el ticket abierto para separar problemas distintos."""
    mensaje_normalizado = _normalizar(mensaje)
    if len(mensaje.strip()) < 18:
        return False

    marcadores_nuevo = (
        'otro problema', 'nuevo problema', 'ahora tengo', 'tambien tengo',
        'aparte tengo', 'ademas tengo', 'cambiando de tema',
    )
    if any(marcador in mensaje_normalizado for marcador in marcadores_nuevo):
        return True

    marcadores_seguimiento = (
        'sigue igual', 'no funciona', 'no funciono', 'todavia no',
        'aun no se soluciona', 'mismo problema', 'lo mismo',
    )
    if any(marcador in mensaje_normalizado for marcador in marcadores_seguimiento):
        return False

    try:
        prompt = (
            "Decide si el mensaje describe un incidente técnico NUEVO y diferente al ticket abierto, "
            "o si es una aclaración/seguimiento del mismo problema. Responde únicamente SI para "
            "un problema nuevo y NO para seguimiento.\n"
            f"Ticket abierto: {descripcion_actual}\nMensaje nuevo: {mensaje}"
        )
        response = await model.generate_content_async(prompt)
        return response.text.strip().upper().startswith('SI')
    except Exception as e:
        logger.error(f"Fallo al comparar el nuevo incidente: {e}")
        stopwords = {
            'que', 'para', 'por', 'con', 'sin', 'una', 'uno', 'unos', 'unas',
            'del', 'las', 'los', 'como', 'hola', 'tengo', 'mi', 'mis', 'está',
            'esta', 'hay', 'muy', 'pero', 'porque', 'desde', 'problema', 'error',
        }
        palabras_actual = set(re.findall(r'\w+', _normalizar(descripcion_actual))) - stopwords
        palabras_nuevas = set(re.findall(r'\w+', mensaje_normalizado)) - stopwords
        return bool(palabras_actual and palabras_nuevas and not palabras_actual.intersection(palabras_nuevas))

async def requiere_intervencion_tecnica(texto):
    """Detecta si el caso necesita pasar de la IA a un técnico humano."""
    if usuario_pide_tecnico(texto):
        return True

    try:
        prompt = (
            "Evalúa si este caso de soporte debe escalarse a un técnico humano. "
            "Responde únicamente SI o NO. Responde SI si hay riesgo de seguridad, "
            "pérdida de datos, acceso/cuenta comprometida, falla crítica, el usuario "
            "ya intentó soluciones sin éxito o el caso requiere acceso/acciones que "
            "un bot no puede realizar. En los demás casos responde NO.\n"
            f"Mensaje del usuario: {texto}"
        )
        response = await model.generate_content_async(prompt)
        return response.text.strip().upper().startswith('SI')
    except Exception as e:
        logger.error(f"Fallo al detectar escalamiento: {e}")
        texto = _normalizar(texto)
        return any(frase in texto for frase in (
            'no funciono', 'sigue igual', 'ya intente', 'ya probe',
            'perdi mis datos', 'cuenta hackeada', 'me hackearon',
            'humo', 'quemado', 'chispas', 'fuego'
        ))

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
