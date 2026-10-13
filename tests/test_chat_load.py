
import asyncio
import json
import time
import uuid

import httpx


# Configuración de la prueba de concurrencia.
NUM_USUARIOS = 3
URL_CHAT = "http://127.0.0.1:8000/chat"
TIMEOUT = 500.0

# Pregunta utilizada por todos los usuarios simulados.
PREGUNTA = "¿Cómo se cambia la contraseña?"


# Consume los eventos SSE de un usuario y mide sus tiempos.
async def simular_usuario(
    cliente: httpx.AsyncClient,
    numero_usuario: int,
) -> dict:

    session_id = f"load-test-{uuid.uuid4()}"
    inicio = time.perf_counter()
    primer_token = None
    respuesta_completa = ""
    evento_actual = None
    datos_actuales = []

    resultado = {
        "usuario": numero_usuario,
        "session_id": session_id,
        "http_status": None,
        "primer_token_s": None,
        "duracion_s": None,
        "caracteres": 0,
        "terminado": False,
        "error": None,
    }

    # Procesa un evento SSE completo.
    def procesar_evento() -> None:
        nonlocal primer_token
        nonlocal respuesta_completa

        if not evento_actual or not datos_actuales:
            return

        datos = json.loads("\n".join(datos_actuales))

        if evento_actual == "token":
            contenido = datos.get("content", "")

            if contenido:
                if primer_token is None:
                    primer_token = time.perf_counter() - inicio

                respuesta_completa += contenido

        elif evento_actual == "done":
            resultado["terminado"] = True

        elif evento_actual == "error":
            resultado["error"] = (
                f'{datos.get("code", "SSE_ERROR")}: '
                f'{datos.get("message", "Error desconocido")}'
            )

    try:
        # Cada usuario envía una solicitud independiente.
        async with cliente.stream(
            "POST",
            URL_CHAT,
            json={
                "session_id": session_id,
                "message": PREGUNTA,
            },
        ) as response:

            resultado["http_status"] = response.status_code
            response.raise_for_status()

            # Lee el flujo línea por línea y reconstruye eventos SSE.
            async for linea in response.aiter_lines():

                if linea == "":
                    procesar_evento()
                    evento_actual = None
                    datos_actuales = []

                elif linea.startswith("event:"):
                    evento_actual = linea[6:].strip()

                elif linea.startswith("data:"):
                    datos_actuales.append(linea[5:].lstrip())

            # Procesa un posible último evento sin separador final.
            if evento_actual is not None:
                procesar_evento()

    except httpx.HTTPStatusError as error:
        resultado["error"] = (
            f"HTTP {error.response.status_code}"
        )

    except httpx.TimeoutException:
        resultado["error"] = "Tiempo de espera agotado"

    except httpx.RequestError as error:
        resultado["error"] = (
            f"Error de conexión: {type(error).__name__}"
        )

    except (json.JSONDecodeError, ValueError) as error:
        resultado["error"] = (
            f"Error procesando SSE: {error}"
        )

    except Exception as error:
        resultado["error"] = (
            f"Error inesperado: {type(error).__name__}: {error}"
        )

    finally:
        resultado["duracion_s"] = time.perf_counter() - inicio
        resultado["primer_token_s"] = primer_token
        resultado["caracteres"] = len(respuesta_completa)

        if not resultado["terminado"] and not resultado["error"]:
            resultado["error"] = "El flujo terminó sin evento done"

    return resultado


# Ejecuta la prueba y presenta un resumen de resultados.
async def ejecutar_prueba() -> None:
    print(f"Iniciando prueba con {NUM_USUARIOS} usuarios...")
    inicio_prueba = time.perf_counter()

    timeout = httpx.Timeout(TIMEOUT, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as cliente:
        tareas = [
            simular_usuario(cliente, numero)
            for numero in range(1, NUM_USUARIOS + 1)
        ]

        resultados = await asyncio.gather(*tareas)

    duracion_prueba = time.perf_counter() - inicio_prueba

    print("\nRESULTADOS POR USUARIO")
    print("-" * 65)

    for resultado in resultados:
        estado = (
            "ÉXITO"
            if resultado["terminado"] and not resultado["error"]
            else "ERROR"
        )

        primer_token = resultado["primer_token_s"]
        primer_token_texto = (
            f"{primer_token:.2f} s"
            if primer_token is not None
            else "N/D"
        )

        print(f'\nUsuario: {resultado["usuario"]}')
        print(f"Estado: {estado}")
        print(f'HTTP: {resultado["http_status"]}')
        print(f"Primer token: {primer_token_texto}")
        print(f'Duración: {resultado["duracion_s"]:.2f} s')
        print(f'Caracteres: {resultado["caracteres"]}')

        if resultado["error"]:
            print(f'Error: {resultado["error"]}')

    exitosos = sum(
        1 for r in resultados
        if r["terminado"] and not r["error"]
    )

    errores = NUM_USUARIOS - exitosos

    tiempos_totales = [
        r["duracion_s"] for r in resultados
    ]

    tiempos_primer_token = [
        r["primer_token_s"]
        for r in resultados
        if r["primer_token_s"] is not None
    ]

    print("\nRESUMEN GENERAL")
    print("-" * 65)
    print(f"Usuarios simulados: {NUM_USUARIOS}")
    print(f"Respuestas exitosas: {exitosos}")
    print(f"Solicitudes con errores: {errores}")
    print(f"Duración de la prueba: {duracion_prueba:.2f} s")

    if tiempos_totales:
        print(
            "Duración promedio por usuario: "
            f"{sum(tiempos_totales) / len(tiempos_totales):.2f} s"
        )
        print(
            "Duración máxima individual: "
            f"{max(tiempos_totales):.2f} s"
        )

    if tiempos_primer_token:
        print(
            "Promedio hasta primer token: "
            f"{sum(tiempos_primer_token) / len(tiempos_primer_token):.2f} s"
        )


# Permite ejecutar el script directamente sin ejecutarlo al importar.
if __name__ == "__main__":
    asyncio.run(ejecutar_prueba())
