from app.rag.embedding_service import generar_embedding
from app.rag.vector_store import search


def recuperar_contexto(pregunta: str, top_k: int = 5):
    embedding = generar_embedding(pregunta)

    resultados = search(
        embedding,
        top_k=top_k
    )

    return resultados

def es_contexto_relevante(resultados, max_distance=0.50):
    """
    Determina si el resultado más relevante supera el umbral
    de distancia permitido.
    """
    if not resultados:
        return False

    return resultados[0]["distance"] <= max_distance