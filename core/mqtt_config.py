import os
from dotenv import load_dotenv

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = "iot/omnidesk/servidores/temperatura"
MQTT_ENABLED = os.getenv("MQTT_ENABLED", "true").lower() == "true"

# Rango del simulador y umbral a partir del cual la lectura se marca como alerta
TEMP_MIN = 20.0
TEMP_MAX = 35.0
TEMP_ALERTA = float(os.getenv("TEMP_ALERTA", "32.0"))
INTERVALO_SEGUNDOS = 10
