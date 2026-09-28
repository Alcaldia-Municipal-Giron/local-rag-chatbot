import json
import httpx

from app.rag.retriever import recuperar_contexto


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOP_K = 3

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

OLLAMA_MODEL = "qwen2.5-coder:3b-instruct"

OLLAMA_TIMEOUT = 500.0


# ============================================================
# PREGUNTAS CON CONTEXTO SUFICIENTE
#
# Estas preguntas deberían poder responderse utilizando
# directamente la información recuperada desde los documentos.
# ============================================================

PREGUNTAS_RESPONDIBLES = [
    "¿Qué es GAIA?",
    "¿Qué información debe registrar un artista?",
    "¿Qué información debe registrar un prestador turístico?",
    "¿Cuántas fotografías puede subir un prestador turístico?",
    "¿Cómo se registra un nuevo prestador de servicios turísticos?",
    "¿Cómo se registra un artista?",
    "¿Qué estados puede tener un registro?",
    "¿Qué puede hacer un funcionario dentro de GAIA?",
    "¿Cómo se busca un artista en GAIA?",
    "¿Cómo se busca un sitio turístico en GAIA?",
]


# ============================================================
# PREGUNTAS RELACIONADAS PERO SIN INFORMACIÓN SUFICIENTE
#
# Estas preguntas tienen relación con GAIA o la Alcaldía,
# pero el contexto recuperado probablemente no contiene
# la información necesaria para responderlas.
# ============================================================

PREGUNTAS_NO_RESPONDIBLES = [
    "¿Cuál es el horario de atención de la Alcaldía?",
    "¿Cuál es la dirección de la Alcaldía de Girón?",
    "¿Cuál es el número de teléfono de la Alcaldía?",
    "¿Quién revisa exactamente la información enviada?",
    "¿Cuál es el tiempo que tarda la aprobación de un registro?",
    "¿Qué requisitos legales necesita un artista para registrarse?",
    "¿Los datos registrados en GAIA son públicos?",
    "¿GAIA permite descargar certificados?",
    "¿Cuánto cuesta registrarse como prestador turístico?",
    "¿Cuál es el correo oficial de atención de la Alcaldía?",
]


# ============================================================
# PREGUNTAS COMPLETAMENTE EXTERNAS
#
# El contexto recuperado será de GAIA, pero no debería contener
# información suficiente para responder estas preguntas.
# ============================================================

PREGUNTAS_EXTERNAS = [
    "¿Cuál es la capital de Japón?",
    "¿Quién escribió Cien años de soledad?",
    "¿Cuál es la población de Colombia?",
    "¿Cuál es el planeta más grande del sistema solar?",
    "¿Cómo funciona la fotosíntesis?",
    "¿Cuál es la fórmula del teorema de Pitágoras?",
    "¿Cómo instalar Python en Windows?",
    "¿Qué es Docker?",
    "¿Cómo funciona PostgreSQL?",
    "¿Qué es inteligencia artificial generativa?",
]


# ============================================================
# FUNCIÓN PARA CONSTRUIR EL CONTEXTO
#
# Aquí NO utilizamos el context_builder.py de producción.
# Construimos el contexto directamente para que esta prueba
# sea independiente y no modifique ninguna parte del sistema.
# ============================================================

def construir_contexto_prueba(resultados: list) -> str:
    """
    Construye el contexto que será enviado a Qwen para evaluar
    si contiene información suficiente para responder la pregunta.
    """

    fragmentos = []

    for posicion, resultado in enumerate(
        resultados,
        start=1
    ):
        fragmento = (
            f"[Fragmento {posicion}]\n"
            f"{resultado['text']}"
        )

        fragmentos.append(fragmento)

    return "\n\n".join(fragmentos)


# ============================================================
# EVALUACIÓN DE ANSWERABILITY
#
# Qwen NO responde la pregunta.
#
# Solamente determina:
#
# RESPONDIBLE
# NO_RESPONDIBLE
#
# utilizando exclusivamente el contexto recibido.
# ============================================================

def evaluar_answerability(
    pregunta: str,
    contexto: str
) -> dict:

    prompt = f"""
Eres un evaluador de contexto para un sistema RAG.

Tu única tarea es determinar si el CONTEXTO contiene
información suficiente para responder la PREGUNTA.

NO respondas la pregunta.

NO utilices conocimiento externo.

NO completes información faltante mediante inferencias.

Considera que el contexto es suficiente solamente cuando
contiene información explícita que permita construir una
respuesta respaldada por los fragmentos proporcionados.

Si el contexto solamente habla de un tema relacionado,
pero no contiene la información necesaria para responder
la pregunta, debes clasificarlo como NO_RESPONDIBLE.

Debes responder ÚNICAMENTE con un objeto JSON válido
utilizando exactamente esta estructura:

{{
    "answerable": true,
    "reason": "breve explicación"
}}

o:

{{
    "answerable": false,
    "reason": "breve explicación"
}}

PREGUNTA:
{pregunta}

CONTEXTO:
{contexto}
"""

    try:

        with httpx.Client(
            timeout=OLLAMA_TIMEOUT
        ) as client:

            respuesta = client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Evalúa únicamente la "
                                "suficiencia del contexto."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "top_p": 1.0,
                        "top_k": 1,
                        "seed": 42,
                        "num_predict": 120,
                        "num_ctx": 4096
                    }
                }
            )

        respuesta.raise_for_status()

        datos = respuesta.json()

        contenido = datos["message"]["content"].strip()

        # ----------------------------------------------------
        # Intentamos extraer JSON directamente.
        # ----------------------------------------------------

        try:
            resultado = json.loads(contenido)

        except json.JSONDecodeError:

            # ------------------------------------------------
            # Algunos modelos pueden envolver el JSON dentro
            # de texto adicional.
            # ------------------------------------------------

            inicio = contenido.find("{")
            final = contenido.rfind("}")

            if inicio == -1 or final == -1:
                return {
                    "answerable": None,
                    "reason": (
                        "Qwen no devolvió un JSON válido."
                    ),
                    "raw": contenido
                }

            json_texto = contenido[
                inicio:final + 1
            ]

            try:
                resultado = json.loads(
                    json_texto
                )

            except json.JSONDecodeError:

                return {
                    "answerable": None,
                    "reason": (
                        "No fue posible interpretar "
                        "la evaluación de Qwen."
                    ),
                    "raw": contenido
                }

        answerable = resultado.get(
            "answerable"
        )

        reason = resultado.get(
            "reason",
            ""
        )

        if not isinstance(
            answerable,
            bool
        ):
            answerable = None

        return {
            "answerable": answerable,
            "reason": str(reason),
            "raw": contenido
        }

    except httpx.RequestError as error:

        return {
            "answerable": None,
            "reason": (
                f"Error conectando con Ollama: {error}"
            ),
            "raw": ""
        }


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

def imprimir_resultado(
    numero: int,
    categoria: str,
    pregunta: str,
    resultados: list,
    evaluacion: dict
):
    """
    Imprime toda la información relevante de una evaluación.
    """

    print()
    print("=" * 80)

    print(
        f"{categoria} #{numero}"
    )

    print("=" * 80)

    print()
    print("Pregunta:")
    print(pregunta)

    # --------------------------------------------------------
    # Resultados de retrieval
    # --------------------------------------------------------

    print()
    print("RETRIEVAL")
    print("-" * 80)

    if not resultados:

        print(
            "No se recuperaron resultados."
        )

    else:

        for posicion, resultado in enumerate(
            resultados,
            start=1
        ):

            distancia = resultado[
                "distance"
            ]

            similitud = (
                1 - distancia
            ) * 100

            print(
                f"Top-{posicion}: "
                f"distance={distancia:.6f} | "
                f"similarity={similitud:.2f}%"
            )

            print(
                f"Chunk ID: "
                f"{resultado['id']}"
            )

            print(
                f"Texto: "
                f"{resultado['text'][:180]}"
            )

            if len(
                resultado["text"]
            ) > 180:
                print("...")

            print()

    # --------------------------------------------------------
    # Answerability
    # --------------------------------------------------------

    print()
    print("ANSWERABILITY")
    print("-" * 80)

    answerable = evaluacion.get(
        "answerable"
    )

    if answerable is True:

        print(
            "DECISIÓN: RESPONDIBLE"
        )

    elif answerable is False:

        print(
            "DECISIÓN: NO_RESPONDIBLE"
        )

    else:

        print(
            "DECISIÓN: ERROR DE EVALUACIÓN"
        )

    print()
    print(
        "Razón:"
    )

    print(
        evaluacion.get(
            "reason",
            ""
        )
    )


# ============================================================
# EJECUTAR CATEGORÍA
# ============================================================

def ejecutar_categoria(
    nombre: str,
    preguntas: list[str]
):

    resultados_categoria = []

    print()
    print()
    print("#" * 80)
    print(
        f"CATEGORÍA: {nombre}"
    )
    print("#" * 80)

    for numero, pregunta in enumerate(
        preguntas,
        start=1
    ):

        # ----------------------------------------------------
        # 1. Recuperar contexto
        # ----------------------------------------------------

        resultados = recuperar_contexto(
            pregunta,
            top_k=TOP_K
        )

        # ----------------------------------------------------
        # 2. Construir contexto
        # ----------------------------------------------------

        contexto = construir_contexto_prueba(
            resultados
        )

        # ----------------------------------------------------
        # 3. Evaluar suficiencia
        # ----------------------------------------------------

        evaluacion = evaluar_answerability(
            pregunta,
            contexto
        )

        # ----------------------------------------------------
        # 4. Mostrar resultado
        # ----------------------------------------------------

        imprimir_resultado(
            numero=numero,
            categoria=nombre,
            pregunta=pregunta,
            resultados=resultados,
            evaluacion=evaluacion
        )

        resultados_categoria.append(
            {
                "pregunta": pregunta,
                "resultados": resultados,
                "evaluacion": evaluacion
            }
        )

    return resultados_categoria


# ============================================================
# ESTADÍSTICAS
# ============================================================

def mostrar_estadisticas(
    nombre: str,
    resultados: list
):

    total = len(resultados)

    respondibles = sum(
        1
        for resultado in resultados
        if resultado["evaluacion"][
            "answerable"
        ] is True
    )

    no_respondibles = sum(
        1
        for resultado in resultados
        if resultado["evaluacion"][
            "answerable"
        ] is False
    )

    errores = sum(
        1
        for resultado in resultados
        if resultado["evaluacion"][
            "answerable"
        ] is None
    )

    print()
    print("=" * 80)
    print(
        f"ESTADÍSTICAS - {nombre}"
    )
    print("=" * 80)

    print(
        f"Total: {total}"
    )

    print(
        f"RESPONDIBLE: "
        f"{respondibles}/{total}"
    )

    print(
        f"NO_RESPONDIBLE: "
        f"{no_respondibles}/{total}"
    )

    print(
        f"ERRORES: "
        f"{errores}/{total}"
    )


# ============================================================
# TEST PRINCIPAL
# ============================================================

def test_context_answerability():

    print()
    print()
    print("#" * 80)
    print("# PRUEBA DE ANSWERABILITY / SUFICIENCIA DEL CONTEXTO")
    print("#" * 80)

    print()
    print(
        "Esta prueba NO modifica retriever.py."
    )

    print(
        "Esta prueba NO modifica chat.py."
    )

    print(
        "Qwen NO responderá las preguntas."
    )

    print(
        "Qwen solamente evaluará si el contexto recuperado"
    )

    print(
        "contiene información suficiente para responder."
    )

    # ========================================================
    # RESPONDIBLES
    # ========================================================

    respondibles = ejecutar_categoria(
        "RESPONDIBLE",
        PREGUNTAS_RESPONDIBLES
    )

    # ========================================================
    # NO RESPONDIBLES
    # ========================================================

    no_respondibles = ejecutar_categoria(
        "NO RESPONDIBLE / RELACIONADA",
        PREGUNTAS_NO_RESPONDIBLES
    )

    # ========================================================
    # EXTERNAS
    # ========================================================

    externas = ejecutar_categoria(
        "EXTERNA",
        PREGUNTAS_EXTERNAS
    )

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    mostrar_estadisticas(
        "RESPONDIBLES",
        respondibles
    )

    mostrar_estadisticas(
        "NO RESPONDIBLES / RELACIONADAS",
        no_respondibles
    )

    mostrar_estadisticas(
        "EXTERNAS",
        externas
    )

    # ========================================================
    # MATRIZ DE RESULTADOS
    # ========================================================

    todos = [
        (
            "RESPONDIBLE",
            resultado
        )
        for resultado in respondibles
    ]

    todos.extend(
        [
            (
                "NO_RESPONDIBLE",
                resultado
            )
            for resultado in no_respondibles
        ]
    )

    todos.extend(
        [
            (
                "EXTERNA",
                resultado
            )
            for resultado in externas
        ]
    )

    print()
    print()
    print("#" * 80)
    print("# MATRIZ FINAL")
    print("#" * 80)

    print()
    print(
        f"{'CATEGORÍA':<20}"
        f"{'RESULTADO':<20}"
        f"{'DISTANCIA':<15}"
        f" PREGUNTA"
    )

    print("-" * 100)

    for categoria, resultado in todos:

        pregunta = resultado[
            "pregunta"
        ]

        evaluacion = resultado[
            "evaluacion"
        ]

        answerable = evaluacion[
            "answerable"
        ]

        if answerable is True:

            decision = "RESPONDIBLE"

        elif answerable is False:

            decision = "NO_RESPONDIBLE"

        else:

            decision = "ERROR"

        resultados_retrieval = resultado[
            "resultados"
        ]

        if resultados_retrieval:

            distancia = resultados_retrieval[
                0
            ]["distance"]

            distancia_texto = (
                f"{distancia:.6f}"
            )

        else:

            distancia_texto = "-"

        print(
            f"{categoria:<20}"
            f"{decision:<20}"
            f"{distancia_texto:<15}"
            f" {pregunta}"
        )

    # ========================================================
    # MATRIZ DE CONFUSIÓN
    # ========================================================

    print()
    print()
    print("#" * 80)
    print("# MATRIZ DE CONFUSIÓN")
    print("#" * 80)

    # --------------------------------------------------------
    # Respondibles correctamente identificadas
    # --------------------------------------------------------

    true_positive = sum(
        1
        for resultado in respondibles
        if resultado["evaluacion"][
            "answerable"
        ] is True
    )

    # --------------------------------------------------------
    # Respondibles clasificadas incorrectamente
    # --------------------------------------------------------

    false_negative = sum(
        1
        for resultado in respondibles
        if resultado["evaluacion"][
            "answerable"
        ] is False
    )

    # --------------------------------------------------------
    # No respondibles correctamente rechazadas
    # --------------------------------------------------------

    true_negative = sum(
        1
        for resultado in (
            no_respondibles + externas
        )
        if resultado["evaluacion"][
            "answerable"
        ] is False
    )

    # --------------------------------------------------------
    # No respondibles clasificadas como respondibles
    # --------------------------------------------------------

    false_positive = sum(
        1
        for resultado in (
            no_respondibles + externas
        )
        if resultado["evaluacion"][
            "answerable"
        ] is True
    )

    print()
    print(
        f"True Positive: "
        f"{true_positive}"
    )

    print(
        f"False Negative: "
        f"{false_negative}"
    )

    print(
        f"True Negative: "
        f"{true_negative}"
    )

    print(
        f"False Positive: "
        f"{false_positive}"
    )

    # ========================================================
    # ASSERT
    # ========================================================

    assert True