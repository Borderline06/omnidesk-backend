import logging
import httpx

from bot.config import SHEETS_WEBHOOK_URL, SHEETS_WEBHOOK_SECRET

logger = logging.getLogger(__name__)


async def enviar_ticket_a_sheets(
    ticket_id, user_id, username, descripcion, categoria, urgencia, estado, fecha
):
    """Replica un ticket en la hoja de Google Sheets vía Apps Script.
    No lanza excepciones hacia afuera: si falla, solo se registra en el log
    para no interrumpir la respuesta al usuario de Telegram.
    """
    if not SHEETS_WEBHOOK_URL:
        logger.warning("SHEETS_WEBHOOK_URL no configurada; se omite la replicación a Sheets.")
        return

    payload = {
        "secret": SHEETS_WEBHOOK_SECRET,
        "id": ticket_id,
        "user_id": user_id,
        "username": username,
        "descripcion": descripcion,
        "categoria": categoria,
        "urgencia": urgencia,
        "estado": estado,
        "fecha": fecha,
    }

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.post(SHEETS_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "ok":
                logger.error(f"Apps Script respondió con error para ticket #{ticket_id}: {data}")
    except Exception as e:
        logger.error(f"No se pudo replicar el ticket #{ticket_id} en Sheets: {e}")