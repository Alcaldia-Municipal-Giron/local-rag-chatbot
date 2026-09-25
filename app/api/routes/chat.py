from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json

from app.services.conversation_service import (
    obtener_historial,
    agregar_mensaje
)

from app.rag.retriever import recuperar_contexto
from app.rag.context_builder import construir_contexto


# Define la estructura de los datos que el cliente debe enviar al endpoint de chat.
class ChatRequest(BaseModel):
    session_id: str
    message: str


# Crea un router para agrupar los endpoints relacionados con el chatbot.
router = APIRouter()


# Envía el mensaje a Ollama utilizando el contexto recuperado mediante RAG
# y transmite progresivamente la respuesta de Qwen.
@router.post("/chat")
def chat(request: ChatRequest):

    # Guarda la pregunta actual del usuario en el historial de la conversación.
    agregar_mensaje(
        request.session_id,
        {
            "role": "user",
            "content": request.message
        }
    )

    # Recupera nuevamente el historial para incluir el mensaje recién guardado.
    historial = obtener_historial(request.session_id)

    # Recupera los fragmentos más relevantes de los documentos
    # utilizando la pregunta actual del usuario.
    resultados = recuperar_contexto(
        request.message,
        top_k=3
    )

    # Convierte los fragmentos recuperados en un único contexto textual.
    contexto = construir_contexto(resultados)

    def generar_respuesta():

        try:
            # Mantiene abierta la conexión con Ollama para recibir
            # la respuesta por fragmentos.
            with httpx.stream(
                "POST",
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "qwen2.5-coder:3b-instruct",

                    "messages": [
                        {
                            "role": "system",
                            "content": f"""Eres un asistente que responde utilizando los documentos proporcionados.

Responde siempre en español.

Utiliza el contexto proporcionado para responder la pregunta del usuario.

No inventes información que no esté respaldada por el contexto.

Si el contexto no contiene información suficiente para responder,
indícalo claramente.

CONTEXTO:
{contexto}
"""
                        }
                    ] + historial,

                    "stream": True,

                    "options": {
                        "num_predict": 200,
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "top_k": 40,
                        "seed": 42,
                        "num_ctx": 4096
                    }
                },
                timeout=300.0
            ) as respuesta:

                # Acumula todos los fragmentos de la respuesta
                # para guardarlos al finalizar.
                respuesta_completa = ""

                # Genera cada fragmento de texto a medida que Ollama lo envía.
                for linea in respuesta.iter_lines():

                    if linea:
                        datos = json.loads(linea)

                        contenido = datos["message"]["content"]

                        if contenido:
                            # Acumula cada fragmento para reconstruir
                            # la respuesta completa.
                            respuesta_completa += contenido

                            # Envía el fragmento inmediatamente al cliente
                            # para mantener el streaming.
                            yield contenido

            # Guarda la respuesta completa del asistente
            # en la sesión actual.
            agregar_mensaje(
                request.session_id,
                {
                    "role": "assistant",
                    "content": respuesta_completa
                }
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="No se pudo conectar con Ollama."
            )

    # Devuelve la respuesta como un flujo de texto
    # en lugar de esperar la respuesta completa.
    return StreamingResponse(
        generar_respuesta(),
        media_type="text/plain"
    )