import json
import logging
import random
import time
from pathlib import Path


# Configuración del registro de eventos
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - IoT_SENSOR - %(levelname)s - %(message)s"
)

RUTA_DATOS = Path(__file__).parent.parent / "data" / "iot_data.json"


def guardar_datos(temperatura, estado, historial):
    datos = {
        "servidor": "Servidor 01",
        "temperatura": temperatura,
        "estado": estado,
        "historial": historial
    }

    with open(RUTA_DATOS, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4)


def monitor_temperatura():
    """Simula la lectura de un sensor de temperatura en el cuarto de servidores."""

    logging.info("Iniciando nodo IoT simulado...")

    historial = []

    try:
        while True:
            # Generar temperatura aleatoria entre 30 y 75 grados
            temperatura = round(random.uniform(30.0, 75.0), 1)

            # Determinar el estado según el umbral
            if temperatura > 65.0:
                estado = "CRITICO"
                logging.warning(
                    f"¡ALERTA CRÍTICA! Servidor 01 superó el umbral: "
                    f"{temperatura}°C. Generando ticket..."
                )
            else:
                estado = "NORMAL"
                logging.info(
                    f"Servidor 01 - Temperatura estable: {temperatura}°C"
                )

            # Guardar la lectura en el historial
            historial.append(temperatura)

            # Mantener únicamente las últimas 20 lecturas
            historial = historial[-20:]

            # Actualizar los datos disponibles para el dashboard
            guardar_datos(temperatura, estado, historial)

            time.sleep(4)

    except KeyboardInterrupt:
        logging.info("Monitoreo IoT detenido por el usuario.")


if __name__ == "__main__":
    monitor_temperatura()