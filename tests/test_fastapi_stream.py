import json
import httpx


# Prueba de integración: verifica el streaming real de FastAPI.
def test_fastapi_stream():
    # Envía una pregunta a FastAPI y recibe la respuesta progresivamente.
    with httpx.stream(
        "POST",
        "http://127.0.0.1:8000/chat",
        json={
            "session_id": "prueba-saludo",
            "message": "Hola, ¿Cómo estás?",
        },
        timeout=500.0
    ) as respuesta:

        # Comprueba que FastAPI respondió correctamente.
        respuesta.raise_for_status()
        assert respuesta.status_code == 200

        print("Respuesta de FastAPI:")
        print()

        contenido_completo = ""
        recibio_token = False
        recibio_done = False

        # Procesa cada línea del flujo SSE.
        for linea in respuesta.iter_lines():

            # Ignora líneas vacías utilizadas para separar los eventos SSE.
            if not linea:
                continue

            # Detecta un evento de tipo token.
            if linea.startswith("event: token"):
                recibio_token = True
                continue

            # Detecta el evento que indica que la respuesta terminó.
            if linea.startswith("event: done"):
                recibio_done = True
                continue

            # Procesa los datos enviados por el evento SSE.
            if linea.startswith("data: "):
                datos = json.loads(linea[6:])

                # Extrae e imprime únicamente el contenido generado.
                if "content" in datos:
                    contenido = datos["content"]
                    print(contenido, end="", flush=True)
                    contenido_completo += contenido

        print()

        # Comprueba que se recibieron eventos de streaming.
        assert recibio_token

        # Comprueba que el flujo finalizó correctamente.
        assert recibio_done

        # Comprueba que realmente se recibió contenido.
        assert contenido_completo
        

# Permite ejecutar la prueba directamente con Python.
if __name__ == "__main__":
    test_fastapi_stream()