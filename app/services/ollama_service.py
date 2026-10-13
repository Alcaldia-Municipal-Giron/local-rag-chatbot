import json
import logging
import time

import httpx


# Configuración de la conexión con Ollama.
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:3b-instruct"
OLLAMA_TIMEOUT = 500.0


# Configuración del registro de métricas.
logger = logging.getLogger(__name__)


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

    # Registra el inicio de la solicitud.
    inicio_solicitud = time.perf_counter()

    # Inicializa las métricas de la generación.
    tiempo_respuesta_http = None
    tiempo_primer_fragmento = None
    metricas_finales = None
    generacion_completada = False

    try:

        # Mantiene abierta la conexión con Ollama
        # para recibir la respuesta progresivamente.
        with httpx.stream(
            "POST",
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        ) as respuesta:

            # Registra el tiempo hasta recibir la respuesta HTTP.
            tiempo_respuesta_http = time.perf_counter() - inicio_solicitud

            # Comprueba si Ollama respondió con un error HTTP.
            respuesta.raise_for_status()

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

                    # Registra el tiempo hasta el primer contenido.
                    if tiempo_primer_fragmento is None:
                        tiempo_primer_fragmento = (
                            time.perf_counter() - inicio_solicitud
                        )

                    # Envía inmediatamente el fragmento
                    # al consumidor del generador.
                    yield contenido

                # Comprueba si Ollama confirmó la finalización.
                if datos.get("done") is True:

                    generacion_completada = True

                    # Conserva las métricas que Ollama informa
                    # en el último fragmento del flujo.
                    metricas_finales = {
                        "prompt_eval_count": datos.get("prompt_eval_count"),
                        "prompt_eval_duration": datos.get(
                            "prompt_eval_duration"
                        ),
                        "eval_count": datos.get("eval_count"),
                        "eval_duration": datos.get("eval_duration"),
                        "load_duration": datos.get("load_duration"),
                        "total_duration": datos.get("total_duration"),
                    }

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

    finally:

        # Calcula el tiempo total transcurrido.
        tiempo_total = time.perf_counter() - inicio_solicitud

        # Convierte las duraciones de nanosegundos a segundos.
        if metricas_finales:
            prompt_eval_segundos = (
                metricas_finales["prompt_eval_duration"] / 1_000_000_000
                if metricas_finales["prompt_eval_duration"] is not None
                else None
            )

            eval_segundos = (
                metricas_finales["eval_duration"] / 1_000_000_000
                if metricas_finales["eval_duration"] is not None
                else None
            )

            # Calcula la velocidad de generación en tokens por segundo.
            tokens_por_segundo = (
                metricas_finales["eval_count"] / eval_segundos
                if (
                    metricas_finales["eval_count"] is not None
                    and eval_segundos is not None
                    and eval_segundos > 0
                )
                else None
            )

            logger.info(
                "[OLLAMA] HTTP: %.2fs | Primer fragmento: %s | "
                "Total: %.2fs | Prompt: %s tokens en %s s | "
                "Generación: %s tokens en %s s | Velocidad: %s tok/s | "
                "Carga modelo: %s s | Total Ollama: %s s",
                tiempo_respuesta_http
                if tiempo_respuesta_http is not None
                else -1,
                (
                    f"{tiempo_primer_fragmento:.2f}s"
                    if tiempo_primer_fragmento is not None
                    else "Sin contenido"
                ),
                tiempo_total,
                metricas_finales["prompt_eval_count"],
                f"{prompt_eval_segundos:.2f}"
                if prompt_eval_segundos is not None
                else "N/D",
                metricas_finales["eval_count"],
                f"{eval_segundos:.2f}"
                if eval_segundos is not None
                else "N/D",
                f"{tokens_por_segundo:.2f}"
                if tokens_por_segundo is not None
                else "N/D",
                (
                    f"{metricas_finales['load_duration'] / 1_000_000_000:.2f}"
                    if metricas_finales["load_duration"] is not None
                    else "N/D"
                ),
                (
                    f"{metricas_finales['total_duration'] / 1_000_000_000:.2f}"
                    if metricas_finales["total_duration"] is not None
                    else "N/D"
                ),
            )

        else:
            logger.warning(
                "[OLLAMA] Generación incompleta o sin métricas finales. "
                "HTTP: %s | Primer fragmento: %s | Tiempo transcurrido: %.2fs",
                (
                    f"{tiempo_respuesta_http:.2f}s"
                    if tiempo_respuesta_http is not None
                    else "Sin respuesta"
                ),
                (
                    f"{tiempo_primer_fragmento:.2f}s"
                    if tiempo_primer_fragmento is not None
                    else "Sin contenido"
                ),
                tiempo_total,
            )
