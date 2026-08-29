import time
import random
import logging

# Configurar el registro de eventos (logs)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - IoT_SENSOR - %(levelname)s - %(message)s')

def monitor_temperatura():
    """Simula la lectura de un sensor de temperatura en el cuarto de servidores."""
    logging.info("Iniciando nodo IoT simulado...")
    try:
        while True:
            # Generar temperatura aleatoria entre 30 y 75 grados
            temp = round(random.uniform(30.0, 75.0), 1)
            
            if temp > 65.0:
                logging.warning(f"¡ALERTA CRÍTICA! Servidor 01 superó el umbral: {temp}°C. Generando ticket...")
                # Aquí luego integraremos la lógica para enviar la alerta al bot
            else:
                logging.info(f"Servidor 01 - Temperatura estable: {temp}°C")
            
            time.sleep(4) # Leer datos cada 4 segundos
    except KeyboardInterrupt:
        logging.info("Monitoreo IoT detenido por el usuario.")

if __name__ == "__main__":
    monitor_temperatura()