from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json


# Define la estructura de los datos que el cliente debe enviar al endpoint de chat.
class ChatRequest(BaseModel):
    message: str


# Crea un router para agrupar los endpoints relacionados con el chatbot.
router = APIRouter()


# Envía el mensaje a Ollama y transmite progresivamente la respuesta de Qwen.
@router.post("/chat")
def chat(request: ChatRequest):

    def generar_respuesta():

        try:
            # Mantiene abierta la conexión con Ollama para recibir la respuesta por fragmentos.
            with httpx.stream(
                "POST",
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "qwen2.5-coder:3b-instruct",
                    "messages": [
                        {
                            "role": "user",
                            "content": request.message
                        }
                    ],
                    "stream": True
                },
                timeout=120.0
            ) as respuesta:

                # Genera cada fragmento de texto a medida que Ollama lo envía.
                for linea in respuesta.iter_lines():

                    if linea:
                        datos = json.loads(linea)

                        contenido = datos["message"]["content"]

                        if contenido:
                            yield contenido

        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="No se pudo conectar con Ollama."
            )

    # Devuelve la respuesta como un flujo de texto en lugar de esperar la respuesta completa.
    return StreamingResponse(
        generar_respuesta(),
        media_type="text/plain"
    )