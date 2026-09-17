from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


FILE_PATH = Path(
    "data/documents/Manual_Usuario_Artista_Turismo_Giron.docx"
)


def inspect_tables(file_path: Path) -> None:
    document = Document(file_path)
    body = document.element.body

    elements = list(body.iterchildren())

    print("=" * 80)
    print("INSPECCIÓN DE TABLAS Y SU CONTEXTO")
    print("=" * 80)

    for index, element in enumerate(elements):

        # ---------------------------------------------------------
        # Detectamos únicamente las tablas del documento.
        # ---------------------------------------------------------
        if not element.tag.endswith("}tbl"):
            continue

        table = Table(element, document)

        print(f"\n{'=' * 80}")
        print(f"TABLA EN ELEMENTO #{index}")
        print(f"{'=' * 80}")

        print(f"FILAS: {len(table.rows)}")
        print(f"COLUMNAS: {len(table.columns)}")

        # ---------------------------------------------------------
        # Mostramos el elemento inmediatamente anterior.
        # Esto permite comprobar si es un caption de tabla.
        # ---------------------------------------------------------
        if index > 0:

            previous_element = elements[index - 1]

            if previous_element.tag.endswith("}p"):

                previous_paragraph = Paragraph(
                    previous_element,
                    document
                )

                print("\n--- ELEMENTO ANTERIOR ---")
                print("TIPO: PÁRRAFO")
                print(
                    f"ESTILO: {previous_paragraph.style.name}"
                )
                print(
                    f"TEXTO: {previous_paragraph.text!r}"
                )

                # Campos internos de Word.
                field_codes = previous_paragraph._p.xpath(
                    ".//w:instrText"
                )

                print(
                    f"CAMPOS DE WORD: {len(field_codes)}"
                )

                for field in field_codes:
                    print(
                        f"CAMPO: {field.text!r}"
                    )

        # ---------------------------------------------------------
        # Mostramos las primeras filas de la tabla.
        # ---------------------------------------------------------
        print("\n--- CONTENIDO DE LA TABLA ---")

        for row_index, row in enumerate(table.rows[:5]):

            cells = [
                cell.text.strip()
                for cell in row.cells
            ]

            print(
                f"FILA {row_index}: {cells}"
            )

        # ---------------------------------------------------------
        # Mostramos el elemento inmediatamente posterior.
        # Esto permite comprobar si existe una nota asociada.
        # ---------------------------------------------------------
        if index + 1 < len(elements):

            next_element = elements[index + 1]

            if next_element.tag.endswith("}p"):

                next_paragraph = Paragraph(
                    next_element,
                    document
                )

                print("\n--- ELEMENTO POSTERIOR ---")
                print("TIPO: PÁRRAFO")
                print(
                    f"ESTILO: {next_paragraph.style.name}"
                )
                print(
                    f"TEXTO: {next_paragraph.text!r}"
                )

        print()


if __name__ == "__main__":
    inspect_tables(FILE_PATH)