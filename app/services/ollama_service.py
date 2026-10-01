
import json

import httpx


# Configuración de la conexión con Ollama.
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:3b-instruct"
OLLAMA_TIMEOUT = 500.0


# Excepción para errores durante la generación de respuestas.
class OllamaServiceError(Exception):
    pass


# Envía los mensajes a Ollama y transmite progresivamente
# el contenido generado por el modelo.
def generar_respuesta(messages):

    # Configura la solicitud que se enviará a Ollama.
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "options": {
            "num_predict": 400,
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 40,
            "seed": 42,
            "num_ctx": 4096,
        },
    }

    try:

        # Mantiene abierta la conexión con Ollama
        # para recibir la respuesta progresivamente.
        with httpx.stream(
            "POST",
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        ) as respuesta:

            # Comprueba si Ollama respondió con un error HTTP.
            respuesta.raise_for_status()

            # Controla si Ollama confirmó el fin de la generación.
            generacion_completada = False

            # Procesa cada fragmento enviado por Ollama.
            for linea in respuesta.iter_lines():

                if not linea:
                    continue

                try:

                    # Convierte el fragmento JSON en un diccionario.
                    datos = json.loads(linea)

                except json.JSONDecodeError as e:

                    raise OllamaServiceError(
                        "Ollama devolvió un fragmento JSON inválido."
                    ) from e

                # Detecta errores comunicados dentro del JSON.
                if "error" in datos:

                    raise OllamaServiceError(
                        f"Ollama informó un error: {datos['error']}"
                    )

                # Obtiene el mensaje generado por el modelo.
                mensaje = datos.get("message")

                if not isinstance(mensaje, dict):

                    raise OllamaServiceError(
                        "Ollama devolvió una estructura de mensaje inválida."
                    )

                # Extrae el contenido del fragmento recibido.
                contenido = mensaje.get("content")

                if not isinstance(contenido, str):

                    raise OllamaServiceError(
                        "Ollama devolvió contenido con un formato inválido."
                    )

                if contenido:

                    # Envía inmediatamente el fragmento
                    # al consumidor del generador.
                    yield contenido

                # Comprueba si Ollama confirmó la finalización.
                if datos.get("done") is True:

                    generacion_completada = True

                    break

            # Si el flujo terminó sin confirmación,
            # se considera que la generación fue interrumpida.
            if not generacion_completada:

                raise OllamaServiceError(
                    "La generación de Ollama terminó inesperadamente "
                    "sin confirmar su finalización."
                )

    except httpx.HTTPStatusError as e:

        # Convierte los errores HTTP en una excepción del servicio.
        raise OllamaServiceError(
            f"Ollama respondió con el estado HTTP "
            f"{e.response.status_code}."
        ) from e

    except httpx.RequestError as e:

        # Maneja los errores de conexión o lectura de Ollama.
        raise OllamaServiceError(
            "No se pudo establecer o mantener la conexión con Ollama."
        ) from e
