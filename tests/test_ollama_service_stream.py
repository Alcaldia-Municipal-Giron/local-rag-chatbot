
import json

import httpx
import pytest

from app.services.ollama_service import (
    generar_respuesta,
    OllamaServiceError,
)

from contextlib import contextmanager

# Crea una respuesta HTTP simulada con fragmentos JSON.
def crear_respuesta_simulada(fragmentos):
    contenido = "\n".join(
        json.dumps(fragmento) for fragmento in fragmentos
    )

    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/chat",
    )

    return httpx.Response(
        200,
        content=contenido.encode("utf-8"),
        request=request,
    )


# Simula la conexión HTTP sin acceder al servidor real.
def simular_ollama(monkeypatch, fragmentos):
    respuesta = crear_respuesta_simulada(fragmentos)

    # Simula el administrador de contexto que utiliza httpx.stream().
    @contextmanager
    def mock_stream(*args, **kwargs):
        try:
            yield respuesta
        finally:
            respuesta.close()

    monkeypatch.setattr(
        "app.services.ollama_service.httpx.stream",
        mock_stream,
    )


# Comprueba que una generación con done=true se complete.
def test_stream_finalizado_correctamente(monkeypatch):
    simular_ollama(
        monkeypatch,
        [
            {"message": {"content": "Hola"}, "done": False},
            {"message": {"content": " mundo"}, "done": False},
            {"message": {"content": ""}, "done": True},
        ],
    )

    resultado = "".join(
        generar_respuesta(
            [{"role": "user", "content": "Hola"}]
        )
    )

    assert resultado == "Hola mundo"


# Comprueba que un flujo sin done=true genere un error.
def test_stream_interrumpido(monkeypatch):
    simular_ollama(
        monkeypatch,
        [
            {
                "message": {"content": "Respuesta parcial"},
                "done": False,
            },
        ],
    )

    generador = generar_respuesta(
        [{"role": "user", "content": "Hola"}]
    )

    assert next(generador) == "Respuesta parcial"

    with pytest.raises(
        OllamaServiceError,
        match="terminó inesperadamente",
    ):
        next(generador)
