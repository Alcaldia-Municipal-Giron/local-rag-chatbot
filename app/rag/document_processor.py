from pathlib import Path

from app.ingestion.text_extractor import extract_text
from app.ingestion.text_chunker import (
    split_into_paragraphs,
    build_chunks,
)
from app.rag.embedding_service import generar_embedding


# ---------------------------------------------------------
# Procesa un documento y genera sus chunks junto con
# sus embeddings.
#
# Flujo:
#
# 1. Extrae el texto.
# 2. Divide el texto en párrafos.
# 3. Construye los chunks.
# 4. Genera un embedding BGE-M3 para cada chunk.
#
# Todavía no guarda información en PostgreSQL.
# ---------------------------------------------------------

def process_document(file_path: Path):

    # Extrae el texto según el tipo de documento.

    text = extract_text(file_path)

    # Divide el texto extraído en párrafos.

    paragraphs = split_into_paragraphs(text)

    # Construye los chunks utilizando la estrategia
    # configurada en text_chunker.py.

    chunks = build_chunks(paragraphs)

    # Genera un embedding para cada chunk.

    embeddings = [
        generar_embedding(chunk).tolist()
        for chunk in chunks
    ]

    return chunks, embeddings