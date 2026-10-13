
import re
import unicodedata


# Define las intenciones sociales que puede reconocer el servicio.
INTENCION_SALUDO = "saludo"
INTENCION_AGRADECIMIENTO = "agradecimiento"
INTENCION_DESPEDIDA = "despedida"
INTENCION_AGRADECIMIENTO_DESPEDIDA = "agradecimiento_despedida"


# Normaliza el texto para comparar sin depender de mayúsculas, tildes,
# signos de puntuación o repeticiones exageradas de letras.
def normalizar_mensaje(mensaje: str) -> str:
    texto = mensaje.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"(.)\1{2,}", r"\1\1", texto)
    return re.sub(r"\s+", " ", texto).strip()


# Agrupa expresiones de despedida habituales, incluidas algunas informales.
PATRONES_DESPEDIDA = (
    r"\badios\b",
    r"\bchao\b",
    r"\bbye(?: bye)?\b",
    r"\bhasta luego\b",
    r"\bhasta pronto\b",
    r"\bhasta la proxima\b",
    r"\bnos vemos\b",
    r"\bahí nos vemos\b",
    r"\bahi nos vemos\b",
    r"\bnos pillamos\b",
    r"\bahi nos pillamos\b",
    r"\bhablamos luego\b",
    r"\bhablamos despues\b",
    r"\bme tengo que ir\b",
    r"\btengo que irme\b",
    r"\bya me voy\b",
    r"\bme voy\b",
    r"\bdebo irme\b",
    r"\bme retiro\b",
    r"\bhasta aqui llegamos por hoy\b",
    r"\bque tengas buen dia\b",
    r"\bque pases buena tarde\b",
    r"\bque descanses\b",
    r"\bque tengas buena noche\b",
    r"\bfeliz noche\b",
    r"\bque te vaya bien\b",
    r"\bque estes muy bien\b",
    r"\bcuidate mucho\b",
    r"\bbueno eso es todo por ahora\b",
    r"\blisto eso era todo\b",
    r"\bno necesito nada mas\b",
)


# Identifica solicitudes de información sin confundir expresiones sociales
# como "¿Qué más?" o "¿Cómo estás?" con consultas documentales.
def contiene_consulta(mensaje: str) -> bool:
    texto = normalizar_mensaje(mensaje)

    if not texto:
        return False

    patrones_consulta = (
        r"\bque es\b",
        r"\bque son\b",
        r"\bque significa\b",
        r"\bque documentos\b",
        r"\bque requisitos\b",
        r"\bque necesito\b",
        r"\bque debo\b",
        r"\bque puedo\b",
        r"\bque permite\b",
        r"\bque funciones\b",
        r"\bque informacion\b",
        r"\bcomo puedo\b",
        r"\bcomo hago\b",
        r"\bcomo se\b",
        r"\bcomo funciona\b",
        r"\bcomo recupero\b",
        r"\bcomo actualizo\b",
        r"\bcomo publico\b",
        r"\bcomo me registro\b",
        r"\bdonde puedo\b",
        r"\bdonde encuentro\b",
        r"\bcuando puedo\b",
        r"\bpor que\b",
        r"\bpara que\b",
        r"\bquien puede\b",
        r"\bcual es\b",
        r"\bcuales son\b",
        r"\bcuanto cuesta\b",
        r"\bexplica\b",
        r"\bexplicame\b",
        r"\binforma(?:me)?\b",
        r"\bindica(?:me)?\b",
        r"\bayuda(?:me)?\b",
        r"\bnecesito informacion\b",
        r"\bnecesito ayuda\b",
        r"\bquiero saber\b",
        r"\bquiero conocer\b",
        r"\bpasos para\b",
        r"\brequisitos para\b",
        r"\bcomo registr",
        r"\bcomo solicit",
        r"\bcomo inscrib",
        r"\bcomo cambiar\b",
        r"\bcomo actualizar\b",
        r"\bcomo configurar\b",
        r"\bcomo ingresar\b",
        r"\bcomo acceder\b",
        r"\bcomo usar\b",
        r"\bcomo conectar\b",
        r"\bcomo publicar\b",
        r"\bcomo crear\b",
        r"\bcomo eliminar\b",
        r"\bcomo editar\b",
        r"\bcomo descargar\b",
        r"\bcomo subir\b",
        r"\bcomo enviar\b",
        r"\bcomo contactar\b",
        r"\bsoporte tecnico\b",
        r"\bcontraseña\b",
        r"\bcontrasena\b",
        r"\bdime\b",
        r"\bdime como\b",
        r"\bdime que\b",
        r"\bnecesito ayuda\b",
        r"\bnecesito saber\b",
        r"\bcomo cambio\b",
        r"\bcomo puedo cambiar\b",
        r"\bcomo modifico\b",
        r"\bcomo puedo modificar\b",
    )

    return any(re.search(patron, texto) for patron in patrones_consulta)


# Reconoce saludos breves, ampliados e informales.
def es_saludo(texto: str) -> bool:
    patrones_saludo = (
        r"^(hol+a{0,2}|hol+i{0,2}|hey|ey|quiubo)(?:\s+\w+){0,3}$",
        r"^(buenas|buenos dias|buenas tardes|buenas noches)"
        r"(?:\s+\w+){0,3}$",
        r"^que mas(?: pues)?$",
        r"^que hubo$",
        r"^todo bien(?: todo bien)?$",
        r"^como estas$",
        r"^como te va$",
        r"^como te va todo$",
        r"^como vas$",
        r"^como te ha ido$",
        r"^como vamos$",
        r"^como andas$",
        r"^como va todo$",
        r"^como va la vuelta$",
        r"^que cuentas$",
        r"^que me cuentas$",
        r"^que se dice$",
        r"^como esta la cosa$",
        r"^todo en orden$",
        r"^hola de nuevo$",
        r"^volvi hola$",
        r"^un cordial saludo$",
        r"^recibe un saludo$",
    )

    return any(re.fullmatch(patron, texto) for patron in patrones_saludo)


# Identifica la intención principal sin interceptar preguntas documentales.
def detectar_intencion(mensaje: str) -> str | None:
    texto = normalizar_mensaje(mensaje)

    if not texto:
        return None

    # Las consultas documentales siempre deben continuar hacia el RAG.
    if contiene_consulta(mensaje):
        return None

    contiene_agradecimiento = bool(
        re.search(
            r"\b(gracias|agradezco|agradecerte|agradecerle)\b",
            texto,
        )
    )

    contiene_despedida = any(
        re.search(patron, texto)
        for patron in PATRONES_DESPEDIDA
    )

    # Si aparecen ambas expresiones sociales, devuelve la intención combinada.
    if contiene_agradecimiento and contiene_despedida:
        return INTENCION_AGRADECIMIENTO_DESPEDIDA

    if contiene_agradecimiento:
        return INTENCION_AGRADECIMIENTO

    if contiene_despedida:
        return INTENCION_DESPEDIDA

    if es_saludo(texto):
        return INTENCION_SALUDO

    return None


# Devuelve la respuesta correspondiente a cada intención reconocida.
def obtener_respuesta_intencion(intencion: str) -> str | None:
    respuestas = {
        INTENCION_SALUDO: "¡Hola! ¿En qué puedo ayudarte?",
        INTENCION_AGRADECIMIENTO: (
            "¡Con gusto! ¿En qué más puedo ayudarte?"
        ),
        INTENCION_DESPEDIDA: (
            "¡Hasta luego! Estoy aquí si necesitas ayuda."
        ),
        INTENCION_AGRADECIMIENTO_DESPEDIDA: (
            "¡Con mucho gusto! ¡Hasta luego, aquí estaré si me necesitas!"
        ),
    }

    return respuestas.get(intencion)
