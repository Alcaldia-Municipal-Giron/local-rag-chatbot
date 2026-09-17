from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


# Ruta del documento DOCX que vamos a inspeccionar.
FILE_PATH = Path(
    "data/documents/Manual_Usuario_Artista_Turismo_Giron.docx"
)


# Muestra información estructural de cada elemento del documento
# manteniendo el orden en el que aparece dentro del DOCX.
def inspect_document(file_path: Path) -> None:
    document = Document(file_path)

    body = document.element.body

    print("=" * 80)
    print("INSPECCIÓN ESTRUCTURAL DEL DOCUMENTO DOCX")
    print("=" * 80)

    for index, element in enumerate(body.iterchildren()):
        print(f"\nELEMENTO #{index}")
        print("-" * 80)

        # Identificamos el tipo de elemento XML.
        print(f"XML: {element.tag}")

        # Convertimos el elemento XML a un objeto de python-docx
        # cuando corresponde a un párrafo o una tabla.
        if element.tag.endswith("}p"):
            paragraph = Paragraph(element, document)

            print("TIPO: PÁRRAFO")
            print(f"ESTILO: {paragraph.style.name}")
            print(f"TEXTO: {paragraph.text!r}")

            # Revisamos si el párrafo contiene dibujos o imágenes.
            drawings = element.xpath(".//w:drawing")

            print(f"DIBUJOS/IMÁGENES: {len(drawings)}")

            # Revisamos si el párrafo contiene campos de Word.
            field_codes = element.xpath(".//w:instrText")

            print(f"CAMPOS DE WORD: {len(field_codes)}")

        elif element.tag.endswith("}tbl"):
            table = Table(element, document)

            print("TIPO: TABLA")
            print(f"FILAS: {len(table.rows)}")
            print(f"COLUMNAS: {len(table.columns)}")

            # Mostramos una pequeña muestra del contenido de la tabla.
            for row_index, row in enumerate(table.rows[:3]):
                cells = [cell.text.strip() for cell in row.cells]

                print(f"FILA {row_index}: {cells}")

        else:
            print("TIPO: OTRO ELEMENTO")

    print("\n" + "=" * 80)
    print("FIN DE LA INSPECCIÓN")
    print("=" * 80)


# Ejecutamos la inspección del documento.
if __name__ == "__main__":
    inspect_document(FILE_PATH)