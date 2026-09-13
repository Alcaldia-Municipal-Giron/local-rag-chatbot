import json
from pathlib import Path


# Define la ubicación del archivo donde se almacenan las conversaciones.
ARCHIVO_CONVERSACIONES = Path("data/conversations.json")


# Carga todas las conversaciones almacenadas en el archivo JSON.
def cargar_conversaciones():
    with open(ARCHIVO_CONVERSACIONES, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


# Guarda todas las conversaciones en el archivo JSON.
def guardar_conversaciones(conversaciones):
    with open(ARCHIVO_CONVERSACIONES, "w", encoding="utf-8") as archivo:
        json.dump(conversaciones, archivo, ensure_ascii=False, indent=4)


# Obtiene el historial de una sesión; si no existe, crea una conversación vacía.
def obtener_historial(session_id):
    conversaciones = cargar_conversaciones()

    if session_id not in conversaciones:
        conversaciones[session_id] = []
        guardar_conversaciones(conversaciones)

    return conversaciones[session_id]


# Agrega un mensaje al historial de una sesión y guarda el cambio.
def agregar_mensaje(session_id, mensaje):
    conversaciones = cargar_conversaciones()

    if session_id not in conversaciones:
        conversaciones[session_id] = []

    conversaciones[session_id].append(mensaje)

    guardar_conversaciones(conversaciones)