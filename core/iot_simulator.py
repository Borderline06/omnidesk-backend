import time
import random
import logging
import sys
import os

# Asegurar que el simulador reconozca el módulo core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import registrar_metrica_iot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - IoT_SENSOR - %(levelname)s - %(message)s')

def monitor_temperatura():
    logging.info("Iniciando nodo IoT simulado...")
    try:
        while True:
            temp = round(random.uniform(30.0, 75.0), 1)
            es_alerta = temp > 65.0
            
            # Registrar en base de datos
            registrar_metrica_iot("SRV-01", temp, es_alerta)
            
            if es_alerta:
                logging.warning(f"¡ALERTA CRÍTICA! SRV-01 superó el umbral: {temp}°C.")
            else:
                logging.info(f"SRV-01 - Temperatura estable: {temp}°C")
            
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Monitoreo IoT detenido.")

if __name__ == "__main__":
    monitor_temperatura()