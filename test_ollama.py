import httpx
import json


# Envía un mensaje a Ollama y recibe la respuesta de Qwen progresivamente.
with httpx.stream(
    "POST",
    "http://127.0.0.1:11434/api/chat",
    json={
        "model": "qwen2.5-coder:3b-instruct",
        "messages": [
            {
                "role": "user",
                "content": "Explícame brevemente qué es Python."
            }
        ],
        "stream": True
    },
    timeout=120.0
) as respuesta:

    print("Respuesta de Qwen:")
    print()

    # Procesa cada fragmento JSON que Ollama envía durante la generación.
    for linea in respuesta.iter_lines():

        if linea:
            # Convierte la línea JSON recibida en un diccionario de Python.
            datos = json.loads(linea)

            # Extrae únicamente el texto generado por el modelo.
            contenido = datos["message"]["content"]

            # Muestra el texto inmediatamente, sin crear una línea nueva.
            print(contenido, end="", flush=True)

    print()