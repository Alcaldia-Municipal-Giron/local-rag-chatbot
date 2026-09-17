from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader


# ---------------------------------------------------------
# Extrae texto de archivos TXT.
# ---------------------------------------------------------
def extract_txt(file_path: Path) -> str:
    with file_path.open("r", encoding="utf-8") as file:
        return file.read()


# ---------------------------------------------------------
# Extrae texto de todas las páginas de un PDF.
# ---------------------------------------------------------
def extract_pdf(file_path: Path) -> str:
    reader = PdfReader(file_path)

    text_parts = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            text_parts.append(text)

    return "\n".join(text_parts)


# ---------------------------------------------------------
# Convierte una tabla de Word en texto.
#
# Se conserva el contenido de la tabla porque posteriormente
# también será utilizado por el sistema RAG.
# ---------------------------------------------------------
def extract_table_text(table: Table) -> str:
    rows = []

    for row in table.rows:
        cells = []

        for cell in row.cells:
            cell_text = " ".join(cell.text.split())

            if cell_text:
                cells.append(cell_text)

        if cells:
            rows.append(" | ".join(cells))

    if not rows:
        return ""

    return "[TABLA]\n" + "\n".join(rows)


# ---------------------------------------------------------
# Recorre los elementos de un documento DOCX respetando
# el orden original entre párrafos y tablas.
# ---------------------------------------------------------
def iter_block_items(document):
    body = document.element.body

    for element in body.iterchildren():

        if element.tag.endswith("}p"):
            yield Paragraph(element, document)

        elif element.tag.endswith("}tbl"):
            yield Table(element, document)


# ---------------------------------------------------------
# Detecta los campos automáticos de Word utilizados para
# generar índices o tablas de contenido.
#
# Ejemplo:
# TOC \o "1-3"
# ---------------------------------------------------------
def is_word_toc(paragraph: Paragraph) -> bool:
    for instr_text in paragraph._p.xpath(".//w:instrText"):

        if instr_text.text and "TOC" in instr_text.text.upper():
            return True

    return False


# ---------------------------------------------------------
# Detecta captions de Word.
#
# Los captions de figuras y tablas normalmente utilizan
# el estilo "Caption".
# ---------------------------------------------------------
def is_caption(paragraph: Paragraph) -> bool:
    style_name = paragraph.style.name.strip().lower()

    return style_name == "caption"


# ---------------------------------------------------------
# Detecta campos SEQ utilizados por Word para numerar
# automáticamente figuras y tablas.
#
# Ejemplo:
# SEQ Figura \* ARABIC
# ---------------------------------------------------------
def has_sequence_field(paragraph: Paragraph) -> bool:
    for instr_text in paragraph._p.xpath(".//w:instrText"):

        if instr_text.text and "SEQ" in instr_text.text.upper():
            return True

    return False


# ---------------------------------------------------------
# Detecta si un párrafo contiene una imagen o dibujo.
#
# Actualmente las imágenes se omiten del texto porque serán
# procesadas posteriormente mediante OCR.
# ---------------------------------------------------------
def has_image(paragraph: Paragraph) -> bool:
    drawings = paragraph._p.xpath(".//w:drawing")

    return len(drawings) > 0


# ---------------------------------------------------------
# Detecta párrafos que utilizan explícitamente un estilo
# destinado a notas.
# ---------------------------------------------------------
def is_note(paragraph: Paragraph) -> bool:
    style_name = paragraph.style.name.strip().lower()

    note_styles = {
        "note",
        "nota",
    }

    return style_name in note_styles


# ---------------------------------------------------------
# Detecta una nota asociada a una figura o tabla.
#
# No eliminamos cualquier párrafo que comience con "Nota".
# Solamente se considera asociada cuando cumple las
# condiciones utilizadas por nuestros documentos.
# ---------------------------------------------------------
def is_associated_note(paragraph: Paragraph) -> bool:

    if is_note(paragraph):
        return True

    style_name = paragraph.style.name.strip().lower()

    if style_name != "normal":
        return False

    text = paragraph.text.strip()

    if not text:
        return False

    return text.lower().startswith("nota")


# ---------------------------------------------------------
# Extrae el contenido de un documento DOCX.
#
# Se conserva:
# - Texto normal
# - Encabezados
# - Tablas
#
# Se excluye:
# - TOC automático
# - Captions de figuras
# - Captions de tablas
# - Imágenes por ahora
# - Notas asociadas a figuras/tablas
# ---------------------------------------------------------
def extract_docx(file_path: Path) -> str:
    document = Document(file_path)

    # Convertimos los bloques a una lista para poder
    # consultar el bloque siguiente.
    blocks = list(iter_block_items(document))

    text_parts = []

    # Indica que el siguiente párrafo puede ser una nota
    # asociada al elemento anterior.
    skip_next_note = False

    for index, block in enumerate(blocks):

        # -------------------------------------------------
        # Procesamiento de párrafos.
        # -------------------------------------------------
        if isinstance(block, Paragraph):

            # Ignoramos los TOC automáticos de Word.
            if is_word_toc(block):
                continue

            # -------------------------------------------------
            # Captions de figuras o tablas.
            #
            # Si el siguiente bloque es una imagen, sabemos
            # que probablemente tenemos:
            #
            # CAPTION → IMAGEN → NOTA
            # -------------------------------------------------
            if is_caption(block) or has_sequence_field(block):

                if index + 1 < len(blocks):

                    next_block = blocks[index + 1]

                    if (
                        isinstance(next_block, Paragraph)
                        and has_image(next_block)
                    ):
                        skip_next_note = True

                continue

            # -------------------------------------------------
            # Las imágenes se omiten temporalmente.
            #
            # Más adelante implementaremos OCR.
            # -------------------------------------------------
            if has_image(block):

                continue

            # -------------------------------------------------
            # Si acabamos de procesar una figura y encontramos
            # su nota asociada, también la omitimos.
            # -------------------------------------------------
            if skip_next_note:

                if is_associated_note(block):
                    skip_next_note = False
                    continue

                skip_next_note = False

            # -------------------------------------------------
            # Texto normal del párrafo.
            # -------------------------------------------------
            text = block.text.strip()

            if text:
                text_parts.append(text)

        # -------------------------------------------------
        # Procesamiento de tablas.
        # -------------------------------------------------
        elif isinstance(block, Table):

            table_text = extract_table_text(block)

            if table_text:
                text_parts.append(table_text)

            # Una nota inmediatamente relacionada con la tabla
            # podrá ser ignorada en el siguiente párrafo.
            skip_next_note = True

    return "\n\n".join(text_parts)


# ---------------------------------------------------------
# Selecciona automáticamente el extractor según la
# extensión del archivo.
# ---------------------------------------------------------
def extract_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension in {".txt", ".md"}:
        return extract_txt(file_path)

    if extension == ".pdf":
        return extract_pdf(file_path)

    if extension == ".docx":
        return extract_docx(file_path)

    raise ValueError(
        f"Formato de archivo no soportado: {extension}"
    )
    
# ---------------------------------------------------------
# PRUEBA MANUAL
#
# Permite ejecutar directamente este archivo para visualizar
# el resultado del extractor y de nuestro chunker.
#
# Esto no forma parte del funcionamiento normal de la
# aplicación; sirve para inspeccionar el procesamiento.
# ---------------------------------------------------------
if __name__ == "__main__":

    from app.ingestion.text_chunker import (
        split_into_paragraphs,
        build_chunks,
    )

    file_path = Path(
        "data/documents/Manual_Usuario_turismo_Administrativo.docx"
    )

    print("=" * 80)
    print("PRUEBA DE EXTRACCIÓN Y CHUNKING")
    print("=" * 80)

    # -----------------------------------------------------
    # Extraemos el texto utilizando nuestra función real.
    # -----------------------------------------------------
    text = extract_text(file_path)

    print("\n1. EXTRACCIÓN")
    print("-" * 80)
    print(f"Archivo: {file_path}")
    print(f"Caracteres: {len(text)}")
    print(f"Palabras: {len(text.split())}")

    # -----------------------------------------------------
    # Convertimos el texto extraído en párrafos.
    # -----------------------------------------------------
    paragraphs = split_into_paragraphs(text)

    print("\n2. PÁRRAFOS")
    print("-" * 80)
    print(f"Cantidad de párrafos: {len(paragraphs)}")

    # -----------------------------------------------------
    # Construimos los chunks utilizando nuestro chunker
    # definitivo.
    # -----------------------------------------------------
    chunks = build_chunks(paragraphs)

    print("\n3. CHUNKS")
    print("-" * 80)
    print(f"Cantidad de chunks: {len(chunks)}")

    # -----------------------------------------------------
    # Mostramos todos los chunks.
    # -----------------------------------------------------
    print("\n4. CONTENIDO DE LOS CHUNKS")
    print("-" * 80)

    for index, chunk in enumerate(chunks, start=1):

        print("\n" + "=" * 80)
        print(f"CHUNK {index}")
        print("=" * 80)

        print(chunk)

        print("\n" + "-" * 80)
        print(f"PALABRAS: {len(chunk.split())}")

    print("\n" + "=" * 80)
    print("PRUEBA FINALIZADA")
    print("=" * 80)