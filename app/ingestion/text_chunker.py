# Cantidad aproximada de palabras que tendrá cada chunk.
CHUNK_SIZE = 500

# Cantidad de palabras que se reutilizarán entre chunks consecutivos.
CHUNK_OVERLAP = 50


# Divide el texto en párrafos, eliminando líneas vacías y espacios innecesarios.
def split_into_paragraphs(text: str) -> list[str]:
    paragraphs = []

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()

        if paragraph:
            paragraphs.append(paragraph)

    return paragraphs


# Divide un párrafo que supera CHUNK_SIZE en fragmentos de palabras,
# conservando un overlap entre los fragmentos.
def split_long_paragraph(paragraph: str) -> list[str]:
    words = paragraph.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]

        chunks.append(" ".join(chunk_words))

        # Retrocedemos CHUNK_OVERLAP palabras para conservar contexto
        # entre este fragmento y el siguiente.
        start = end - CHUNK_OVERLAP

    return chunks


# Agrupa los párrafos hasta alcanzar aproximadamente el tamaño máximo del chunk
# y conserva parte del contenido anterior para mantener el contexto entre chunks.
def build_chunks(paragraphs: list[str]) -> list[str]:
    chunks = []

    current_paragraphs = []
    current_word_count = 0

    for paragraph in paragraphs:
        paragraph_word_count = len(paragraph.split())

        # Si el párrafo supera el tamaño máximo, lo dividimos internamente.
        if paragraph_word_count > CHUNK_SIZE:
            # Guardamos el chunk actual antes de procesar el párrafo largo.
            if current_paragraphs:
                chunks.append("\n".join(current_paragraphs))

            # Dividimos el párrafo largo conservando overlap.
            long_paragraph_chunks = split_long_paragraph(paragraph)

            # Agregamos directamente los fragmentos obtenidos.
            chunks.extend(long_paragraph_chunks)

            # Reiniciamos el estado para continuar con los siguientes párrafos.
            current_paragraphs = []
            current_word_count = 0

            continue

        # Si el párrafo cabe en el chunk actual, lo agregamos.
        if current_word_count + paragraph_word_count <= CHUNK_SIZE:
            current_paragraphs.append(paragraph)
            current_word_count += paragraph_word_count

        else:
            # Guardamos el chunk actual antes de comenzar uno nuevo.
            if current_paragraphs:
                chunks.append("\n".join(current_paragraphs))

            # Conservamos los últimos párrafos necesarios para aproximarnos
            # al tamaño definido para el overlap.
            overlap_paragraphs = []
            overlap_word_count = 0

            for previous_paragraph in reversed(current_paragraphs):
                previous_word_count = len(previous_paragraph.split())

                if overlap_word_count + previous_word_count > CHUNK_OVERLAP:
                    break

                overlap_paragraphs.insert(0, previous_paragraph)
                overlap_word_count += previous_word_count

            # El nuevo chunk comienza con el contenido conservado.
            current_paragraphs = overlap_paragraphs + [paragraph]

            current_word_count = (
                overlap_word_count + paragraph_word_count
            )

    # Guardamos el último chunk pendiente.
    if current_paragraphs:
        chunks.append("\n".join(current_paragraphs))

    return chunks