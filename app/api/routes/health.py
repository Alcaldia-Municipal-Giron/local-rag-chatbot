from fastapi import APIRouter

# Crea un router para agrupar los endpoints relacionados con el estado de la API.

router = APIRouter()

# Verifica que la API esté funcionando correctamente.

@router.get("/health")
def health():
    return {"status": "ok"}


# Verifica que el modelo BGE-M3 esté cargado dentro del proceso de FastAPI.

@router.get("/health/embedding")
def health_embedding():
    from app.rag.embedding_service import model

    return {
        "model": model.model_card_data.get(
            "model_name",
            "BAAI/bge-m3"
        ),
        "embedding_dimension": model.get_sentence_embedding_dimension()
    }
