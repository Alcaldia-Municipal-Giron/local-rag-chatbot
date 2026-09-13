import httpx


# Envía una pregunta a FastAPI y recibe la respuesta progresivamente.
with httpx.stream(
    "POST",
    "http://127.0.0.1:8000/chat",
    json={
        "message": "Explícame brevemente qué es Python."
    },
    timeout=120.0
) as respuesta:

    print("Respuesta de FastAPI:")
    print()

    # Comprueba que FastAPI respondió correctamente.
    respuesta.raise_for_status()

    # Procesa cada fragmento de texto que FastAPI va enviando.
    for fragmento in respuesta.iter_text():

        if fragmento:
            print(fragmento, end="", flush=True)

    print()