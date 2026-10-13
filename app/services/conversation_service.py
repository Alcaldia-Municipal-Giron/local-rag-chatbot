import json
import threading
from pathlib import Path


# Define la ubicación del archivo donde se almacenan las conversaciones activas.
ARCHIVO_CONVERSACIONES = Path("data/conversations.json")

# Define la ubicación del archivo donde se almacenan los turnos archivados.
ARCHIVO_ARCHIVO_CONVERSACIONES = Path("data/conversation_archive.json")

# Define cuántos turnos completos permanecerán en la conversación activa.
# El turno actual se conserva junto con el turno inmediatamente anterior.
MAX_TURNOS_ACTIVOS = 2

# Evita que varias solicitudes del mismo proceso modifiquen los archivos
# de conversaciones al mismo tiempo.
# RLock permite que una función protegida pueda llamar a otra función protegida.
bloqueo_conversaciones = threading.RLock()


# Carga todas las conversaciones activas almacenadas en el archivo JSON.
def cargar_conversaciones():
    with open(ARCHIVO_CONVERSACIONES, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


# Guarda todas las conversaciones activas mediante un archivo temporal.
# Después reemplaza el archivo original para evitar escrituras incompletas.
def guardar_conversaciones(conversaciones):
    ARCHIVO_CONVERSACIONES.parent.mkdir(parents=True, exist_ok=True)

    archivo_temporal = ARCHIVO_CONVERSACIONES.with_suffix(".tmp")

    with open(archivo_temporal, "w", encoding="utf-8") as archivo:
        json.dump(conversaciones, archivo, ensure_ascii=False, indent=4)

    archivo_temporal.replace(ARCHIVO_CONVERSACIONES)

# Carga el archivo de conversaciones archivadas.
#
# Si el archivo todavía no existe o está vacío, devuelve un diccionario
# vacío para que el sistema pueda inicializarlo automáticamente.
def cargar_conversaciones_archivadas():
    if not ARCHIVO_ARCHIVO_CONVERSACIONES.exists():
        return {}

    # Lee el contenido completo del archivo para poder comprobar
    # si realmente contiene información antes de intentar convertirlo
    # desde JSON.
    with open(
        ARCHIVO_ARCHIVO_CONVERSACIONES,
        "r",
        encoding="utf-8"
    ) as archivo:
        contenido = archivo.read().strip()

    # Un archivo vacío todavía no contiene ninguna conversación archivada.
    if not contenido:
        return {}

    return json.loads(contenido)


# Guarda las conversaciones archivadas mediante un archivo temporal.
# Esto mantiene la misma protección utilizada para conversations.json.
def guardar_conversaciones_archivadas(conversaciones_archivadas):
    ARCHIVO_ARCHIVO_CONVERSACIONES.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    archivo_temporal = ARCHIVO_ARCHIVO_CONVERSACIONES.with_suffix(".tmp")

    with open(
        archivo_temporal,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            conversaciones_archivadas,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    archivo_temporal.replace(ARCHIVO_ARCHIVO_CONVERSACIONES)


# Separa el historial de una sesión en turnos completos.
#
# Un turno termina cuando aparece un mensaje del asistente.
# Por ejemplo:
#
# usuario
# usuario
# asistente
#
# se considera un único turno.
#
# Si al final existe un mensaje de usuario sin respuesta del asistente,
# permanece como un turno incompleto y no se archiva.
def separar_turnos(historial):
    turnos_completos = []
    turno_actual = []

    for mensaje in historial:
        turno_actual.append(mensaje)

        # La respuesta del asistente marca el final del turno.
        if mensaje["role"] == "assistant":
            turnos_completos.append(turno_actual)
            turno_actual = []

    return turnos_completos, turno_actual


# Archiva los turnos antiguos de una sesión cuando se supera
# la cantidad máxima de turnos activos.
#
# Ejemplo:
#
# Antes:
#   Turno 1
#   Turno 2
#   Turno 3
#
# Después:
#   conversations.json:
#       Turno 2
#       Turno 3
#
#   conversation_archive.json:
#       Turno 1
#
# El archivado solamente se realiza sobre turnos completos.
def archivar_turnos_antiguos(session_id, historial):
    turnos_completos, turno_incompleto = separar_turnos(historial)

    # Si todavía no se supera el límite de turnos activos,
    # no hay nada que archivar.
    if len(turnos_completos) <= MAX_TURNOS_ACTIVOS:
        return historial

    # Obtiene todos los turnos que deben salir de la conversación activa.
    turnos_a_archivar = turnos_completos[:-MAX_TURNOS_ACTIVOS]

    # Conserva solamente los turnos más recientes.
    turnos_activos = turnos_completos[-MAX_TURNOS_ACTIVOS:]

    # Si existe un mensaje de usuario pendiente de respuesta,
    # se conserva en la conversación activa.
    if turno_incompleto:
        turnos_activos.append(turno_incompleto)

    # Carga el archivo donde se almacenan los turnos antiguos.
    conversaciones_archivadas = cargar_conversaciones_archivadas()

    # Crea la sesión en el archivo de archivado si todavía no existe.
    if session_id not in conversaciones_archivadas:
        conversaciones_archivadas[session_id] = []

    # Agrega los turnos antiguos al historial archivado de esa sesión.
    for turno in turnos_a_archivar:
        conversaciones_archivadas[session_id].extend(turno)

    # Guarda el archivo de archivado.
    guardar_conversaciones_archivadas(conversaciones_archivadas)

    # Reconstruye el historial activo manteniendo el mismo formato
    # utilizado actualmente por conversations.json.
    historial_activo = []

    for turno in turnos_activos:
        historial_activo.extend(turno)

    return historial_activo


# Obtiene el historial de una sesión; si no existe, crea una conversación vacía.
def obtener_historial(session_id):
    with bloqueo_conversaciones:
        conversaciones = cargar_conversaciones()

        if session_id not in conversaciones:
            conversaciones[session_id] = []
            guardar_conversaciones(conversaciones)

        return conversaciones[session_id]


# Obtiene únicamente los últimos turnos completos de una sesión.
#
# Los mensajes que todavía no tienen respuesta del asistente no se
# consideran un turno completo.
def obtener_historial_reciente(session_id, cantidad_turnos=2):
    historial = obtener_historial(session_id)

    turnos, _ = separar_turnos(historial)

    # Selecciona solamente los turnos más recientes solicitados.
    turnos_recientes = turnos[-cantidad_turnos:]

    historial_reciente = []

    # Convierte nuevamente los turnos en una lista de mensajes.
    for turno in turnos_recientes:
        historial_reciente.extend(turno)

    return historial_reciente


# Agrega un mensaje al historial de una sesión y guarda el cambio.
#
# El archivado se ejecuta después de guardar el mensaje.
# Por lo tanto, cuando se guarda la respuesta del asistente,
# el turno queda completo y en ese momento puede activarse el FIFO.
def agregar_mensaje(session_id, mensaje):
    with bloqueo_conversaciones:
        conversaciones = cargar_conversaciones()

        if session_id not in conversaciones:
            conversaciones[session_id] = []

        # Agrega el nuevo mensaje al historial de la sesión.
        conversaciones[session_id].append(mensaje)

        # Guarda primero el mensaje para asegurar que el turno actual
        # quede registrado antes de realizar el archivado.
        guardar_conversaciones(conversaciones)

        # Ejecuta el archivado después de guardar el mensaje.
        #
        # Si el mensaje es del usuario y todavía no existe una respuesta,
        # el turno permanece incompleto y no se archiva.
        #
        # Cuando posteriormente se guarda el mensaje del asistente,
        # el turno queda completo y puede realizarse el desplazamiento FIFO.
        historial_actualizado = archivar_turnos_antiguos(
            session_id,
            conversaciones[session_id]
        )

        # Si el archivado produjo cambios, actualiza la sesión activa
        # y vuelve a guardar conversations.json.
        if historial_actualizado != conversaciones[session_id]:
            conversaciones[session_id] = historial_actualizado
            guardar_conversaciones(conversaciones)