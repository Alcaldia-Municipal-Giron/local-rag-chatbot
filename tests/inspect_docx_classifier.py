from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph


FILE_PATHS = [
    Path(
        "data/documents/Manual_Usuario_Artista_Turismo_Giron.docx"
    ),
    Path(
        "data/documents/Plantilla - Informe - Corte 2 1.docx"
    ),
]


def has_image(paragraph: Paragraph) -> bool:
    """
    Determina si el párrafo contiene una imagen de Word.
    """
    return bool(
        paragraph._p.xpath(".//w:drawing")
    )


def is_caption(paragraph: Paragraph) -> bool:
    """
    Detecta captions mediante el estilo estructural de Word.
    """
    return paragraph.style.name.lower() == "caption"


def inspect_notes(file_path: Path) -> None:
    document = Document(file_path)
    elements = list(
        document.element.body.iterchildren()
    )

    print("\n")
    print("=" * 90)
    print(f"DOCUMENTO: {file_path.name}")
    print("=" * 90)

    # ---------------------------------------------------------
    # Buscamos la secuencia:
    #
    # CAPTION
    #   ↓
    # IMAGEN
    #   ↓
    # PÁRRAFO
    #
    # para inspeccionar el posible párrafo de nota.
    # ---------------------------------------------------------
    for index in range(len(elements) - 2):

        current = elements[index]
        next_element = elements[index + 1]
        after_image = elements[index + 2]

        if not current.tag.endswith("}p"):
            continue

        if not next_element.tag.endswith("}p"):
            continue

        if not after_image.tag.endswith("}p"):
            continue

        caption = Paragraph(
            current,
            document
        )

        image_paragraph = Paragraph(
            next_element,
            document
        )

        possible_note = Paragraph(
            after_image,
            document
        )

        # -----------------------------------------------------
        # Confirmamos que tenemos:
        #
        # Caption → Imagen → Párrafo
        # -----------------------------------------------------
        if not is_caption(caption):
            continue

        if not has_image(image_paragraph):
            continue

        print("\n" + "-" * 90)

        print(f"ELEMENTO CAPTION: #{index}")
        print(f"ESTILO: {caption.style.name}")
        print(f"TEXTO: {caption.text!r}")

        print(f"\nELEMENTO IMAGEN: #{index + 1}")
        print(f"ESTILO: {image_paragraph.style.name}")
        print(f"TEXTO: {image_paragraph.text!r}")

        print(f"\nPOSIBLE NOTA: #{index + 2}")
        print(f"ESTILO: {possible_note.style.name}")
        print(f"TEXTO: {possible_note.text!r}")

        # -----------------------------------------------------
        # Mostramos las propiedades estructurales del posible
        # párrafo de nota.
        # -----------------------------------------------------
        print(
            f"Tiene imagen: {has_image(possible_note)}"
        )

        field_codes = possible_note._p.xpath(
            ".//w:instrText"
        )

        print(
            f"Campos Word: {len(field_codes)}"
        )

        # -----------------------------------------------------
        # Mostramos solamente el XML de propiedades del
        # párrafo (<w:pPr>), no todo el XML.
        #
        # Esto evita llenar la consola.
        # -----------------------------------------------------
        paragraph_properties = possible_note._p.xpath(
            "./w:pPr"
        )

        if paragraph_properties:
            print("\nPROPIEDADES XML DEL PÁRRAFO:")

            print(
                paragraph_properties[0].xml
            )
        else:
            print(
                "\nPROPIEDADES XML DEL PÁRRAFO: "
                "NINGUNA"
            )


if __name__ == "__main__":

    for file_path in FILE_PATHS:

        if file_path.exists():
            inspect_notes(file_path)

        else:
            print(
                f"\nNO ENCONTRADO: {file_path}"
            )