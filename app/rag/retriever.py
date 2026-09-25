from app.rag.embedding_service import generar_embedding
from app.rag.vector_store import search


def recuperar_contexto(pregunta: str, top_k: int = 5):
    embedding = generar_embedding(pregunta)

    resultados = search(
        embedding,
        top_k=top_k
    )

    return resultados