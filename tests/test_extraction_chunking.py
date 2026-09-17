from pathlib import Path

from app.ingestion.text_extractor import extract_text
from app.ingestion.text_chunker import (
    split_into_paragraphs,
    build_chunks,
)


# Documento que utilizaremos para probar el proceso completo.
FILE_PATH = Path(
    "data/documents/Manual_Usuario_Gaia_Administrativo_v2.docx"
)


def main():
    print("=" * 80)
    print("PRUEBA COMPLETA: EXTRACCIÓN + CHUNKING")
    print("=" * 80)

    # ---------------------------------------------------------
    # 1. Extraemos el contenido del documento.
    # ---------------------------------------------------------
    text = extract_text(FILE_PATH)

    print("\n1. EXTRACCIÓN")
    print("-" * 80)
    print(f"Archivo: {FILE_PATH}")
    print(f"Caracteres extraídos: {len(text)}")
    print(f"Palabras extraídas: {len(text.split())}")

    # ---------------------------------------------------------
    # 2. Convertimos el texto extraído en párrafos.
    # ---------------------------------------------------------
    paragraphs = split_into_paragraphs(text)

    print("\n2. PÁRRAFOS")
    print("-" * 80)
    print(f"Párrafos obtenidos: {len(paragraphs)}")

    # ---------------------------------------------------------
    # 3. Construimos los chunks.
    # ---------------------------------------------------------
    chunks = build_chunks(paragraphs)

    print("\n3. CHUNKS")
    print("-" * 80)
    print(f"Cantidad de chunks: {len(chunks)}")

    # ---------------------------------------------------------
    # 4. Mostramos el tamaño de cada chunk.
    # ---------------------------------------------------------
    print("\n4. PALABRAS POR CHUNK")
    print("-" * 80)

    for index, chunk in enumerate(chunks, start=1):
        word_count = len(chunk.split())

        print(
            f"Chunk {index:02d}: "
            f"{word_count} palabras"
        )

    # ---------------------------------------------------------
    # 5. Comprobamos qué chunks contienen tablas.
    # ---------------------------------------------------------
    table_chunks = [
        index
        for index, chunk in enumerate(chunks, start=1)
        if "[TABLA]" in chunk
    ]

    print("\n5. TABLAS")
    print("-" * 80)
    print(
        f"Chunks que contienen [TABLA]: "
        f"{len(table_chunks)}"
    )

    if table_chunks:
        print(f"Chunks con tablas: {table_chunks}")

    # ---------------------------------------------------------
    # 6. Mostramos TODOS los chunks.
    #
    # El documento tiene solamente 5 chunks, por lo que
    # mostramos todos para poder revisar visualmente
    # el contenido generado por nuestro chunker.
    # ---------------------------------------------------------
    print("\n6. TODOS LOS CHUNKS")
    print("-" * 80)

    for index, chunk in enumerate(chunks, start=1):

        print("\n" + "=" * 80)
        print(f"CHUNK {index}")
        print("=" * 80)

        print(chunk)

        print("\n" + "-" * 80)
        print(f"PALABRAS: {len(chunk.split())}")

    # ---------------------------------------------------------
    # 7. Comprobamos el solapamiento entre chunks consecutivos.
    #
    # Nuestro CHUNK_OVERLAP está configurado en 50 palabras.
    # Sin embargo, como el chunker respeta párrafos completos,
    # el solapamiento real puede variar.
    # ---------------------------------------------------------
    print("\n7. SOLAPAMIENTO")
    print("-" * 80)

    for index in range(len(chunks) - 1):

        current_words = chunks[index].split()
        next_words = chunks[index + 1].split()

        overlap = 0

        max_overlap = min(
            len(current_words),
            len(next_words),
        )

        for size in range(max_overlap, 0, -1):

            if current_words[-size:] == next_words[:size]:
                overlap = size
                break

        print(
            f"Chunk {index + 1:02d} → "
            f"Chunk {index + 2:02d}: "
            f"{overlap} palabras compartidas"
        )

    print("\n" + "=" * 80)
    print("PRUEBA FINALIZADA")
    print("=" * 80)


if __name__ == "__main__":
    main()