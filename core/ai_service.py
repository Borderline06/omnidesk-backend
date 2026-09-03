import os
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class AgenteSoporte:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error(" CRÍTICO: GEMINI_API_KEY no está configurada en el archivo .env")
            raise ValueError("No se encontró la GEMINI_API_KEY en el entorno.")
        
        self.client = genai.Client(api_key=api_key)

    async def generar_solucion(self, problema: str, intentos: int = 1) -> dict:
        prompt_sistema = (
            "Eres OmniDesk AI, un agente de soporte técnico Nivel 1 capacitado para diagnosticar "
            "y resolver problemas de infraestructura, software y hardware.\n\n"
            f"El usuario está en el intento #{intentos} para solucionar su problema.\n"
            "INSTRUCCIONES:\n"
            "1. Proporciona una solución técnica clara y concisa de máximo 3 pasos numerados.\n"
            "2. Si el intento es mayor a 1, ofrece un diagnóstico o procedimiento técnico más avanzado pero simple.\n"
            "3. Clasifica la gravedad del problema únicamente como 'Alta' o 'Media'.\n\n"
            "4. Otorga respuestas y soluciones simples y faciles de entender, evitando tecnicismos innecesarios.\n"
            "FORMATO OBLIGATORIO DE RESPUESTA (Respeta las etiquetas exactas):\n"
            "GRAVEDAD: [Alta/Media]\n"
            "SOLUCION: [Pasos numerados]"
        )

        # Modelos válidos en la API de Gemini
        modelos_a_probar ='gemini-3.6-flash',
        response = None
        ultimo_error = None

        for modelo in modelos_a_probar:
            try:
                response = self.client.models.generate_content(
                    model=modelo,
                    contents=f"Problema reportado por el usuario: {problema}",
                    config=types.GenerateContentConfig(
                        system_instruction=prompt_sistema,
                        temperature=0.3,
                    ),
                )
                if response and response.text:
                    logger.info(f" Respuesta generada exitosamente con el modelo: {modelo}")
                    break
            except Exception as e:
                logger.warning(f" El modelo {modelo} falló, intentando alternativa... Error: {e}")
                ultimo_error = e

        if not response or not response.text:
            logger.error(f"Ningún modelo de Gemini respondió adecuadamente. Error final: {ultimo_error}")
            raise ultimo_error

        texto = response.text
        gravedad = "Media"
        solucion = texto

        if "GRAVEDAD:" in texto and "SOLUCION:" in texto:
            partes = texto.split("SOLUCION:")
            linea_gravedad = partes[0].replace("GRAVEDAD:", "").strip()
            if linea_gravedad in ["Alta", "Media"]:
                gravedad = linea_gravedad
            solucion = partes[1].strip()

        return {
            "solucion": f"{solucion}\n\n*(Solución generada por Gemini AI)*", 
            "gravedad": gravedad
        }