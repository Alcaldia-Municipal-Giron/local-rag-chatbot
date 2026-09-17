from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader


# Extrae el contenido de un archivo TXT o Markdown como texto plano.
def extract_txt(file_path: Path) -> str:
    with file_path.open("r", encoding="utf-8") as file:
        return file.read()


# Extrae el texto de todas las páginas de un archivo PDF.
def extract_pdf(file_path: Path) -> str:
    reader = PdfReader(file_path)

    text_parts = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            text_parts.append(text)

    return "\n".join(text_parts)


# Convierte una tabla de Word en texto estructurado,
# conservando la información de sus filas y columnas.
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


# Recorre los elementos de un documento DOCX respetando
# el orden original entre párrafos y tablas.
def iter_block_items(document):
    body = document.element.body

    for element in body.iterchildren():
        if element.tag.endswith("}p"):
            yield Paragraph(element, document)

        elif element.tag.endswith("}tbl"):
            yield Table(element, document)


# Detecta si un párrafo contiene un campo TOC de Word.
# Los campos TOC corresponden a índices automáticos como
# tablas de contenido, índices de figuras e índices de tablas.
def is_word_toc(paragraph: Paragraph) -> bool:
    for instr_text in paragraph._p.xpath(".//w:instrText"):
        if instr_text.text and "TOC" in instr_text.text.upper():
            return True

    return False


# Extrae el contenido textual de un documento DOCX,
# conservando el orden entre párrafos y tablas.
def extract_docx(file_path: Path) -> str:
    document = Document(file_path)

    text_parts = []

    for block in iter_block_items(document):

        # Procesamos los párrafos de Word.
        if isinstance(block, Paragraph):

            # Los índices automáticos de Word contienen campos TOC.
            # Se excluyen porque funcionan como navegación del documento
            # y no aportan contenido semántico al RAG.
            if is_word_toc(block):
                continue

            text = block.text.strip()

            if text:
                text_parts.append(text)

        # Procesamos las tablas de Word.
        elif isinstance(block, Table):
            table_text = extract_table_text(block)

            if table_text:
                text_parts.append(table_text)

    return "\n\n".join(text_parts)


# Selecciona el extractor correspondiente según
# la extensión del archivo recibido.
def extract_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension in {".txt", ".md"}:
        return extract_txt(file_path)

    if extension == ".pdf":
        return extract_pdf(file_path)

    if extension == ".docx":
        return extract_docx(file_path)

    raise ValueError(f"Formato de archivo no soportado: {extension}")
 