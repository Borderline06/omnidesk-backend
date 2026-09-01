import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

RUTA_DATOS_IOT = Path(__file__).parent.parent / "data" / "iot_data.json"
RUTA_TICKETS = Path(__file__).parent.parent / "data" / "tickets.json"


@router.get("/iot")
def obtener_datos_iot():
    with open(RUTA_DATOS_IOT, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


@router.get("/tickets")
def obtener_tickets():
    with open(RUTA_TICKETS, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


@router.post("/tickets")
def crear_ticket(ticket: dict):
    with open(RUTA_TICKETS, "r", encoding="utf-8") as archivo:
        tickets = json.load(archivo)

    nuevo_id = len(tickets) + 1

    ticket["ID"] = nuevo_id

    tickets.append(ticket)

    with open(RUTA_TICKETS, "w", encoding="utf-8") as archivo:
        json.dump(tickets, archivo, ensure_ascii=False, indent=4)

    return {
        "mensaje": "Ticket creado correctamente",
        "ticket": ticket
    }