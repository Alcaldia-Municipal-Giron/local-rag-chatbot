# ---------------------------------------------------------
# Configuración principal del chunker.
#
# Cada chunk intenta tener como máximo 500 palabras.
# Se utiliza un solapamiento de 50 palabras para conservar
# contexto entre chunks consecutivos.
# ---------------------------------------------------------
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


# ---------------------------------------------------------
# Divide el texto en párrafos.
#
# Se eliminan líneas vacías y espacios innecesarios.
# ---------------------------------------------------------
def split_into_paragraphs(text: str) -> list[str]:
    paragraphs = []

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()

        if paragraph:
            paragraphs.append(paragraph)

    return paragraphs


# ---------------------------------------------------------
# Divide un párrafo que supera CHUNK_SIZE.
#
# En este caso no podemos conservar el párrafo completo,
# por lo que se divide directamente por palabras.
# ---------------------------------------------------------
def split_long_paragraph(paragraph: str) -> list[str]:
    words = paragraph.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + CHUNK_SIZE

        chunk_words = words[start:end]

        chunks.append(" ".join(chunk_words))

        start = end - CHUNK_OVERLAP

    return chunks


# ---------------------------------------------------------
# Construye los chunks finales.
#
# La estrategia intenta conservar párrafos completos.
# Cuando un nuevo párrafo supera el límite, se crea un
# nuevo chunk utilizando algunos párrafos anteriores como
# contexto.
# ---------------------------------------------------------
def build_chunks(paragraphs: list[str]) -> list[str]:
    chunks = []

    current_paragraphs = []
    current_word_count = 0

    for paragraph in paragraphs:

        paragraph_word_count = len(paragraph.split())

        # -------------------------------------------------
        # Si un párrafo individual supera CHUNK_SIZE,
        # debemos dividirlo directamente.
        # -------------------------------------------------
        if paragraph_word_count > CHUNK_SIZE:

            if current_paragraphs:
                chunks.append(
                    "\n".join(current_paragraphs)
                )

            long_paragraph_chunks = split_long_paragraph(
                paragraph
            )

            chunks.extend(long_paragraph_chunks)

            current_paragraphs = []
            current_word_count = 0

            continue

        # -------------------------------------------------
        # Intentamos agregar el párrafo al chunk actual.
        # -------------------------------------------------
        if (
            current_word_count + paragraph_word_count
            <= CHUNK_SIZE
        ):

            current_paragraphs.append(paragraph)

            current_word_count += paragraph_word_count

        else:

            # -------------------------------------------------
            # Guardamos el chunk actual.
            # -------------------------------------------------
            if current_paragraphs:
                chunks.append(
                    "\n".join(current_paragraphs)
                )

            # -------------------------------------------------
            # Buscamos párrafos anteriores para formar
            # el overlap.
            # -------------------------------------------------
            overlap_paragraphs = []
            overlap_word_count = 0

            for previous_paragraph in reversed(
                current_paragraphs
            ):

                previous_word_count = len(
                    previous_paragraph.split()
                )

                if (
                    overlap_word_count
                    + previous_word_count
                    > CHUNK_OVERLAP
                ):
                    break

                overlap_paragraphs.insert(
                    0,
                    previous_paragraph,
                )

                overlap_word_count += previous_word_count

            # -------------------------------------------------
            # El nuevo chunk comienza con el contexto
            # anterior y continúa con el nuevo párrafo.
            # -------------------------------------------------
            current_paragraphs = (
                overlap_paragraphs
                + [paragraph]
            )

            current_word_count = (
                overlap_word_count
                + paragraph_word_count
            )

    # ---------------------------------------------------------
    # Guardamos el último chunk.
    # ---------------------------------------------------------
    if current_paragraphs:
        chunks.append(
            "\n".join(current_paragraphs)
        )

    return chunks