import os
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

# Obtener el token y validar que exista
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

SHEETS_WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL", "")
SHEETS_WEBHOOK_SECRET = os.getenv("SHEETS_WEBHOOK_SECRET", "")

if not TELEGRAM_TOKEN:
    raise ValueError("Error: TELEGRAM_TOKEN no está configurado en el archivo .env")