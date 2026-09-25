from fastapi import APIRouter, File, HTTPException, UploadFile

import hashlib
import json
import os
import tempfile
from pathlib import Path

from app.rag.document_processor import process_document
from app.rag.vector_store import (
    save_document_with_chunks,
    delete_document,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


# ---------------------------------------------------------
# Define la carpeta donde se almacenarán los documentos.
# ---------------------------------------------------------

DOCUMENTS_DIR = Path("data/documents")

DOCUMENTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ---------------------------------------------------------
# Extensiones de archivos que no permitimos subir.
# ---------------------------------------------------------

BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".scr",
    ".zip",
    ".rar",
}


# ---------------------------------------------------------
# Tamaño máximo permitido por archivo: 50 MB.
# ---------------------------------------------------------

MAX_FILE_SIZE = 50 * 1024 * 1024


# ---------------------------------------------------------
# Archivo donde se almacenan los hashes de los documentos.
# ---------------------------------------------------------

METADATA_FILE = Path(
    "data/documents_metadata.json"
)


# ---------------------------------------------------------
# Calcula el hash SHA-256 del contenido del archivo.
# ---------------------------------------------------------

async def calculate_file_hash(file: UploadFile):
    sha256 = hashlib.sha256()

    while chunk := await file.read(1024 * 1024):
        sha256.update(chunk)

    await file.seek(0)

    return sha256.hexdigest()


# ---------------------------------------------------------
# Lee la metadata de los documentos.
# ---------------------------------------------------------

def load_metadata():
    if not METADATA_FILE.exists():
        return {}

    with METADATA_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ---------------------------------------------------------
# Guarda la metadata de forma atómica.
#
# Primero se crea un archivo temporal.
# Cuando termina correctamente, se reemplaza
# el archivo original.
# ---------------------------------------------------------

def save_metadata(metadata):
    metadata_directory = METADATA_FILE.parent

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=metadata_directory,
        delete=False,
        suffix=".tmp"
    ) as temporary_file:

        json.dump(
            metadata,
            temporary_file,
            indent=4,
            ensure_ascii=False
        )

        temporary_file.flush()

        os.fsync(
            temporary_file.fileno()
        )

        temporary_path = Path(
            temporary_file.name
        )

    try:
        os.replace(
            temporary_path,
            METADATA_FILE
        )

    except Exception:
        temporary_path.unlink(
            missing_ok=True
        )

        raise


# ---------------------------------------------------------
# Registra los documentos físicos existentes en metadata.
# ---------------------------------------------------------

def initialize_metadata():
    metadata = load_metadata()

    for file_path in DOCUMENTS_DIR.iterdir():

        if not file_path.is_file():
            continue

        if file_path.name in metadata:
            continue

        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:

            while chunk := file.read(1024 * 1024):
                sha256.update(chunk)

        metadata[file_path.name] = {
            "sha256": sha256.hexdigest(),
            "size_bytes": file_path.stat().st_size,
            "content_type": None
        }

    save_metadata(metadata)

    return metadata


# ---------------------------------------------------------
# Genera un nombre alternativo si el nombre ya existe.
# ---------------------------------------------------------

def get_available_filename(filename):
    original_path = DOCUMENTS_DIR / filename

    if not original_path.exists():
        return filename

    path = Path(filename)

    name = path.stem
    extension = path.suffix

    counter = 1

    while True:

        new_filename = (
            f"{name}_{counter}{extension}"
        )

        new_path = DOCUMENTS_DIR / new_filename

        if not new_path.exists():
            return new_filename

        counter += 1


# ---------------------------------------------------------
# Recibe, procesa y almacena un documento para RAG.
# ---------------------------------------------------------

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    # -----------------------------------------------------
    # 1. Validar extensión.
    # -----------------------------------------------------

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension in BLOCKED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail="Este tipo de archivo no está permitido."
        )


    # -----------------------------------------------------
    # 2. Calcular SHA-256 para detectar duplicados.
    # -----------------------------------------------------

    file_hash = await calculate_file_hash(file)

    metadata = load_metadata()

    for filename, info in metadata.items():

        if info["sha256"] == file_hash:

            raise HTTPException(
                status_code=409,
                detail=(
                    "El documento ya existe con el "
                    f"nombre '{filename}'."
                )
            )


    # -----------------------------------------------------
    # 3. Determinar el nombre y ruta del archivo.
    # -----------------------------------------------------

    filename = get_available_filename(
        file.filename
    )

    file_path = DOCUMENTS_DIR / filename

    total_size = 0

    try:

        # -------------------------------------------------
        # 4. Guardar físicamente el archivo.
        # -------------------------------------------------

        with file_path.open("wb") as buffer:

            while chunk := await file.read(
                1024 * 1024
            ):

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:

                    file_path.unlink(
                        missing_ok=True
                    )

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "El archivo supera el "
                            "tamaño máximo permitido "
                            "de 50 MB."
                        )
                    )

                buffer.write(chunk)


        # -------------------------------------------------
        # 5. Extraer texto, generar chunks y embeddings.
        # -------------------------------------------------

        chunks, embeddings = process_document(
            file_path
        )


        # -------------------------------------------------
        # 6. Guardar documento + chunks + embeddings
        #    en PostgreSQL.
        # -------------------------------------------------

        document_id = save_document_with_chunks(
            filename=filename,
            sha256=file_hash,
            size_bytes=total_size,
            content_type=file.content_type,
            texts=chunks,
            embeddings=embeddings
        )


        # -------------------------------------------------
        # 7. Guardar metadata.
        #
        # Si esta operación falla, eliminamos el documento
        # de PostgreSQL y el archivo físico.
        # -------------------------------------------------

        try:

            metadata[filename] = {
                "sha256": file_hash,
                "size_bytes": total_size,
                "content_type": file.content_type
            }
                             
            save_metadata(metadata)


        except Exception:

            # ---------------------------------------------
            # Rollback de PostgreSQL.
            #
            # La eliminación del documento también elimina
            # automáticamente sus chunks por ON DELETE
            # CASCADE.
            # ---------------------------------------------

            delete_document(
                document_id
            )

            # ---------------------------------------------
            # Eliminar archivo físico.
            # ---------------------------------------------

            file_path.unlink(
                missing_ok=True
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "El documento fue guardado en PostgreSQL, "
                    "pero ocurrió un error guardando sus "
                    "metadatos. Se revirtieron los cambios."
                )
            )


        # -------------------------------------------------
        # 8. Devolver resultado del procesamiento.
        # -------------------------------------------------

        return {
            "filename": filename,
            "content_type": file.content_type,
            "size_bytes": total_size,
            "saved": True,
            "document_id": document_id,
            "chunks_processed": len(chunks)
        }


    except HTTPException:
        raise


    except Exception as error:

        # -------------------------------------------------
        # Si algo falla antes de completar el proceso,
        # eliminamos el archivo físico.
        # -------------------------------------------------

        file_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Ocurrió un error procesando el "
                f"documento: {str(error)}"
            )
        )