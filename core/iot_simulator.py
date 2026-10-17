import json
import logging
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt

from core.mqtt_config import (
    MQTT_HOST, MQTT_PORT, MQTT_TOPIC, TEMP_MIN, TEMP_MAX, INTERVALO_SEGUNDOS,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - IoT_SENSOR - %(levelname)s - %(message)s')

SERVIDOR = "SRV-01"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Conectado al broker MQTT {MQTT_HOST}:{MQTT_PORT}")
    else:
        logging.error(f"Conexión MQTT rechazada (rc={rc})")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.warning("Conexión MQTT perdida; paho reintentará automáticamente.")

def monitor_temperatura():
    logging.info("Iniciando nodo IoT simulado...")
    client = mqtt.Client(client_id="omnidesk-iot-simulator")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    # Reintenta hasta que el broker (EMQX) esté disponible
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            break
        except OSError as e:
            logging.warning(f"Broker no disponible ({e}); reintentando en 5 s...")
            time.sleep(5)

    client.loop_start()
    try:
        while True:
            temp = round(random.uniform(TEMP_MIN, TEMP_MAX), 1)
            payload = json.dumps({
                "servidor": SERVIDOR,
                "temperatura": temp,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            })
            info = client.publish(MQTT_TOPIC, payload, qos=1)
            logging.info(f"Publicado en {MQTT_TOPIC}: {payload} (mid={info.mid})")
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        logging.info("Monitoreo IoT detenido.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    monitor_temperatura()
