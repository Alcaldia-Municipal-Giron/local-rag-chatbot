
import json
import time

from app.rag.retriever import recuperar_contexto
from app.rag.context_builder import construir_contexto
from app.services.conversation_service import (
    obtener_historial,
    agregar_mensaje,
)
from app.services.ollama_service import (
    generar_respuesta as generar_respuesta_ollama,
    OllamaServiceError,
)
from app.services.intent_service import (
    detectar_intencion,
    obtener_respuesta_intencion,
)


# Mantiene el mismo mensaje cuando no se encuentra contexto relevante.
MENSAJE_SIN_CONTEXTO = (
    "No encontré información suficiente en los documentos "
    "para responder esta pregunta."
)

# Conserva el umbral de distancia y la cantidad de fragmentos del RAG.
MAX_DISTANCE = 0.50
TOP_K = 3


# Convierte los eventos y sus datos al formato SSE.
def crear_evento_sse(evento: str, datos: dict) -> str:
    contenido = json.dumps(datos, ensure_ascii=False)
    return f"event: {evento}\ndata: {contenido}\n\n"


# Guarda la respuesta del asistente y devuelve el tiempo empleado.
def guardar_respuesta(
    session_id: str,
    respuesta: str,
) -> float:
    inicio_guardado = time.perf_counter()

    agregar_mensaje(
        session_id,
        {
            "role": "assistant",
            "content": respuesta,
        },
    )

    return time.perf_counter() - inicio_guardado


# Registra las métricas de las respuestas que no necesitan consultar
# los documentos ni invocar el modelo de Ollama.
def registrar_respuesta_sin_rag(
    session_id: str,
    tiempo_guardado: float,
    tiempo_historial: float,
    tiempo_guardado_respuesta: float,
    tiempo_total: float,
    tipo_respuesta: str,
) -> None:
    print(
        "[CHAT] "
        f"Sesión: {session_id} | "
        f"Tipo: {tipo_respuesta} | "
        f"Guardado usuario: {tiempo_guardado:.2f}s | "
        f"Historial: {tiempo_historial:.2f}s | "
        f"Guardado respuesta: {tiempo_guardado_respuesta:.2f}s | "
        f"Total sin RAG: {tiempo_total:.2f}s"
    )


# Coordina el historial, la detección de intenciones, el RAG,
# la construcción del contexto y la generación de respuestas.
#
# Devuelve un generador SSE que conserva los eventos token, done y error.
# La recuperación RAG se ejecuta antes de devolver el generador para que
# los errores de base de datos puedan propagarse antes de iniciar la
# transmisión HTTP.
def preparar_stream_chat(
    session_id: str,
    mensaje: str,
):
    inicio_solicitud = time.perf_counter()

    # Guarda primero el mensaje del usuario para conservar la persistencia.
    inicio_guardado = time.perf_counter()

    agregar_mensaje(
        session_id,
        {
            "role": "user",
            "content": mensaje,
        },
    )

    tiempo_guardado = time.perf_counter() - inicio_guardado

    # Recupera el historial de la conversación, incluido el mensaje actual.
    inicio_historial = time.perf_counter()

    historial = obtener_historial(session_id)

    tiempo_historial = time.perf_counter() - inicio_historial

    # Delega la clasificación del mensaje al servicio de intenciones.
    intencion = detectar_intencion(mensaje)

    # Obtiene una respuesta directa si se reconoció una intención social.
    respuesta_social = (
        obtener_respuesta_intencion(intencion)
        if intencion is not None
        else None
    )

    # Resuelve las intenciones sociales sin consultar el RAG ni Ollama.
    if respuesta_social is not None:
        tiempo_guardado_respuesta = guardar_respuesta(
            session_id=session_id,
            respuesta=respuesta_social,
        )

        tiempo_total = time.perf_counter() - inicio_solicitud

        registrar_respuesta_sin_rag(
            session_id=session_id,
            tiempo_guardado=tiempo_guardado,
            tiempo_historial=tiempo_historial,
            tiempo_guardado_respuesta=tiempo_guardado_respuesta,
            tiempo_total=tiempo_total,
            tipo_respuesta=f"intención: {intencion}",
        )

        # Envía la respuesta social mediante el mismo contrato SSE.
        def transmitir_respuesta_social():
            yield crear_evento_sse(
                "token",
                {"content": respuesta_social},
            )

            yield crear_evento_sse(
                "done",
                {"message": "Respuesta completada"},
            )

        return transmitir_respuesta_social()

    # Recupera los fragmentos documentales más relevantes para la pregunta.
    inicio_rag = time.perf_counter()

    resultados = recuperar_contexto(
        mensaje,
        top_k=TOP_K,
    )

    tiempo_rag = time.perf_counter() - inicio_rag

    # Comprueba si el mejor resultado supera el umbral de distancia.
    if not resultados or resultados[0]["distance"] > MAX_DISTANCE:
        tiempo_guardado_respuesta = guardar_respuesta(
            session_id=session_id,
            respuesta=MENSAJE_SIN_CONTEXTO,
        )

        tiempo_total = time.perf_counter() - inicio_solicitud

        print(
            "[CHAT] "
            f"Sesión: {session_id} | "
            "Tipo: sin contexto suficiente | "
            f"Guardado usuario: {tiempo_guardado:.2f}s | "
            f"Historial: {tiempo_historial:.2f}s | "
            f"RAG: {tiempo_rag:.2f}s | "
            f"Guardado respuesta: {tiempo_guardado_respuesta:.2f}s | "
            f"Total sin contexto: {tiempo_total:.2f}s"
        )

        # Devuelve el mensaje de falta de contexto mediante SSE.
        def transmitir_sin_contexto():
            yield crear_evento_sse(
                "token",
                {"content": MENSAJE_SIN_CONTEXTO},
            )

            yield crear_evento_sse(
                "done",
                {"message": "Respuesta completada"},
            )

        return transmitir_sin_contexto()

    # Construye el contexto con los fragmentos recuperados.
    inicio_contexto = time.perf_counter()

    contexto = construir_contexto(resultados)

    tiempo_construccion_contexto = (
        time.perf_counter() - inicio_contexto
    )

    # Prepara las instrucciones del modelo y el historial de conversación.
    messages = [
        {
            "role": "system",
            "content": f"""
Eres un asistente de consulta documental.

Responde siempre en español y utiliza únicamente la información del CONTEXTO.

REGLAS:
1. No uses conocimientos externos ni información que no aparezca en el CONTEXTO.
2. No inventes, supongas ni completes datos faltantes.
3. Responde solo cuando el CONTEXTO contenga información suficiente y directamente relacionada con la pregunta.
4. Para datos específicos o procedimientos, utiliza únicamente información explícitamente presente en el CONTEXTO.
5. Si el CONTEXTO no contiene información suficiente, responde exactamente:

"{MENSAJE_SIN_CONTEXTO}"

Si existe información suficiente, responde de forma clara, directa y concisa.

CONTEXTO:

{contexto}
""",
        }
    ] + historial

    # Calcula las métricas del prompt. El contexto ya forma parte del
    # mensaje de sistema, por lo que no debe sumarse dos veces al total.
    contenido_sistema = messages[0]["content"]

    caracteres_historial = sum(
        len(item.get("content", ""))
        for item in historial
    )

    caracteres_sistema = len(contenido_sistema)
    caracteres_contexto = len(contexto)
    cantidad_mensajes_historial = len(historial)

    caracteres_totales = caracteres_sistema + caracteres_historial

    print(
        "[PROMPT] "
        f"Sesión: {session_id} | "
        f"Mensajes historial: {cantidad_mensajes_historial} | "
        f"Caracteres sistema: {caracteres_sistema} | "
        f"Caracteres contexto: {caracteres_contexto} | "
        f"Caracteres historial: {caracteres_historial} | "
        f"Caracteres totales aproximados: {caracteres_totales}"
    )

    # Mide el tiempo transcurrido antes de comenzar la generación.
    tiempo_previo_ollama = time.perf_counter() - inicio_solicitud

    # Transmite progresivamente la respuesta del modelo y guarda el
    # mensaje completo al finalizar correctamente la generación.
    def transmitir_respuesta():
        respuesta_completa = ""

        inicio_generacion = time.perf_counter()
        tiempo_primer_fragmento = None
        generacion_exitosa = False

        try:
            # Cada fragmento se envía al cliente y se acumula para guardarlo.
            for contenido in generar_respuesta_ollama(messages):
                if not contenido:
                    continue

                # Registra cuánto tarda Ollama en entregar el primer fragmento.
                if tiempo_primer_fragmento is None:
                    tiempo_primer_fragmento = (
                        time.perf_counter() - inicio_generacion
                    )

                respuesta_completa += contenido

                yield crear_evento_sse(
                    "token",
                    {"content": contenido},
                )

            generacion_exitosa = True

        except OllamaServiceError as e:
            # Informa del error de generación sin guardar una respuesta parcial.
            print(f"Error durante la generación con Ollama: {e}")

            yield crear_evento_sse(
                "error",
                {
                    "code": "GENERATION_FAILED",
                    "message": "No fue posible completar la respuesta.",
                },
            )

            return

        finally:
            # Registra las métricas incluso cuando la generación falla.
            tiempo_generacion = (
                time.perf_counter() - inicio_generacion
            )

            if tiempo_primer_fragmento is not None:
                primer_fragmento = (
                    f"{tiempo_primer_fragmento:.2f}s"
                )
            else:
                primer_fragmento = "N/D"

            print(
                "[CHAT] "
                f"Sesión: {session_id} | "
                f"Guardado usuario: {tiempo_guardado:.2f}s | "
                f"Historial: {tiempo_historial:.2f}s | "
                f"RAG: {tiempo_rag:.2f}s | "
                f"Construcción contexto: "
                f"{tiempo_construccion_contexto:.2f}s | "
                f"Previo a Ollama: {tiempo_previo_ollama:.2f}s | "
                f"Primer fragmento Ollama: {primer_fragmento}"
            )

            print(
                "[CHAT] "
                f"Sesión: {session_id} | "
                f"Generación total: {tiempo_generacion:.2f}s | "
                f"Caracteres: {len(respuesta_completa)} | "
                f"Generación exitosa: {generacion_exitosa}"
            )

        # Persiste la respuesta completa solo si se recibió contenido.
        if respuesta_completa:
            try:
                tiempo_guardado_respuesta = guardar_respuesta(
                    session_id=session_id,
                    respuesta=respuesta_completa,
                )

                print(
                    "[CHAT] "
                    f"Sesión: {session_id} | "
                    f"Guardado respuesta: "
                    f"{tiempo_guardado_respuesta:.2f}s"
                )

            except Exception as e:
                # Informa si la respuesta se generó, pero no pudo guardarse.
                print(f"Error al guardar la respuesta: {e}")

                yield crear_evento_sse(
                    "error",
                    {
                        "code": "HISTORY_SAVE_FAILED",
                        "message": (
                            "La respuesta se generó, pero no pudo "
                            "guardarse en el historial."
                        ),
                    },
                )

                return

        # Notifica al cliente que terminó el procesamiento del flujo.
        yield crear_evento_sse(
            "done",
            {"message": "Respuesta completada"},
        )

    return transmitir_respuesta()
