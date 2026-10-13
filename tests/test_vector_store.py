
from uuid import uuid4

from app.rag.embedding_service import generar_embedding
from app.rag.vector_store import (
    add_document,
    add_chunks,
    search,
    get_collection_count,
    delete_document,
)


# Genera un documento de prueba único para evitar conflictos con
# documentos existentes y facilitar la limpieza posterior.
sufijo_prueba = uuid4().hex[:12]
nombre_documento = f"test_vector_store_{sufijo_prueba}.txt"
texto = "Recuperar contraseña mediante código de verificación"

document_id = None

try:
    # Genera el embedding utilizando el modelo BGE-M3.
    embedding = generar_embedding(texto)

    # Registra el documento padre, necesario para relacionar sus chunks.
    document_id = add_document(
        filename=nombre_documento,
        sha256=uuid4().hex,
        size_bytes=len(texto.encode("utf-8")),
        content_type="text/plain",
    )

    # Guarda el fragmento asociado al documento en PostgreSQL.
    add_chunks(
        document_id=document_id,
        texts=[texto],
        embeddings=[embedding.tolist()],
    )

    # Comprueba que existen registros almacenados en la tabla chunks.
    cantidad = get_collection_count()
    print("Cantidad total de chunks:", cantidad)

    # Busca el fragmento usando el mismo embedding de la inserción.
    resultados = search(
        query_embedding=embedding.tolist(),
        top_k=1,
    )

    # Verifica que la búsqueda haya recuperado el fragmento esperado.
    assert resultados, "No se recuperó ningún chunk."
    assert resultados[0]["text"] == texto, (
        "El texto recuperado no coincide con el texto insertado."
    )

    print("ID recuperado:", resultados[0]["id"])
    print("Texto recuperado:", resultados[0]["text"])
    print("Distancia:", resultados[0]["distance"])

finally:
    # Elimina el documento de prueba y sus chunks asociados,
    # incluso si alguna comprobación falla.
    if document_id is not None:
        delete_document(document_id)
