from fastapi import APIRouter, File, HTTPException, UploadFile
import hashlib
import json
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["Documents"])


# Define la carpeta donde se almacenarán los documentos subidos.
DOCUMENTS_DIR = Path("data/documents")

# Crea la carpeta si todavía no existe.
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

# Extensiones de archivos que no permitimos subir al sistema.
BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".scr",
    ".zip",
    ".rar",
}

# Tamaño máximo permitido por archivo: 50 MB.
MAX_FILE_SIZE = 50 * 1024 * 1024

# Define la ubicación donde se almacenará la metadata de los documentos.
METADATA_FILE = Path("data/documents_metadata.json")

# Calcula el hash SHA-256 del contenido de un archivo.
async def calculate_file_hash(file: UploadFile):
    sha256 = hashlib.sha256()

    while chunk := await file.read(1024 * 1024):
        sha256.update(chunk)

    await file.seek(0)

    return sha256.hexdigest()

# Lee la metadata de los documentos almacenada en el archivo JSON.
def load_metadata():
    if not METADATA_FILE.exists():
        return {}

    with METADATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)
    
# Guarda la metadata de los documentos en el archivo JSON.
def save_metadata(metadata):
    with METADATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)
        
# Registra en la metadata los documentos que ya existen físicamente.
def initialize_metadata():
    metadata = load_metadata()

    for file_path in DOCUMENTS_DIR.iterdir():
        if not file_path.is_file():
            continue

        # Si el archivo ya está registrado, no necesitamos procesarlo otra vez.
        if file_path.name in metadata:
            continue

        # Calcula el SHA-256 del archivo existente.
        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:
            while chunk := file.read(1024 * 1024):
                sha256.update(chunk)

        # Guarda la información básica del documento.
        metadata[file_path.name] = {
            "sha256": sha256.hexdigest(),
            "size_bytes": file_path.stat().st_size,
            "content_type": None
        }

    save_metadata(metadata)

    return metadata

# Genera un nombre alternativo cuando el nombre original ya está ocupado.
def get_available_filename(filename):
    original_path = DOCUMENTS_DIR / filename

    # Si el nombre original está disponible, lo utilizamos directamente.
    if not original_path.exists():
        return filename

    path = Path(filename)
    name = path.stem
    extension = path.suffix
    counter = 1

    # Busca el siguiente nombre disponible agregando un número.
    while True:
        new_filename = f"{name}_{counter}{extension}"
        new_path = DOCUMENTS_DIR / new_filename

        if not new_path.exists():
            return new_filename

        counter += 1

# Recibe un documento, valida su extensión y tamaño, y lo guarda.
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Obtiene la extensión del archivo y la convierte a minúsculas.
    extension = Path(file.filename).suffix.lower()
    
    # Calcula la huella SHA-256 del contenido del archivo.
    file_hash = await calculate_file_hash(file)
    
    # Carga la metadata existente de los documentos.
    metadata = load_metadata()

    # Busca si el mismo contenido ya fue registrado anteriormente.
    for filename, info in metadata.items():
        if info["sha256"] == file_hash:
            raise HTTPException(
                status_code=409,
                detail=f"El documento ya existe con el nombre '{filename}'."
            )
            
    # Rechaza archivos con extensiones bloqueadas.
    if extension in BLOCKED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Este tipo de archivo no está permitido."
        )

    # Obtiene un nombre disponible para evitar sobrescribir documentos existentes.
    filename = get_available_filename(file.filename)
    # Construye la ruta completa donde se guardará el documento.
    file_path = DOCUMENTS_DIR / filename
    total_size = 0

    # Lee el archivo por bloques de 1 MB y lo guarda progresivamente.
    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024): # Lee un bloque y guárdalo en chunk; mientras haya contenido, continúa.
            total_size += len(chunk)

            # Rechaza el archivo si supera el límite establecido.
            if total_size > MAX_FILE_SIZE:
                file_path.unlink()
                raise HTTPException(
                    status_code=413,
                    detail="El archivo supera el tamaño máximo permitido de 50 MB."
                )

            buffer.write(chunk)
            
    # Registra la información del documento en la metadata.
    metadata[filename] = {
        "sha256": file_hash,
        "size_bytes": total_size,
        "content_type": file.content_type
    }
    
    # Guarda la metadata actualizada en el archivo JSON.
    save_metadata(metadata)

    return {
        "filename": filename,
        "content_type": file.content_type,
        "size_bytes": total_size,
        "saved": True
    }