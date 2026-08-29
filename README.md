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
