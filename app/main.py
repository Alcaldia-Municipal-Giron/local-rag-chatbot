from fastapi import FastAPI
# Importacion de la ruta de Health.py
from app.api.routes.health import router as health_router
# Importación de la ruta de Chat.py
from app.api.routes.chat import router as chat_router
# Importación de la ruta de Documents.py
from app.api.routes.documents import router as documents_router, initialize_metadata


# Crea la aplicación principal y configura la información básica de la API.
app = FastAPI(
    title="Local RAG Chatbot",
    description="API para un chatbot de IA con RAG ejecutado localmente.",
    version="0.1.0",
)

# Registra en la metadata los documentos que ya existen físicamente.
initialize_metadata()

# Registra las rutas relacionadas con el estado de la aplicación.
app.include_router(health_router)

# Registra las rutas relacionadas con el chatbot.
app.include_router(chat_router)

# Registra las rutas relacionadas con los documentos.
app.include_router(documents_router)

# Ruta raíz utilizada para comprobar que la API está disponible.
@app.get("/")
def inicio():
    return {"message": "Hola desde nuestro RAG"}