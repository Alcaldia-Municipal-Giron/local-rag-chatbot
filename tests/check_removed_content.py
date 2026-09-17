from pathlib import Path

from app.ingestion.text_extractor import extract_text
from app.ingestion.text_chunker import (
    split_into_paragraphs,
    build_chunks,
)


FILE_PATH = Path(
    "data/documents/Manual_Usuario_Artista_Turismo_Giron.docx"
)


def main():
    text = extract_text(FILE_PATH)

    paragraphs = split_into_paragraphs(text)
    chunks = build_chunks(paragraphs)

    print("=" * 80)
    print("VERIFICACIÓN DE CAPTIONS Y NOTAS")
    print("=" * 80)

    found = False

    for index, chunk in enumerate(chunks, start=1):

        for line in chunk.splitlines():

            if (
                line.strip().startswith("Figura ")
                or line.strip().startswith("Nota.")
            ):
                print(
                    f"Chunk {index}: {line.strip()}"
                )
                found = True

    print("\n" + "=" * 80)

    if found:
        print("⚠️ TODAVÍA SE ENCONTRARON CAPTIONS/NOTAS")
    else:
        print("✅ NO SE ENCONTRARON CAPTIONS/NOTAS DE FIGURAS")

    print("=" * 80)


if __name__ == "__main__":
    main()