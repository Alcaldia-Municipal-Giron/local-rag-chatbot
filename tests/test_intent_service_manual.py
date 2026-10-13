import sys
from pathlib import Path


# Agrega la raíz del proyecto a las rutas de búsqueda de Python.
# Esto permite importar el paquete app al ejecutar el script desde tests.
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROYECTO))

from app.services.intent_service import (
    detectar_intencion,
    obtener_respuesta_intencion,
)


# ============================================================
# MENSAJES DE PRUEBA: 50 SALUDOS Y 50 DESPEDIDAS
# Enfoque: español general y expresiones colombianas.
# ============================================================

mensajes_prueba = [

    # ========================================================
    # 50 SALUDOS
    # ========================================================

    # Saludos básicos y comunes
    "Hola",
    "Hola, ¿cómo estás?",
    "Hola, ¿cómo te va?",
    "Hola, buenos días",
    "Hola, buenas tardes",
    "Hola, buenas noches",
    "Buenos días",
    "Buenas tardes",
    "Buenas noches",
    "Buenas",

    # Saludos informales
    "Holaaa",
    "Holaaaa, ¿qué tal?",
    "Holi",
    "Holiii",
    "Hey",
    "Hey, ¿cómo vas?",
    "Ey, hola",
    "Quiubo",
    "Quiubo, ¿cómo estás?",
    "Quiubo pues",

    # Expresiones colombianas
    "¿Qué más?",
    "¿Qué más pues?",
    "¿Qué más, cómo vamos?",
    "¿Qué hubo?",
    "¿Quiubo, parce?",
    "Hola, parce",
    "Buenas, parcero",
    "Buenas, parceros",
    "¿Todo bien o qué?",
    "¿Todo bien, todo bien?",

    # Saludos cercanos y coloquiales
    "¿Cómo va todo?",
    "¿Cómo te ha ido?",
    "¿Cómo vamos?",
    "¿Cómo andas?",
    "¿Cómo va la vuelta?",
    "¿Qué cuentas?",
    "¿Qué me cuentas?",
    "¿Qué se dice?",
    "¿Cómo está la cosa?",
    "¿Todo en orden?",

    # Saludos formales o dirigidos al chatbot
    "Un cordial saludo",
    "Recibe un saludo",
    "Hola, estimado asistente",
    "Buenos días, asistente",
    "Buenas tardes, chatbot",
    "Hola, ¿hay alguien ahí?",
    "Hola, ¿me puedes atender?",
    "Hola, estoy por aquí",
    "Hola de nuevo",
    "Volví, hola",


    # ========================================================
    # 50 DESPEDIDAS
    # ========================================================

    # Despedidas básicas
    "Adiós",
    "Hasta luego",
    "Hasta pronto",
    "Hasta la próxima",
    "Chao",
    "Chao, chao",
    "Chao pues",
    "Nos vemos",
    "Nos vemos luego",
    "Nos vemos pronto",

    # Despedidas informales
    "Bye",
    "Bye bye",
    "Bueno, chao",
    "Bueno, hasta luego",
    "Listo, chao",
    "Dale, chao",
    "Bueno, me voy",
    "Ya me voy",
    "Me tengo que ir",
    "Tengo que irme",

    # Expresiones colombianas
    "Bueno, parce, chao",
    "Hágale, chao",
    "Hágale pues, hasta luego",
    "Nos pillamos",
    "Nos pillamos luego",
    "Ahí nos vemos",
    "Ahí nos pillamos",
    "Bueno, mi pez, chao",
    "De una, chao",
    "Todo bien, nos vemos",

    # Despedidas por horario
    "Que tengas buen día",
    "Que pases buena tarde",
    "Que descanses",
    "Que tengas buena noche",
    "Feliz noche",
    "Feliz día, hasta luego",
    "Descansa, hablamos luego",
    "Que te vaya bien",
    "Que estés muy bien",
    "Cuídate mucho",

    # Despedidas por finalización de la conversación
    "Eso era todo, gracias",
    "Bueno, eso es todo por ahora",
    "Ya terminé, hasta luego",
    "Me retiro, muchas gracias",
    "Gracias por todo, adiós",
    "Muchas gracias, chao",
    "Listo, eso era todo",
    "No necesito nada más, gracias",
    "Hasta aquí llegamos por hoy",
    "Bueno, hablamos después",


    # ========================================================
    # CASOS MIXTOS: DEBEN CONTINUAR AL RAG
    # No hacen parte de los 50 saludos ni de las 50 despedidas.
    # Sirven para comprobar que no se pierdan las consultas.
    # ========================================================

    "Hola, ¿cómo me registro como artista?",
    "Buenas, necesito información sobre el registro",
    "Quiubo, parce, ¿qué es GAIA?",
    "Hola, ¿me explicas cómo funciona la plataforma?",
    "Buenos días, ¿cómo puedo recuperar mi contraseña?",
    "¿Qué más? Necesito ayuda con mi cuenta",
    "Hola, tengo una pregunta sobre los requisitos",
    "Buenas tardes, ¿cómo publico mi música?",
    "Gracias, ¿cómo me registro como artista?",
    "Chao, pero antes dime cómo cambio mi correo",
    "Bueno, me voy, pero necesito saber cómo registrarme",
    "Muchas gracias, ¿qué documentos necesito?",
    "Hasta luego, ¿me puedes explicar qué es GAIA?",
    "Hola, ¿dónde puedo encontrar soporte técnico?",
    "Quiubo, ¿cómo actualizo los datos de mi perfil?",
]


# ============================================================
# EJECUCIÓN DE LAS PRUEBAS
# ============================================================

for mensaje in mensajes_prueba:
    intencion = detectar_intencion(mensaje)

    respuesta = (
        obtener_respuesta_intencion(intencion)
        if intencion is not None
        else None
    )

    destino = (
        "RESPUESTA DIRECTA"
        if intencion is not None
        else "CONTINUAR AL RAG"
    )

    print("-" * 80)
    print(f"Mensaje:   {mensaje}")
    print(f"Intención: {intencion}")
    print(f"Destino:   {destino}")
    print(f"Respuesta: {respuesta}")