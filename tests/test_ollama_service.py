from app.services.ollama_service import generar_respuesta


def test_generar_respuesta():
    messages = [
        {
            "role": "user",
            "content": "Responde únicamente: Hola.",
        }
    ]

    fragmentos = list(generar_respuesta(messages))
    respuesta = "".join(fragmentos)

    print("Respuesta:", respuesta)

    assert respuesta.strip()