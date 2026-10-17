# OmniDesk AI

Prototipo de mesa de ayuda omnicanal integrada con Telegram.

## Instalación y ejecución

1. Clona el repositorio y abre la carpeta en **VS Code**.

2. Crea `.env` en la raíz:

```env
TELEGRAM_TOKEN=aqui_va_el_token
```

3. En **Git Bash**, ejecuta:

```bash
py -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
py -m bot.main
```

4. Si aparece el mensaje de que el bot está escuchando, abre Telegram y envía:

```text
/start
```

**Requisitos:** Python instalado y Git Bash.


## IoT (MQTT + EMQX)

```
docker compose up -d --build     # emqx + bot + simulador IoT
```

- Broker EMQX: MQTT `1883`, WebSocket `8083`, dashboard `http://localhost:18083` (admin / public).
- El simulador publica cada 10 s una temperatura de 20-35 °C en `iot/omnidesk/servidores/temperatura`.
- El bot se suscribe a ese tópico y guarda las lecturas en la tabla `iot_metrics` (SQLite).
- Sin Docker: `python -m core.iot_simulator` y `python -m bot.main` con `MQTT_HOST=localhost`.
- Tests: `pytest tests`.
