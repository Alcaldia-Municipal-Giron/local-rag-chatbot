from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
from app.db.database import DatabaseConnectionError

from app.services.conversation_service import (
    obtener_historial,
    agregar_mensaje,
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

    # Guarda la pregunta actual del usuario en el historial.
    agregar_mensaje(
        request.session_id,
        {
            "role": "user",
            "content": request.message,
        },
    )

    # Recupera nuevamente el historial para incluir
    # el mensaje recién guardado.
    historial = obtener_historial(request.session_id)

    # Recupera los fragmentos más relevantes de los documentos.
    try:
        resultados = recuperar_contexto(
            request.message,
            top_k=3,
        )
    except DatabaseConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e),
        ) from e

    # Distancia máxima permitida para considerar
    # que existe suficiente información relevante.
    MAX_DISTANCE = 0.50

    # Si no hay resultados o el resultado más relevante
    # está demasiado lejos, no se consulta al LLM.
    if not resultados or resultados[0]["distance"] > MAX_DISTANCE:

        respuesta = (
            "No encontré información suficiente en los documentos "
            "para responder esta pregunta."
        )

        agregar_mensaje(
            request.session_id,
            {
                "role": "assistant",
                "content": respuesta,
            },
        )

        return respuesta

    # Convierte los fragmentos recuperados
    # en un único contexto textual.
    contexto = construir_contexto(resultados)

    def generar_respuesta():

        try:

            # Mantiene abierta la conexión con Ollama
            # para recibir la respuesta progresivamente.
            with httpx.stream(
                "POST",
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "qwen2.5-coder:3b-instruct",

                    "messages": [
                        {
                            "role": "system",
                            "content": f"""
Eres un asistente que responde preguntas utilizando
exclusivamente la información contenida en los documentos proporcionados.

Responde siempre en español.

REGLAS DE EVIDENCIA:

1. Utiliza únicamente la información presente en el CONTEXTO.

2. No utilices conocimientos generales, conocimientos previos del modelo
ni información externa a los documentos.

3. No inventes, supongas ni completes información que no aparezca
en el CONTEXTO.

4. No determines que una pregunta puede responderse únicamente porque
existan palabras o conceptos relacionados con ella.

5. Para responder una pregunta, el CONTEXTO debe contener información
suficiente y directamente relacionada con lo que se está preguntando.

6. Si la pregunta solicita un dato específico, como una cantidad,
límite, fecha, estado, condición o requisito, ese dato debe estar
explícitamente presente en el CONTEXTO.

7. Si la pregunta solicita un procedimiento, el CONTEXTO debe contener
los pasos o instrucciones necesarios para explicar dicho procedimiento.

8. Si la pregunta solicita requisitos legales, normativos o jurídicos,
solo puedes responder si esos requisitos aparecen explícitamente
en el CONTEXTO. No conviertas datos de un formulario en requisitos legales.

9. Si el CONTEXTO contiene información relacionada pero no suficiente
para responder exactamente la pregunta, debes indicarlo en lugar
de intentar completar la respuesta.

10. Si no existe información suficiente en el CONTEXTO, responde exactamente:

"No encontré información suficiente en los documentos para responder
esta pregunta."

11. Cuando sí exista información suficiente, responde de forma clara,
directa y basada únicamente en el CONTEXTO.

CONTEXTO:
{contexto}
""",
                        }
                    ]
                    + historial,

                    "stream": True,

                    "options": {
                        "num_predict": 400,
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "top_k": 40,
                        "seed": 42,
                        "num_ctx": 4096,
                    },
                },
                timeout=500.0,
            ) as respuesta:

                # Acumula todos los fragmentos para
                # guardar la respuesta completa al finalizar.
                respuesta_completa = ""

                # Procesa cada fragmento enviado por Ollama.
                for linea in respuesta.iter_lines():

                    if not linea:
                        continue

                    datos = json.loads(linea)

                    contenido = datos["message"]["content"]

                    if contenido:

                        # Acumula el fragmento.
                        respuesta_completa += contenido

                        # Envía inmediatamente el fragmento
                        # al cliente mediante streaming.
                        yield contenido

                # Guarda la respuesta solamente si Ollama
                # realmente generó contenido.
                if respuesta_completa:

                    agregar_mensaje(
                        request.session_id,
                        {
                            "role": "assistant",
                            "content": respuesta_completa,
                        },
                    )

        except httpx.RequestError as e:

            raise HTTPException(
                status_code=503,
                detail="No se pudo conectar con Ollama.",
            ) from e

    # Devuelve la respuesta como un flujo de texto.
    return StreamingResponse(
        generar_respuesta(),
        media_type="text/plain",
    )