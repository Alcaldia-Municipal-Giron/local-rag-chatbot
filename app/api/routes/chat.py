
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.database import DatabaseConnectionError
from app.services.chat_service import preparar_stream_chat


# Define la estructura de los datos que el cliente debe enviar al endpoint.
class ChatRequest(BaseModel):
    session_id: str
    message: str


# Crea un router para agrupar los endpoints relacionados con el chatbot.
router = APIRouter()


# Recibe la pregunta, delega el procesamiento al servicio y devuelve
# la respuesta mediante el flujo SSE utilizado por el frontend.
@router.post("/chat")
def chat(request: ChatRequest):
    try:
        # Prepara el flujo de respuesta y ejecuta las operaciones
        # previas a la transmisión, incluida la recuperación RAG.
        flujo_respuesta = preparar_stream_chat(
            session_id=request.session_id,
            mensaje=request.message,
        )

    except DatabaseConnectionError as e:
        # Mantiene el código HTTP 503 cuando falla la conexión
        # con la base de datos durante la preparación del chat.
        raise HTTPException(
            status_code=503,
            detail=str(e),
        ) from e

    # Conserva el contrato SSE que consume el frontend.
    return StreamingResponse(
        flujo_respuesta,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
