from app.db.database import get_connection


# ---------------------------------------------------------
# Devuelve la cantidad total de chunks almacenados.
# ---------------------------------------------------------

def get_collection_count():
    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) FROM chunks"
            )

            return cursor.fetchone()[0]


# ---------------------------------------------------------
# Registra un documento en PostgreSQL y devuelve su ID.
# ---------------------------------------------------------

def add_document(
    filename,
    sha256,
    size_bytes,
    content_type
):
    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO documents (
                    filename,
                    sha256,
                    size_bytes,
                    content_type
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    filename,
                    sha256,
                    size_bytes,
                    content_type
                )
            )

            document_id = cursor.fetchone()[0]

        connection.commit()

    return document_id


# ---------------------------------------------------------
# Elimina un documento y todos sus chunks asociados
# de PostgreSQL.
# ---------------------------------------------------------

def delete_document(document_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM documents
                WHERE id = %s
                """,
                (document_id,)
            )

        connection.commit()


# ---------------------------------------------------------
# Guarda los chunks de un documento junto con sus embeddings.
# ---------------------------------------------------------

def add_chunks(document_id, texts, embeddings):
    with get_connection() as connection:
        with connection.cursor() as cursor:

            for chunk_index, (text, embedding) in enumerate(
                zip(texts, embeddings)
            ):
                vector = "[" + ",".join(map(str, embedding)) + "]"

                cursor.execute(
                    """
                    INSERT INTO chunks (
                        document_id,
                        chunk_index,
                        text,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (
                        document_id,
                        chunk_index,
                        text,
                        vector
                    )
                )

        connection.commit()


# ---------------------------------------------------------
# Guarda un documento y todos sus chunks en una sola
# transacción de PostgreSQL.
# ---------------------------------------------------------

def save_document_with_chunks(
    filename,
    sha256,
    size_bytes,
    content_type,
    texts,
    embeddings
):
    if len(texts) != len(embeddings):
        raise ValueError(
            "La cantidad de chunks y embeddings debe coincidir."
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Registra el documento y obtiene su ID.
            cursor.execute(
                """
                INSERT INTO documents (
                    filename,
                    sha256,
                    size_bytes,
                    content_type
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    filename,
                    sha256,
                    size_bytes,
                    content_type
                )
            )

            document_id = cursor.fetchone()[0]

            # Guarda todos los chunks y sus embeddings.
            for chunk_index, (text, embedding) in enumerate(
                zip(texts, embeddings)
            ):
                vector = "[" + ",".join(
                    map(str, embedding)
                ) + "]"

                cursor.execute(
                    """
                    INSERT INTO chunks (
                        document_id,
                        chunk_index,
                        text,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (
                        document_id,
                        chunk_index,
                        text,
                        vector
                    )
                )

        # Confirma documento + chunks como una sola operación.
        connection.commit()

    return document_id


# ---------------------------------------------------------
# Busca los chunks más similares utilizando distancia coseno.
# ---------------------------------------------------------

def search(query_embedding, top_k=5):
    vector = "[" + ",".join(map(str, query_embedding)) + "]"

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    chunk_index,
                    text,
                    embedding <=> %s::vector AS distance
                FROM chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    vector,
                    vector,
                    top_k
                )
            )

            rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "chunk_index": row[1],
            "text": row[2],
            "distance": float(row[3])
        }
        for row in rows
    ]