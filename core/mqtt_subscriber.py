import json
import logging

import paho.mqtt.client as mqtt

from core.db import registrar_metrica_iot
from core.mqtt_config import MQTT_HOST, MQTT_PORT, MQTT_TOPIC, TEMP_ALERTA

logger = logging.getLogger(__name__)

def _parsear_mensaje(payload):
    """Acepta JSON {"servidor","temperatura"} o un número plano. Devuelve (servidor, temp) o None."""
    texto = payload.decode("utf-8", errors="replace").strip()
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError:
        return None
    if isinstance(datos, dict):
        servidor = str(datos.get("servidor", "SRV-01"))
        temp = datos.get("temperatura")
    else:
        servidor, temp = "SRV-01", datos
    if isinstance(temp, bool) or not isinstance(temp, (int, float)):
        return None
    return servidor, float(temp)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # Se suscribe aquí para que también se restablezca tras una reconexión
        client.subscribe(MQTT_TOPIC, qos=1)
        logger.info(f"Suscrito a {MQTT_TOPIC} en {MQTT_HOST}:{MQTT_PORT}")
    else:
        logger.error(f"Conexión MQTT rechazada (rc={rc})")

def on_message(client, userdata, msg):
    try:
        parsed = _parsear_mensaje(msg.payload)
        if parsed is None:
            logger.warning(f"Mensaje MQTT ignorado (formato inválido): {msg.payload!r}")
            return
        servidor, temp = parsed
        alerta = temp > TEMP_ALERTA
        registrar_metrica_iot(servidor, temp, alerta)
        logger.info(f"IoT {servidor}: {temp}°C {'(ALERTA)' if alerta else ''} guardado en BD")
    except Exception as e:
        logger.error(f"No se pudo guardar la lectura IoT: {e}")

def iniciar_suscriptor():
    """Inicia el suscriptor en un hilo propio de paho. No bloquea ni falla si no hay broker."""
    client = mqtt.Client(client_id="omnidesk-backend-subscriber")
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    try:
        # connect_async + loop_start reintenta en segundo plano hasta que EMQX esté arriba
        client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()
    except Exception as e:
        logger.error(f"No se pudo iniciar el suscriptor MQTT: {e}")
        return None
    return client

if __name__ == "__main__":
    import time
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    from core.db import init_db
    init_db()
    iniciar_suscriptor()
    while True:
        time.sleep(3600)
