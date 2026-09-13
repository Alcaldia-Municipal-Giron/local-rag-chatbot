# Chatbot con IA

Chatbot con IA desarrollado de forma local utilizando Python, FastAPI, Ollama y un modelo de lenguaje Qwen.

> 🚧 Proyecto en desarrollo. La documentación se irá ampliando a medida que se incorporen nuevas funcionalidades.

## Tecnologías actuales

* Python 3.12.10
* FastAPI
* Uvicorn
* Ollama
* Qwen2.5 Coder 3B Instruct
* HTTPX
* Git / GitHub

## Requisitos

Antes de ejecutar el proyecto se necesita tener instalado:

* Python 3.12 o superior
* Git
* Ollama

Además, se debe tener descargado el modelo:

```bash
ollama pull qwen2.5-coder:3b-instruct
```

## Descargar el proyecto

Clonar el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
```

Entrar en la carpeta del proyecto:

```bash
cd local-rag-chatbot
```

## Crear el entorno virtual

Crear el entorno virtual:

```bash
python -m venv .venv
```

Activar el entorno virtual en Windows:

```powershell
.venv\Scripts\activate
```

## Instalar las dependencias

Instalar las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

## Ejecutar Ollama

Iniciar el servidor local de Ollama:

```bash
ollama serve
```

Ollama debe quedar disponible en:

```text
http://127.0.0.1:11434
```

Para comprobar que el modelo está instalado:

```bash
ollama list
```

Debería aparecer:

```text
qwen2.5-coder:3b-instruct
```

## Ejecutar FastAPI

Con el entorno virtual activado, ejecutar:

```bash
uvicorn app.main:app --reload
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

## Endpoints actuales

### Health Check

```text
GET /health
```

Permite comprobar que la API está funcionando.

### Chat

```text
POST /chat
```

Ejemplo de petición:

```json
{
    "message": "Hola, ¿quién eres?"
}
```

La respuesta es generada por el modelo local mediante Ollama.

Actualmente `/chat` utiliza streaming, por lo que la respuesta puede recibirse progresivamente mientras el modelo genera el contenido.

## Documentación de FastAPI

FastAPI proporciona documentación interactiva mediante Swagger:

```text
http://127.0.0.1:8000/docs
```

## Prueba de streaming

El proyecto incluye un script para comprobar el streaming desde FastAPI:

```bash
python test_fastapi_stream.py
```

Este script comprueba la siguiente comunicación:

```text
Python
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
Python
```

La respuesta se muestra progresivamente en la terminal.

## Estructura actual

```text
local-rag-chatbot/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py
│   │       └── health.py
│   │
│   └── main.py
│
├── .venv/
├── .gitignore
├── requirements.txt
├── test_ollama.py
├── test_fastapi_stream.py
└── README.md
```

## Estado actual

### Completado

* [x] Configuración de Python y entorno virtual
* [x] Configuración de FastAPI
* [x] Endpoint `/health`
* [x] Endpoint `/chat`
* [x] Instalación y configuración de Ollama
* [x] Instalación del modelo Qwen2.5 Coder 3B Instruct
* [x] Comunicación FastAPI → Ollama
* [x] Integración del modelo local
* [x] Streaming de respuestas
* [x] Prueba de streaming de extremo a extremo

### Próximamente

* [ ] Controlar la longitud de las respuestas del modelo
* [ ] Mejorar la configuración del modelo
* [ ] Implementar RAG
* [ ] Procesamiento de documentos
* [ ] Embeddings
* [ ] Base de datos/vector store
* [ ] Interfaz del chatbot
* [ ] Más documentación

## Nota

Este proyecto está diseñado para ejecutarse localmente. Actualmente la generación de respuestas se realiza mediante Ollama y un modelo de IA ejecutado en el equipo local.
