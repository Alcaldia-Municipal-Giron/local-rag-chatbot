"""
Prueba comparativa de prompts para Answerability.

Objetivo:
Comparar tres estrategias diferentes para determinar si el contexto
recuperado contiene información suficiente para responder una pregunta.

Esta prueba NO modifica el código productivo.
"""

import json
import httpx

from app.rag.retriever import recuperar_contexto
from app.rag.context_builder import construir_contexto


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:3b-instruct"


# ---------------------------------------------------------------------------
# Casos problemáticos detectados en la prueba anterior.
# ---------------------------------------------------------------------------

CASOS = [
    {
        "pregunta": "¿Cuántas fotografías puede subir un prestador turístico?",
        "esperado": True,
    },
    {
        "pregunta": "¿Cómo se registra un nuevo prestador de servicios turísticos?",
        "esperado": True,
    },
    {
        "pregunta": "¿Qué requisitos legales necesita un artista para registrarse?",
        "esperado": False,
    },
]


# ---------------------------------------------------------------------------
# Llamada común a Ollama.
# ---------------------------------------------------------------------------

def consultar_qwen(prompt: str) -> str:

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
                "num_predict": 150,
                "num_ctx": 4096,
            },
        },
        timeout=500.0,
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    return datos["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Extrae JSON de una respuesta de Qwen.
# ---------------------------------------------------------------------------

def extraer_json(texto: str):

    inicio = texto.find("{")
    fin = texto.rfind("}")

    if inicio == -1 or fin == -1:
        return None

    try:
        return json.loads(
            texto[inicio:fin + 1]
        )

    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# PROMPT A
#
# Es el prompt utilizado anteriormente.
# ---------------------------------------------------------------------------

def prompt_a(pregunta: str, contexto: str) -> str:

    return f"""
Eres un evaluador de suficiencia de contexto para un sistema RAG.

Debes decidir únicamente si el contexto proporcionado contiene
información suficiente para responder la pregunta.

No utilices conocimiento externo.

Pregunta:
{pregunta}

Contexto:
{contexto}

Responde únicamente con JSON válido:

{{
  "answerable": true,
  "reason": "explicación breve"
}}
"""


# ---------------------------------------------------------------------------
# PROMPT B
#
# Exige evidencia explícita y prohíbe inferencias.
# ---------------------------------------------------------------------------

def prompt_b(pregunta: str, contexto: str) -> str:

    return f"""
Eres un evaluador estricto de suficiencia de contexto para un sistema RAG.

Tu tarea NO es responder la pregunta.

Debes determinar si la respuesta puede obtenerse DIRECTAMENTE
del contexto proporcionado.

Reglas obligatorias:

1. Usa únicamente el contexto.
2. No utilices conocimiento externo.
3. No hagas inferencias.
4. No completes información que no aparezca.
5. Información relacionada pero insuficiente = false.
6. Si la respuesta aparece explícitamente en el contexto = true.
7. Si para responder necesitas asumir, deducir o imaginar algo = false.

Pregunta:
{pregunta}

Contexto:
{contexto}

Responde únicamente con JSON válido:

{{
  "answerable": true,
  "reason": "explicación breve basada únicamente en el contexto"
}}
"""


# ---------------------------------------------------------------------------
# PROMPT C
#
# Primero exige localizar evidencia concreta.
# ---------------------------------------------------------------------------

def prompt_c(pregunta: str, contexto: str) -> str:

    return f"""
Eres un analizador de evidencia para un sistema RAG.

Debes determinar si el contexto contiene evidencia suficiente
para responder la pregunta.

NO respondas la pregunta directamente.

Primero busca una evidencia textual concreta.

Reglas:

- Usa únicamente el contexto.
- No uses conocimiento externo.
- No hagas inferencias.
- No completes información.
- Si encuentras evidencia suficiente, indícala literalmente.
- Si no encuentras evidencia suficiente, utiliza "SIN_EVIDENCIA".

Pregunta:
{pregunta}

Contexto:
{contexto}

Responde únicamente con JSON válido:

{{
  "evidence": "fragmento concreto del contexto o SIN_EVIDENCIA",
  "answerable": true,
  "reason": "explicación breve"
}}
"""


# ---------------------------------------------------------------------------
# Ejecuta los tres prompts para un caso.
# ---------------------------------------------------------------------------

def ejecutar_caso(caso):

    pregunta = caso["pregunta"]
    esperado = caso["esperado"]

    print("\n")
    print("=" * 90)
    print(f"PREGUNTA: {pregunta}")
    print(f"ESPERADO: {esperado}")
    print("=" * 90)

    # ---------------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------------

    resultados = recuperar_contexto(
        pregunta,
        top_k=3,
    )

    contexto = construir_contexto(resultados)

    print("\nRETRIEVAL")
    print("-" * 90)

    for posicion, resultado in enumerate(resultados, start=1):

        similarity = 1 - resultado["distance"]

        print(
            f"Top-{posicion}: "
            f"distance={resultado['distance']:.6f} | "
            f"similarity={similarity:.2%} | "
            f"chunk={resultado['id']}"
        )

        print(
            resultado["text"][:350]
            .replace("\n", " ")
        )

    # ---------------------------------------------------------------
    # PROMPT A
    # ---------------------------------------------------------------

    print("\nPROMPT A — ACTUAL")
    print("-" * 90)

    respuesta_a = consultar_qwen(
        prompt_a(
            pregunta,
            contexto,
        )
    )

    resultado_a = extraer_json(respuesta_a)

    print(respuesta_a)

    # ---------------------------------------------------------------
    # PROMPT B
    # ---------------------------------------------------------------

    print("\nPROMPT B — EVIDENCIA EXPLÍCITA")
    print("-" * 90)

    respuesta_b = consultar_qwen(
        prompt_b(
            pregunta,
            contexto,
        )
    )

    resultado_b = extraer_json(respuesta_b)

    print(respuesta_b)

    # ---------------------------------------------------------------
    # PROMPT C
    # ---------------------------------------------------------------

    print("\nPROMPT C — EXTRACCIÓN DE EVIDENCIA")
    print("-" * 90)

    respuesta_c = consultar_qwen(
        prompt_c(
            pregunta,
            contexto,
        )
    )

    resultado_c = extraer_json(respuesta_c)

    print(respuesta_c)

    # ---------------------------------------------------------------
    # Comparación
    # ---------------------------------------------------------------

    print("\nCOMPARACIÓN")
    print("-" * 90)

    valor_a = (
        resultado_a.get("answerable")
        if resultado_a
        else None
    )

    valor_b = (
        resultado_b.get("answerable")
        if resultado_b
        else None
    )

    valor_c = (
        resultado_c.get("answerable")
        if resultado_c
        else None
    )

    print(f"Esperado : {esperado}")
    print(f"Prompt A : {valor_a}")
    print(f"Prompt B : {valor_b}")
    print(f"Prompt C : {valor_c}")

    if resultado_c:

        print(
            f"Evidencia C: "
            f"{resultado_c.get('evidence', '')}"
        )

    return {
        "pregunta": pregunta,
        "esperado": esperado,
        "prompt_a": valor_a,
        "prompt_b": valor_b,
        "prompt_c": valor_c,
    }


# ---------------------------------------------------------------------------
# Prueba principal.
# ---------------------------------------------------------------------------

def test_answerability_prompts():

    resultados = []

    print("\n")
    print("#" * 90)
    print("# PRUEBA COMPARATIVA DE PROMPTS DE ANSWERABILITY")
    print("#" * 90)

    for caso in CASOS:

        resultado = ejecutar_caso(caso)

        resultados.append(resultado)

    # ---------------------------------------------------------------
    # Resumen final
    # ---------------------------------------------------------------

    print("\n")
    print("#" * 90)
    print("# RESUMEN FINAL")
    print("#" * 90)

    print(
        f"{'PREGUNTA':55} | "
        f"ESP | A | B | C"
    )

    print("-" * 90)

    for resultado in resultados:

        pregunta = resultado["pregunta"]

        print(
            f"{pregunta[:55]:55} | "
            f"{str(resultado['esperado']):3} | "
            f"{str(resultado['prompt_a']):5} | "
            f"{str(resultado['prompt_b']):5} | "
            f"{str(resultado['prompt_c']):5}"
        )

    print("\n")
    print("#" * 90)
    print("# INTERPRETACIÓN")
    print("#" * 90)

    print("""
A = Prompt actual
B = Prompt con exigencia de evidencia explícita
C = Prompt con extracción explícita de evidencia

La prueba es diagnóstica.
No modifica código productivo.
""")

    assert True