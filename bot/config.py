import os
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

# Obtener el token y validar que exista
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("Error: TELEGRAM_TOKEN no está configurado en el archivo .env")