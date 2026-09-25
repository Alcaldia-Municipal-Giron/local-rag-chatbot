from app.rag.embedding_service import generar_embedding
from app.rag.vector_store import (
    add_chunks,
    search,
    get_collection_count
)


# Genera un embedding de prueba utilizando BGE-M3.
texto = "Recuperar contraseña mediante código de verificación"
embedding = generar_embedding(texto)


# Guarda un único chunk de prueba en ChromaDB.
add_chunks(
    ids=["TEST_01"],
    texts=[texto],
    embeddings=[embedding.tolist()],
    metadatas=[
        {
            "documento": "documento_prueba.txt"
        }
    ]
)


# Comprueba cuántos registros existen en la colección.
print("Cantidad de registros:", get_collection_count())


# Busca el chunk utilizando el mismo embedding.
resultados = search(
    query_embedding=embedding.tolist(),
    top_k=1
)


# Muestra el resultado recuperado.
print("ID recuperado:", resultados["ids"][0][0])
print("Texto recuperado:", resultados["documents"][0][0])
print("Distancia:", resultados["distances"][0][0])