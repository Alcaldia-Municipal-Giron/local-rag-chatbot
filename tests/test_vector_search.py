from app.rag.embedding_service import generar_embedding
from app.rag.vector_store import search


# Genera el embedding de la consulta.
embedding = generar_embedding(
    "¿Cómo se utiliza el sistema Gaia?"
)

# Busca los 3 chunks más similares.
resultados = search(
    embedding,
    top_k=3
)

print("Resultados:", len(resultados))

for resultado in resultados:
    print(
        f"Chunk {resultado['chunk_index']} "
        f"| distancia={resultado['distance']:.4f}"
    )