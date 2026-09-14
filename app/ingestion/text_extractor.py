from pathlib import Path

from docx import Document
from pypdf import PdfReader


# Lee un archivo de texto y devuelve todo su contenido como un string.
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


# Extrae el texto de los párrafos de un archivo DOCX.
def extract_docx(file_path: Path) -> str:
    document = Document(file_path)

    text_parts = []

    for paragraph in document.paragraphs:
        if paragraph.text:
            text_parts.append(paragraph.text)

    return "\n".join(text_parts)


# Selecciona el extractor adecuado según la extensión del archivo.
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