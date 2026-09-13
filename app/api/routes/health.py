from fastapi import APIRouter


# Crea un router para agrupar los endpoints relacionados con el estado de la API.
router = APIRouter()


# Verifica que la API esté funcionando correctamente.
@router.get("/health")
def health():
    return {"status": "ok"}