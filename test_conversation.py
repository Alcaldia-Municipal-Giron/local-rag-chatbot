from app.services.conversation_service import (
    obtener_historial,
    agregar_mensaje
)


# Prueba la creación y recuperación de una conversación.
historial = obtener_historial("sesion-prueba")

print("Historial inicial:")
print(historial)


# Agrega un mensaje de prueba a la conversación.
agregar_mensaje(
    "sesion-prueba",
    {
        "role": "user",
        "content": "Hola, esta es una prueba."
    }
)


# Recupera nuevamente el historial después de guardar el mensaje.
historial = obtener_historial("sesion-prueba")

print("\nHistorial después de guardar:")
print(historial)