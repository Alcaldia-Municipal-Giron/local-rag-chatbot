
from app.rag.embedding_service import generar_embedding
from app.rag.vector_store import search


def recuperar_contexto(pregunta: str, top_k: int = 5):
    # Genera el embedding de la pregunta para realizar la búsqueda semántica.
    embedding = generar_embedding(pregunta)

    # Recupera los fragmentos más cercanos a la pregunta en PostgreSQL.
    resultados = search(
        embedding,
        top_k=top_k
    )

    # Muestra el contenido completo de cada fragmento para auditar
    # qué información está recuperando el sistema RAG.
    print("\n" + "=" * 80)
    print(f"[RETRIEVER] Pregunta: {pregunta}")
    print(f"[RETRIEVER] Total de fragmentos: {len(resultados)}")
    print("=" * 80)

    for posicion, resultado in enumerate(resultados, start=1):
        texto = resultado.get("text", "")

        print(f"\n[RETRIEVER] FRAGMENTO {posicion}")
        print(f"ID: {resultado.get('id', 'N/D')}")
        print(f"Índice del chunk: {resultado.get('chunk_index', 'N/D')}")
        print(f"Distancia: {resultado.get('distance', 'N/D')}")
        print(f"Caracteres: {len(texto)}")
        print("-" * 80)
        print(texto)
        print("=" * 80)

    return resultados

def es_contexto_relevante(resultados, max_distance=0.50):
    """
    Determina si el resultado más relevante supera el umbral
    de distancia permitido.
    """
    if not resultados:
        return False

    return resultados[0]["distance"] <= max_distance
