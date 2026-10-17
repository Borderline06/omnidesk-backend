import asyncio
import json

import pytest

from core import ai_service
from core.ai_service import (
    clasificar_emergencia, detectar_emergencia, analizar_incidente_ia,
    requiere_intervencion_tecnica, _normalizar_urgencia,
)
from core.mqtt_subscriber import _parsear_mensaje


@pytest.mark.parametrize("texto", [
    "humo", "Hay HUMO en la oficina", "salen chispas del enchufe", "mi pc está quemada",
    "se quemó la fuente", "huele a quemado", "hay fuego", "caída de servidor",
    "se cayó el servidor", "el servidor está caído", "servidor down",
])
def test_detecta_emergencias(texto):
    assert detectar_emergencia(texto)


@pytest.mark.parametrize("texto", [
    "mi laptop va lenta", "no puedo entrar a mi cuenta", "necesito reducir costos", "cómo cambio mi contraseña",
])
def test_no_marca_falsos_positivos(texto):
    assert not detectar_emergencia(texto)


def test_tipo_de_emergencia():
    assert clasificar_emergencia("hay humo") == 'peligro'
    assert clasificar_emergencia("caída de servidor") == 'servidor'


@pytest.mark.parametrize("valor,esperado", [
    ("Alta", "Alta"), ("alta (peligro)", "Alta"), ("Urgencia: Baja", "Baja"),
    ("MEDIA", "Media"), ("Crítico", "Alta"), ("", "Media"), ("???", "Media"),
])
def test_normalizar_urgencia(valor, esperado):
    assert _normalizar_urgencia(valor) == esperado


def test_humo_es_alta_aunque_gemini_diga_baja(monkeypatch):
    async def gemini_baja(_):
        return "Soporte General|Baja|Reinicie el equipo."
    monkeypatch.setattr(ai_service, "generar_contenido_ia", gemini_baja)
    categoria, urgencia, instruccion = asyncio.run(analizar_incidente_ia("hay humo saliendo de mi pc"))
    assert urgencia == "Alta"
    assert categoria == "Hardware"
    assert "desconecte" in instruccion.lower()


def test_humo_es_alta_si_gemini_falla(monkeypatch):
    async def gemini_falla(_):
        raise RuntimeError("sin red")
    monkeypatch.setattr(ai_service, "generar_contenido_ia", gemini_falla)
    _, urgencia, instruccion = asyncio.run(analizar_incidente_ia("humo"))
    assert urgencia == "Alta"
    assert "desconecte" in instruccion.lower()


def test_caida_de_servidor_es_alta(monkeypatch):
    async def gemini_falla(_):
        raise RuntimeError("sin red")
    monkeypatch.setattr(ai_service, "generar_contenido_ia", gemini_falla)
    _, urgencia, _ = asyncio.run(analizar_incidente_ia("tuvimos una caída de servidor"))
    assert urgencia == "Alta"


def test_respuesta_normal_de_gemini_se_respeta(monkeypatch):
    async def gemini_ok(_):
        return "Redes|Media|Reinicie el router."
    monkeypatch.setattr(ai_service, "generar_contenido_ia", gemini_ok)
    assert asyncio.run(analizar_incidente_ia("el wifi va lento")) == ("Redes", "Media", "Reinicie el router.")


def test_emergencia_siempre_escala():
    assert asyncio.run(requiere_intervencion_tecnica("hay fuego")) is True


def test_parseo_mqtt():
    assert _parsear_mensaje(json.dumps({"servidor": "SRV-01", "temperatura": 27.4}).encode()) == ("SRV-01", 27.4)
    assert _parsear_mensaje(b"25.5") == ("SRV-01", 25.5)
    assert _parsear_mensaje(b"basura") is None
    assert _parsear_mensaje(b'{"temperatura": "x"}') is None
