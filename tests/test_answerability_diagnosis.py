"""
Prueba diagnóstica de Answerability.

Objetivo:
Separar dos problemas diferentes:

A. ¿El retrieval recuperó información que realmente permite responder?
B. ¿Qwen reconoció correctamente que esa información permite responder?

Esta prueba NO modifica retriever.py ni chat.py.
"""

import json
import httpx

from app.rag.retriever import recuperar_contexto
from app.rag.context_builder import construir_contexto


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:3b-instruct"


# ---------------------------------------------------------------------------
# Preguntas que sabemos que deberían poder responderse con los documentos.
# ---------------------------------------------------------------------------

CASOS_RESPONDIBLES = [
    {
        "pregunta": "¿Qué es GAIA?",
        "evidencia_esperada": [
            "GAIA",
            "sistema",
            "gestionar",
        ],
    },
    {
        "pregunta": "¿Qué información debe registrar un artista?",
        "evidencia_esperada": [
            "datos personales",
            "trayectoria",
            "redes sociales",
        ],
    },
    {
        "pregunta": "¿Qué información debe registrar un prestador turístico?",
        "evidencia_esperada": [
            "nombre",
            "dirección",
            "teléfono",
            "correo",
        ],
    },
    {
        "pregunta": "¿Cuántas fotografías puede subir un prestador turístico?",
        "evidencia_esperada": [
            "6 fotografías",
        ],
    },
    {
        "pregunta": "¿Cómo se registra un nuevo prestador de servicios turísticos?",
        "evidencia_esperada": [
            "prestador",
            "servicios turísticos",
        ],
    },
    {
        "pregunta": "¿Cómo se registra un artista?",
        "evidencia_esperada": [
            "artista",
            "registro",
        ],
    },
    {
        "pregunta": "¿Qué estados puede tener un registro?",
        "evidencia_esperada": [
            "Pendiente",
            "Aprobado",
            "Rechazado",
        ],
    },
    {
        "pregunta": "¿Qué puede hacer un funcionario dentro de GAIA?",
        "evidencia_esperada": [
            "funcionario",
            "GAIA",
        ],
    },
    {
        "pregunta": "¿Cómo se busca un artista en GAIA?",
        "evidencia_esperada": [
            "Artistas",
            "búsqueda",
        ],
    },
    {
        "pregunta": "¿Cómo se busca un sitio turístico en GAIA?",
        "evidencia_esperada": [
            "Turismo",
            "búsqueda",
        ],
    },
]


# ---------------------------------------------------------------------------
# Preguntas que NO deberían poder responderse con los documentos actuales.
# ---------------------------------------------------------------------------

CASOS_NO_RESPONDIBLES = [
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


# ---------------------------------------------------------------------------
# Determina de forma simple si el contexto contiene evidencia esperada.
#
# Esto NO pretende reemplazar al modelo.
# Es una prueba de diagnóstico para comprobar si el texto recuperado
# contiene literalmente las pistas que esperamos encontrar.
# ---------------------------------------------------------------------------

def evaluar_retrieval(contexto: str, evidencias: list[str]) -> bool:
    contexto_normalizado = contexto.lower()

    encontradas = 0

    for evidencia in evidencias:
        if evidencia.lower() in contexto_normalizado:
            encontradas += 1

    # Para preguntas con varias evidencias exigimos al menos una.
    return encontradas > 0


# ---------------------------------------------------------------------------
# Pregunta a Qwen únicamente si el contexto permite responder.
# ---------------------------------------------------------------------------

def evaluar_answerability_qwen(pregunta: str, contexto: str) -> dict:

    prompt = f"""
Eres un evaluador de suficiencia de contexto para un sistema RAG.

Debes decidir ÚNICAMENTE si el contexto proporcionado contiene
información suficiente para responder la pregunta.

No utilices conocimiento externo.

IMPORTANTE:
- Si el contexto contiene directamente la información necesaria,
  responde true.
- Si el contexto contiene información relacionada pero no suficiente,
  responde false.
- No debes responder la pregunta.
- No debes completar información usando tus conocimientos.
- Debes analizar únicamente el contexto.

Pregunta:
{pregunta}

Contexto:
{contexto}

Responde ÚNICAMENTE con JSON válido:

{{
  "answerable": true,
  "reason": "explicación breve"
}}
"""

    respuesta = httpx.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 1,
                "top_k": 1,
                "seed": 42,
                "num_predict": 120,
                "num_ctx": 4096,
            },
        },
        timeout=500.0,
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    contenido = datos["message"]["content"].strip()

    # ---------------------------------------------------------------
    # Intentamos extraer JSON aunque el modelo agregue texto.
    # ---------------------------------------------------------------

    inicio = contenido.find("{")
    fin = contenido.rfind("}")

    if inicio == -1 or fin == -1:
        return {
            "answerable": None,
            "reason": f"Qwen no devolvió JSON válido: {contenido}",
        }

    try:
        resultado = json.loads(contenido[inicio:fin + 1])

        return {
            "answerable": bool(resultado.get("answerable")),
            "reason": resultado.get("reason", ""),
        }

    except json.JSONDecodeError:
        return {
            "answerable": None,
            "reason": f"JSON inválido: {contenido}",
        }


# ---------------------------------------------------------------------------
# Ejecuta un caso completo.
# ---------------------------------------------------------------------------

def ejecutar_caso(pregunta: str, evidencias: list[str], esperado: bool):

    print("\n" + "=" * 80)
    print(f"Pregunta: {pregunta}")
    print("=" * 80)

    resultados = recuperar_contexto(
        pregunta,
        top_k=3,
    )

    contexto = construir_contexto(resultados)

    distancia_top1 = resultados[0]["distance"]

    print("\nRETRIEVAL")
    print("-" * 80)

    for posicion, resultado in enumerate(resultados, start=1):

        similarity = 1 - resultado["distance"]

        print(
            f"Top-{posicion}: "
            f"distance={resultado['distance']:.6f} | "
            f"similarity={similarity:.2%} | "
            f"chunk={resultado['id']}"
        )

        print(
            resultado["text"][:300]
            .replace("\n", " ")
        )

    retrieval_ok = evaluar_retrieval(
        contexto,
        evidencias,
    )

    print("\nDIAGNÓSTICO DEL RETRIEVAL")
    print("-" * 80)

    if esperado:
        if retrieval_ok:
            print("RETRIEVAL_OK")
        else:
            print("RETRIEVAL_ERROR")
    else:
        if retrieval_ok:
            print(
                "RETRIEVAL_CONTIENE_EVIDENCIA "
                "(revisar manualmente)"
            )
        else:
            print("RETRIEVAL_CORRECTAMENTE_SIN_EVIDENCIA")

    # ---------------------------------------------------------------
    # Solo evaluamos Qwen cuando queremos estudiar el comportamiento
    # del clasificador.
    # ---------------------------------------------------------------

    qwen = evaluar_answerability_qwen(
        pregunta,
        contexto,
    )

    qwen_resultado = qwen["answerable"]

    print("\nANSWERABILITY DE QWEN")
    print("-" * 80)

    print(f"Qwen: {qwen_resultado}")
    print(f"Razón: {qwen['reason']}")

    # ---------------------------------------------------------------
    # Diagnóstico final.
    # ---------------------------------------------------------------

    print("\nDIAGNÓSTICO FINAL")
    print("-" * 80)

    if esperado:

        if retrieval_ok and qwen_resultado is True:
            diagnostico = "RETRIEVAL_OK + QWEN_OK"

        elif retrieval_ok and qwen_resultado is False:
            diagnostico = "RETRIEVAL_OK + QWEN_ERROR"

        elif not retrieval_ok:
            diagnostico = "RETRIEVAL_ERROR"

        else:
            diagnostico = "RESULTADO_INDETERMINADO"

    else:

        if qwen_resultado is False:
            diagnostico = "NO_RESPONDIBLE_CORRECTO"

        elif qwen_resultado is True:
            diagnostico = "QWEN_FALSO_POSITIVO"

        else:
            diagnostico = "QWEN_RESULTADO_INDETERMINADO"

    print(diagnostico)

    return {
        "pregunta": pregunta,
        "esperado": esperado,
        "distance": distancia_top1,
        "retrieval_ok": retrieval_ok,
        "qwen": qwen_resultado,
        "diagnostico": diagnostico,
    }


# ---------------------------------------------------------------------------
# Prueba principal.
# ---------------------------------------------------------------------------

def test_answerability_diagnosis():

    resultados = []

    print("\n")
    print("#" * 80)
    print("# DIAGNÓSTICO RETRIEVAL vs ANSWERABILITY")
    print("#" * 80)

    # ---------------------------------------------------------------
    # Casos respondibles.
    # ---------------------------------------------------------------

    print("\n")
    print("#" * 80)
    print("# CASOS RESPONDIBLES")
    print("#" * 80)

    for caso in CASOS_RESPONDIBLES:

        resultado = ejecutar_caso(
            pregunta=caso["pregunta"],
            evidencias=caso["evidencia_esperada"],
            esperado=True,
        )

        resultados.append(resultado)

    # ---------------------------------------------------------------
    # Casos no respondibles.
    # ---------------------------------------------------------------

    print("\n")
    print("#" * 80)
    print("# CASOS NO RESPONDIBLES")
    print("#" * 80)

    for pregunta in CASOS_NO_RESPONDIBLES:

        resultado = ejecutar_caso(
            pregunta=pregunta,
            evidencias=[],
            esperado=False,
        )

        resultados.append(resultado)

    # ---------------------------------------------------------------
    # Resumen.
    # ---------------------------------------------------------------

    print("\n")
    print("#" * 80)
    print("# RESUMEN DIAGNÓSTICO")
    print("#" * 80)

    diagnosticos = {}

    for resultado in resultados:

        diagnostico = resultado["diagnostico"]

        diagnosticos[diagnostico] = (
            diagnosticos.get(diagnostico, 0) + 1
        )

    for diagnostico, cantidad in diagnosticos.items():

        print(
            f"{diagnostico}: {cantidad}"
        )

    print("\n")
    print("#" * 80)
    print("# DETALLE")
    print("#" * 80)

    for resultado in resultados:

        print(
            f"{resultado['diagnostico']:35} | "
            f"distance={resultado['distance']:.6f} | "
            f"{resultado['pregunta']}"
        )

    # ---------------------------------------------------------------
    # La prueba es diagnóstica.
    # No falla por clasificación incorrecta.
    # ---------------------------------------------------------------

    assert True