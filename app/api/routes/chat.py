from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
from app.services.conversation_service import (
    obtener_historial,
    agregar_mensaje
)


# Define la estructura de los datos que el cliente debe enviar al endpoint de chat.
class ChatRequest(BaseModel):
    session_id: str
    message: str

# Crea un router para agrupar los endpoints relacionados con el chatbot.
router = APIRouter()

# Envía el mensaje a Ollama y transmite progresivamente la respuesta de Qwen.
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
                            "role": "system",
                            "content": """Eres un asistente especializado en programación.

                            Responde siempre en español.

                            Explica los conceptos de forma clara, sencilla y ordenada.

                            Cuando sea posible, utiliza ejemplos prácticos para facilitar la comprensión.

                            No inventes información. Si no tienes suficiente información para responder, indícalo claramente."""
                        }
                    ] + historial,
                    "stream": True,
                    "options":{
                        "num_predict": 200, # Número máximo de tokens a generar.
                        "temperature": 0.2, # Controla la aleatoriedad de la respuesta generada. Un valor más bajo produce respuestas más deterministas.
                        "top_p": 0.9, # Controla la diversidad de la respuesta generada. Un valor más alto permite una mayor variedad de palabras.
                        "top_k": 40, # Limita el número de palabras candidatas a considerar en cada paso de generación. Un valor más bajo puede producir respuestas más coherentes pero menos diversas.
                        "seed": 42,  # Semilla para la generación de números aleatorios, lo que permite reproducir resultados consistentes.
                        "num_ctx": 4096, # Número máximo de tokens que el modelo puede considerar en su contexto. Un valor más alto permite respuestas más largas y coherentes.
                        
                    }
                },
                timeout=120.0
            ) as respuesta:
                
                # Acumula todos los fragmentos de la respuesta para guardarlos al finalizar.
                respuesta_completa = ""

                # Genera cada fragmento de texto a medida que Ollama lo envía.
                for linea in respuesta.iter_lines():

                    if linea:
                        datos = json.loads(linea)

                        contenido = datos["message"]["content"]

                        if contenido:
                            # Acumula cada fragmento para reconstruir la respuesta completa.
                            respuesta_completa += contenido
                            
                            # Envía el fragmento inmediatamente al cliente para mantener el streaming.
                            yield contenido
                            
            # Guarda la respuesta completa del asistente en la sesión actual.
            agregar_mensaje(
                request.session_id,
                {
                "role": "assistant",
                "content": respuesta_completa
            })

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