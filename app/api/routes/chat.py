from fastapi import APIRouter
from pydantic import BaseModel # Una petición para /chat debe contener un campo message de tipo texto.


# Define la estructura de los datos que el cliente debe enviar al endpoint de chat.
class ChatRequest(BaseModel):
    message: str

# Define la estructura de la respuesta que devuelve el endpoint de chat.
class ChatResponse(BaseModel):
    answer: str

# Crea un router para agrupar los endpoints relacionados con el chatbot.
router = APIRouter()


# Recibe una pregunta del usuario y devuelve una respuesta de prueba.
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return {
        "answer": f"Recibí tu pregunta: {request.message}"
    }