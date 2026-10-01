# Chatbot con IA

Chatbot con IA desarrollado completamente de forma local utilizando Python, FastAPI, Ollama, PostgreSQL, pgvector y modelos de IA locales.

El proyecto implementa una arquitectura RAG (Retrieval-Augmented Generation), que permite procesar documentos, generar embeddings, almacenarlos en una base de datos vectorial y recuperar información relevante para utilizarla como contexto al responder las preguntas del usuario.

> Proyecto en desarrollo. La documentación se irá ampliando a medida que se incorporen nuevas funcionalidades.

---

# Tecnologías

- Python 3.12.10
- FastAPI
- Uvicorn
- Ollama 0.34.0
- Qwen2.5 Coder 3B Instruct
- Sentence Transformers
- BGE-M3
- PostgreSQL 17.11
- pgvector 0.8.6
- Docker
- HTTPX
- Git / GitHub

---

# Arquitectura general

El funcionamiento principal del proyecto se divide en dos procesos.

## 1. Procesamiento e indexación de documentos

Documento
    ↓
documents.py
    ↓
Extracción de texto
    ↓
text_extractor.py
    ↓
División en chunks
    ↓
text_chunker.py
    ↓
Generación de embeddings
    ↓
embedding_service.py
    ↓
PostgreSQL + pgvector

## 2. Consulta del usuario

Pregunta del usuario
    ↓
chat.py
    ↓
Embedding de la pregunta
    ↓
BGE-M3
    ↓
retriever.py
    ↓
PostgreSQL + pgvector
    ↓
Búsqueda por similitud
    ↓
Chunks relevantes
    ↓
context_builder.py
    ↓
Filtro de relevancia
    ↓
Ollama
    ↓
Qwen2.5 Coder 3B Instruct
    ↓
Respuesta en streaming

---

# Requisitos

Antes de ejecutar el proyecto se necesita tener instalado:

- Python 3.12 o superior
- Git
- Docker Desktop
- Ollama

Además, Docker debe estar funcionando y Ollama debe estar disponible localmente.

---

# 1. Descargar el proyecto

Clonar el repositorio:

git clone <URL_DEL_REPOSITORIO>

Entrar en la carpeta del proyecto:

cd local-rag-chatbot

---

# 2. Crear el entorno virtual

Crear el entorno virtual:

python -m venv .venv

Activar el entorno virtual en Windows:

.venv\Scripts\activate

---

# 3. Instalar las dependencias

Con el entorno virtual activado:

pip install -r requirements.txt

---

# 4. Configurar Ollama

El proyecto utiliza Ollama para ejecutar localmente el modelo de lenguaje.

Descargar el modelo:

ollama pull qwen2.5-coder:3b-instruct

Comprobar que el modelo está instalado:

ollama list

Debería aparecer:

qwen2.5-coder:3b-instruct

Iniciar el servidor local de Ollama:

ollama serve

Ollama debe quedar disponible en:

http://127.0.0.1:11434

Si Ollama ya está ejecutándose como aplicación en Windows, no es necesario iniciar ollama serve nuevamente.

---

# 5. Configurar PostgreSQL + pgvector con Docker

El proyecto utiliza PostgreSQL como base de datos y pgvector para almacenar y consultar los embeddings.

## 5.1 Crear la red Docker

Crear la red utilizada por los servicios del proyecto:

docker network create local-rag-network

Si la red ya existe, Docker mostrará un mensaje indicando que ya existe.

## 5.2 Crear el volumen de PostgreSQL

Crear un volumen para conservar los datos de PostgreSQL aunque el contenedor se detenga o elimine:

docker volume create local-rag-postgres-data

## 5.3 Descargar la imagen de pgvector

El proyecto utiliza la imagen:

pgvector/pgvector:pg17

Puede descargarse mediante:

docker pull pgvector/pgvector:pg17

## 5.4 Crear y ejecutar el contenedor PostgreSQL

En Windows CMD:

docker run -d ^
  --name local-rag-postgres ^
  --network local-rag-network ^
  -e POSTGRES_DB=local_rag ^
  -e POSTGRES_USER=rag_user ^
  -e POSTGRES_PASSWORD=rag_password_local ^
  -p 5433:5432 ^
  -v local-rag-postgres-data:/var/lib/postgresql/data ^
  pgvector/pgvector:pg17

Configuración utilizada:

- Contenedor: local-rag-postgres
- Base de datos: local_rag
- Usuario: rag_user
- Contraseña: rag_password_local
- Puerto del host: 5433
- Puerto interno: 5432
- Volumen: local-rag-postgres-data
- Imagen: pgvector/pgvector:pg17
- Red: local-rag-network

El puerto 5433 corresponde al puerto utilizado desde Windows para conectarse al PostgreSQL que está dentro del contenedor.

---

# 6. Comprobar el contenedor PostgreSQL

Ver los contenedores activos:

docker ps

Debería aparecer:

local-rag-postgres

También se puede comprobar específicamente:

docker ps --filter "name=local-rag-postgres"

---

# 7. Conectarse a PostgreSQL mediante psql

Para abrir psql directamente dentro del contenedor:

docker exec -it local-rag-postgres psql -U rag_user -d local_rag

Si la conexión es correcta aparecerá algo similar a:

psql (17.11)
Type "help" for help.

local_rag=#

A partir de este momento se pueden ejecutar comandos SQL directamente sobre la base de datos.

---

# 8. Comprobar la versión de PostgreSQL

Dentro de psql:

SELECT version();

---

# 9. Activar pgvector

Dentro de psql:

CREATE EXTENSION IF NOT EXISTS vector;

Comprobar que la extensión está instalada:

SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';

El proyecto utiliza actualmente:

vector | 0.8.6

---

# 10. Comprobar las tablas

Dentro de psql:

\dt

Esto permite comprobar las tablas existentes en la base de datos.

Para salir de psql:

\q

---

# 11. Datos de conexión

La aplicación utiliza PostgreSQL mediante las variables de configuración correspondientes al servidor local.

Configuración actual:

POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=local_rag
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password_local

El puerto utilizado por FastAPI es 5433 porque PostgreSQL está publicado desde Docker mediante 5433:5432.

---

# 12. Procesamiento de documentos

Los documentos se cargan mediante:

POST /documents/upload

El sistema realiza las siguientes operaciones:

Documento
    ↓
Validación
    ↓
Detección de duplicados mediante SHA-256
    ↓
Almacenamiento
    ↓
Extracción de texto
    ↓
Chunking
    ↓
Generación de embeddings
    ↓
Almacenamiento en PostgreSQL + pgvector

Los documentos se almacenan en:

data/documents/

Los metadatos se almacenan en:

data/documents_metadata.json

---

# 13. Formatos de documentos

Actualmente se procesan:

- .txt
- .md
- .pdf
- .docx

La extracción de PDF utiliza pypdf.

La extracción de documentos Word utiliza python-docx.

Actualmente no se realiza OCR. Si un PDF o DOCX contiene texto dentro de una imagen, ese contenido no se extrae mediante el extractor actual.

---

# 14. Chunking

Después de extraer el texto, text_chunker.py divide el contenido en fragmentos llamados chunks.

Configuración actual:

CHUNK_SIZE = 500 palabras
CHUNK_OVERLAP = 50 palabras

El sistema intenta mantener la información relacionada dentro de los mismos fragmentos y evita realizar cortes innecesarios.

También se eliminan líneas vacías y espacios innecesarios durante el procesamiento.

---

# 15. Embeddings

Cada chunk se transforma en una representación numérica mediante el modelo:

BAAI/bge-m3

El modelo genera embeddings de:

1024 dimensiones

Los embeddings permiten representar semánticamente el contenido de los chunks para posteriormente realizar búsquedas por similitud.

---

# 16. PostgreSQL + pgvector

Los chunks y sus embeddings se almacenan en PostgreSQL.

La extensión pgvector permite almacenar los vectores y realizar búsquedas por similitud.

El sistema puede utilizar esta información para encontrar los fragmentos más relacionados con una pregunta.

Si un documento se elimina de la base de datos, también deben eliminarse los chunks y embeddings asociados al documento.

---

# 17. Ejecutar FastAPI

Con el entorno virtual activado:

uvicorn app.main:app --reload

La API estará disponible en:

http://127.0.0.1:8000

---

# 18. Documentación de FastAPI

FastAPI proporciona documentación interactiva mediante Swagger:

http://127.0.0.1:8000/docs

Desde Swagger se pueden probar los endpoints disponibles.

---

# 19. Endpoints actuales

## Health Check

GET /health

Permite comprobar que la API está funcionando.

## Chat

POST /chat

Ejemplo:

{
    "session_id": "mi-sesion",
    "message": "¿Qué información se solicita?"
}

El sistema procesa la pregunta mediante el flujo RAG y devuelve la respuesta mediante streaming.

## Upload de documentos

POST /documents/upload

Permite cargar documentos para posteriormente procesarlos e indexarlos.

---

# 20. Funcionamiento del RAG

Cuando el usuario realiza una pregunta, el sistema sigue este proceso:

Pregunta
    ↓
chat.py
    ↓
Clasificación de la consulta
    ↓
Embedding de la pregunta
    ↓
BGE-M3
    ↓
retriever.py
    ↓
PostgreSQL + pgvector
    ↓
Búsqueda por similitud
    ↓
Top 3 resultados
    ↓
Filtro de relevancia
    ↓
context_builder.py
    ↓
Construcción del contexto
    ↓
Historial reciente
    ↓
Prompt RAG
    ↓
Ollama
    ↓
Qwen2.5 Coder 3B Instruct
    ↓
Respuesta en streaming

---

# 21. Control de relevancia

El sistema utiliza un filtro determinista para evitar enviar a Ollama preguntas que no tengan suficiente evidencia documental.

Configuración actual:

MAX_DISTANCE = 0.50

En pgvector, una distancia menor representa una mayor similitud.

Si no existen resultados suficientes o la mejor distancia supera el límite establecido, el sistema no consulta a Ollama y devuelve:

No encontré información suficiente en los documentos para responder esta pregunta.

Esto evita que el modelo genere respuestas utilizando información externa a los documentos.

---

# 22. Historial de conversaciones

Las conversaciones se almacenan en:

data/conversations.json

El sistema conserva el historial completo de la sesión.

Para las consultas normales se utiliza el historial reciente de los últimos 4 turnos completos.

También existe un modo para reconocer preguntas relacionadas con la conversación, por ejemplo:

¿Qué hemos hablado?
¿De qué hemos hablado?
¿Qué me dijiste?
Resume nuestra conversación.

Estas consultas utilizan el historial conversacional en lugar de realizar una búsqueda documental normal.

---

# 23. Streaming

El endpoint /chat utiliza streaming para recibir progresivamente la respuesta generada por Ollama.

Flujo:

Usuario
   ↓
FastAPI
   ↓
Ollama
   ↓
Qwen
   ↓
Ollama
   ↓
FastAPI
   ↓
Cliente

La respuesta puede mostrarse progresivamente mientras el modelo genera el contenido.

---

# 24. Pruebas

El proyecto contiene pruebas y scripts para comprobar diferentes partes del sistema.

Ejemplo de prueba de streaming:

python tests/test_fastapi_stream.py

Las pruebas pueden utilizarse para verificar la comunicación entre FastAPI y Ollama y comprobar el funcionamiento del flujo RAG.

---

# 25. Estructura actual

local-rag-chatbot/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py
│   │       ├── documents.py
│   │       └── health.py
│   │
│   ├── ingestion/
│   │   ├── text_extractor.py
│   │   └── text_chunker.py
│   │
│   ├── rag/
│   │   ├── embedding_service.py
│   │   ├── retriever.py
│   │   ├── vector_store.py
│   │   └── context_builder.py
│   │
│   ├── services/
│   │   ├── conversation_service.py
│   │   └── query_classifier.py
│   │
│   └── main.py
│
├── data/
│   ├── documents/
│   ├── documents_metadata.json
│   └── conversations.json
│
├── tests/
│
├── .gitignore
├── requirements.txt
└── README.md

.venv no se incluye en la estructura del proyecto porque es un entorno virtual local y normalmente está excluido mediante .gitignore.

---

# 26. Estado actual del proyecto

## Completado

- [x] Configuración de Python y entorno virtual
- [x] Configuración de FastAPI
- [x] Endpoint /health
- [x] Endpoint /chat
- [x] Instalación y configuración de Ollama
- [x] Instalación del modelo Qwen2.5 Coder 3B Instruct
- [x] Comunicación FastAPI → Ollama
- [x] Streaming de respuestas
- [x] Carga de documentos
- [x] Detección de duplicados mediante SHA-256
- [x] Extracción de texto
- [x] Chunking de documentos
- [x] Generación de embeddings
- [x] BGE-M3
- [x] PostgreSQL
- [x] pgvector
- [x] Almacenamiento de embeddings
- [x] Búsqueda semántica
- [x] Recuperación de contexto
- [x] Construcción de contexto
- [x] Integración completa del flujo RAG
- [x] Control determinista de relevancia
- [x] Historial de conversaciones
- [x] Clasificación de consultas conversacionales
- [x] Pruebas del flujo RAG

---
### Próximamente

* [ ] Controlar la longitud de las respuestas del modelo
* [ ] Mejorar la configuración del modelo
* [ ] Implementar RAG
* [ ] Procesamiento de documentos
* [ ] Embeddings
* [ ] Base de datos/vector store
* [ ] Interfaz del chatbot
* [ ] Más documentación

# 27. Consideraciones importantes

El proyecto está diseñado para ejecutarse localmente.

La generación de respuestas se realiza mediante Ollama y un modelo de IA ejecutado en el equipo local.

Los documentos proporcionan el contexto utilizado por el sistema RAG, pero no entrenan ni modifican los pesos del modelo de lenguaje.

El sistema utiliza embeddings y búsqueda vectorial para recuperar información relevante de los documentos antes de generar una respuesta.

Actualmente no se utiliza ninguna API de IA de pago o servicio externo para la generación de respuestas.

---

# 28. Estado estable

El último estado estable del proyecto corresponde al commit:

feat: mejorar control de respuestas del RAG

Las pruebas experimentales realizadas posteriormente fueron descartadas y no forman parte del estado estable actual del proyecto.


## Nota

Este proyecto está diseñado para ejecutarse localmente. Actualmente la generación de respuestas se realiza mediante Ollama y un modelo de IA ejecutado en el equipo local.
