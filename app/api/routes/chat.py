
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.database import DatabaseConnectionError

from app.services.conversation_service import (
    obtener_historial,
    agregar_mensaje,
)

from app.services.ollama_service import (
    generar_respuesta as generar_respuesta_ollama,
    OllamaServiceError,
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

    # Construye los mensajes que recibirá el modelo.
    messages = [
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
    ] + historial

    # Genera la respuesta utilizando el servicio de Ollama
    # y transmite progresivamente los fragmentos al cliente.
    def transmitir_respuesta():

        # Acumula los fragmentos para guardar
        # la respuesta completa al finalizar.
        respuesta_completa = ""

        try:
            # Solicita la generación al servicio de Ollama.
            for contenido in generar_respuesta_ollama(messages):

                if contenido:
                    # Acumula el fragmento.
                    respuesta_completa += contenido

                    # Envía inmediatamente el fragmento
                    # al cliente mediante streaming.
                    yield contenido

        except OllamaServiceError as e:
            # Registra el error sin guardar una respuesta parcial.
            print(f"Error durante la generación con Ollama: {e}")
            return

        # Guarda la respuesta solamente si la generación
        # terminó correctamente y realmente produjo contenido.
        if respuesta_completa:
            agregar_mensaje(
                request.session_id,
                {
                    "role": "assistant",
                    "content": respuesta_completa,
                },
            )

    # Devuelve la respuesta como un flujo de texto.
    return StreamingResponse(
        transmitir_respuesta(),
        media_type="text/plain",
    )
