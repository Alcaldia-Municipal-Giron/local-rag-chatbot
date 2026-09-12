# Importamos FastApi
from fastapi import FastAPI

# Crea la instancia principal de la aplicación FastAPI.
app = FastAPI(
    title="Local RAG Chatbot",
    description="API para un chatbot de IA con RAG ejecutado localmente.",
    version="0.1.0",
)

# Creamos un endpoint de prueba
@app.get("/")
def inicio():
    return {"message": "Hola desde nuestro RAG"}

# Verifica que la API esté funcionando correctamente.
@app.get("/health")
def health():
    return {"status": "ok"}