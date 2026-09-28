import json
import re
import time
from pathlib import Path

import httpx
import pytest

from app.rag.retriever import recuperar_contexto
from app.rag.context_builder import construir_contexto


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

MODEL_NAME = "qwen2.5-coder:3b-instruct"

TOP_K = 3

# Timeout por pregunta.
#
# Se deja en 300 segundos para evitar que una pregunta
# problemática bloquee toda la prueba durante demasiado tiempo.
OLLAMA_TIMEOUT = 300.0

# Opciones deterministas para Qwen.
OLLAMA_OPTIONS = {
    "num_predict": 220,
    "temperature": 0,
    "top_p": 1,
    "top_k": 1,
    "seed": 42,
    "num_ctx": 4096,
}


# ============================================================
# ARCHIVO DE RESULTADOS
# ============================================================

RESULTS_FILE = (
    Path(__file__).resolve().parent
    / "evidence_gate_results.json"
)


# ============================================================
# CASOS DE PRUEBA
# ============================================================
#
# Categorías:
#
# RESPONDIBLE_DIRECTA
#     La respuesta aparece explícitamente en el manual.
#
# RESPONDIBLE_PROCEDIMIENTO
#     El manual explica cómo realizar una acción.
#
# NO_RESPONDIBLE
#     La pregunta está relacionada con el sistema,
#     pero el manual no proporciona la información solicitada.
#
# INTENCION_ENGANOSA
#     Existe información relacionada, pero no responde
#     exactamente a lo que pregunta el usuario.
#
# EXTERNA
#     La pregunta no pertenece al dominio del manual.
#
# ============================================================

CASOS = [

    # ========================================================
    # 1 - RESPONDIBLES DIRECTAMENTE
    # ========================================================

    {
        "id": 1,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué es GAIA?",
        "esperado": True,
    },

    {
        "id": 2,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué estados puede tener un registro?",
        "esperado": True,
    },

    {
        "id": 3,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Cuántas fotografías puede subir un prestador turístico durante el registro?",
        "esperado": True,
    },

    {
        "id": 4,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Cuál es el máximo de fotografías que puede cargar un sitio turístico en el formulario de registro?",
        "esperado": True,
    },

    {
        "id": 5,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Cuántas fotos adicionales se pueden agregar a la galería?",
        "esperado": True,
    },

    {
        "id": 6,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué tipos de registro existen en GAIA?",
        "esperado": True,
    },

    {
        "id": 7,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué información se solicita en los datos personales del artista?",
        "esperado": True,
    },

    {
        "id": 8,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué información puede registrar un prestador turístico sobre su establecimiento?",
        "esperado": True,
    },

    {
        "id": 9,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué información puede actualizar un artista desde su perfil?",
        "esperado": True,
    },

    {
        "id": 10,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué información puede actualizar un prestador turístico desde su perfil?",
        "esperado": True,
    },

    {
        "id": 11,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué estados aparecen en los registros?",
        "esperado": True,
    },

    {
        "id": 12,
        "categoria": "RESPONDIBLE_DIRECTA",
        "pregunta": "¿Qué información se puede consultar en el directorio público?",
        "esperado": True,
    },


    # ========================================================
    # 2 - RESPONDIBLES: PROCEDIMIENTOS
    # ========================================================

    {
        "id": 13,
        "categoria": "RESPONDIBLE_PROCEDIMIENTO",
        "pregunta": "¿Cómo se registra un artista?",
        "esperado": True,
    },

    {
        "id": 14,
        "categoria": "RESPONDIBLE_PROCEDIMIENTO",
        "pregunta": "¿Cómo se registra un nuevo prestador de servicios turísticos?",
        "esperado": True,
    },

    {
        "id": 15,
        "categoria": "RESPONDIBLE_PROCEDIMIENTO",
        "pregunta": "¿Cómo se inicia el registro de un sitio turístico?",
        "esperado": True,
    },

    {
        "id": 16,
        "categoria": "RESPONDIBLE_PROCEDIMIENTO",
        "pregunta": "¿Qué debe hacer el usuario para aceptar la autorización de tratamiento de datos personales?",
        "esperado": True,
    },

    {
        "id": 17,
        "categoria": "RESPONDIBLE_PROCEDIMIENTO",
        "pregunta": "¿Cómo puede un usuario buscar un artista?",
        "esperado": True,
    },

    {
        "id": 18,
        "categoria": "RESPONDIBLE_PROCEDIMIENTO",
        "pregunta": "¿Cómo puede un usuario buscar un sitio turístico?",
        "esperado": True,
    },

    {
        "id": 19,
        "categoria": "RESPONDIBLE_PROCEDIMIENTO",
        "pregunta": "¿Cómo se recupera una contraseña?",
        "esperado": True,
    },

    {
        "id": 20,
        "categoria": "RESPONDIBLE_PROCEDIMIENTO",
        "pregunta": "¿Cómo se puede editar el perfil?",
        "esperado": True,
    },


    # ========================================================
    # 3 - NO RESPONDIBLES
    # ========================================================

    {
        "id": 21,
        "categoria": "NO_RESPONDIBLE",
        "pregunta": "¿Cuál es el horario de atención de la Alcaldía?",
        "esperado": False,
    },

    {
        "id": 22,
        "categoria": "NO_RESPONDIBLE",
        "pregunta": "¿Cuál es la dirección de la Alcaldía de Girón?",
        "esperado": False,
    },

    {
        "id": 23,
        "categoria": "NO_RESPONDIBLE",
        "pregunta": "¿Cuál es el teléfono de la Alcaldía de Girón?",
        "esperado": False,
    },

    {
        "id": 24,
        "categoria": "NO_RESPONDIBLE",
        "pregunta": "¿Cuánto tiempo tarda la aprobación de un registro?",
        "esperado": False,
    },

    {
        "id": 25,
        "categoria": "NO_RESPONDIBLE",
        "pregunta": "¿Cuánto cuesta registrarse como prestador turístico?",
        "esperado": False,
    },

    {
        "id": 26,
        "categoria": "NO_RESPONDIBLE",
        "pregunta": "¿Cuál es el correo oficial de la Secretaría de Cultura y Turismo?",
        "esperado": False,
    },

    {
        "id": 27,
        "categoria": "NO_RESPONDIBLE",
        "pregunta": "¿Qué requisitos legales necesita un artista para registrarse?",
        "esperado": False,
    },

    {
        "id": 28,
        "categoria": "NO_RESPONDIBLE",
        "pregunta": "¿Qué ley regula legalmente el registro de artistas en GAIA?",
        "esperado": False,
    },


    # ========================================================
    # 4 - INTENCIÓN SEMÁNTICA ENGAÑOSA
    # ========================================================
    #
    # Aquí existe información relacionada en el contexto,
    # pero la evidencia NO debe considerarse suficiente
    # si no responde exactamente a la intención.
    #
    # ========================================================

    {
        "id": 29,
        "categoria": "INTENCION_ENGANOSA",
        "pregunta": "¿Qué sanciones recibe un artista si proporciona información falsa?",
        "esperado": False,
    },

    {
        "id": 30,
        "categoria": "INTENCION_ENGANOSA",
        "pregunta": "¿Qué requisitos jurídicos debe cumplir un artista?",
        "esperado": False,
    },

    {
        "id": 31,
        "categoria": "INTENCION_ENGANOSA",
        "pregunta": "¿Qué documentos legales debe presentar obligatoriamente un artista?",
        "esperado": False,
    },

    {
        "id": 32,
        "categoria": "INTENCION_ENGANOSA",
        "pregunta": "¿La información del formulario de artista demuestra que esos campos son requisitos legales?",
        "esperado": False,
    },


    # ========================================================
    # 5 - PREGUNTAS EXTERNAS
    # ========================================================

    {
        "id": 33,
        "categoria": "EXTERNA",
        "pregunta": "¿Cuál es la capital de Japón?",
        "esperado": False,
    },

    {
        "id": 34,
        "categoria": "EXTERNA",
        "pregunta": "¿Quién escribió Cien años de soledad?",
        "esperado": False,
    },

    {
        "id": 35,
        "categoria": "EXTERNA",
        "pregunta": "¿Cuál es el planeta más grande del sistema solar?",
        "esperado": False,
    },

    {
        "id": 36,
        "categoria": "EXTERNA",
        "pregunta": "¿Qué es PostgreSQL?",
        "esperado": False,
    },
]


# ============================================================
# PROMPT DEL EVIDENCE GATE
# ============================================================

EVIDENCE_GATE_PROMPT = """
Eres un evaluador de evidencia para un sistema RAG.

Tu trabajo NO es responder la pregunta.

Tu trabajo es determinar si el CONTEXTO contiene evidencia
EXPLÍCITA, DIRECTA y SUFICIENTE para responder EXACTAMENTE
la PREGUNTA.

Debes utilizar EXCLUSIVAMENTE el CONTEXTO.

============================================================
REGLAS ESTRICTAS
============================================================

1. NO utilices conocimiento externo.

2. NO completes información que no aparezca en el contexto.

3. NO hagas inferencias para llenar información faltante.

4. La evidencia debe responder directamente a la intención
   de la pregunta.

5. Que una frase esté relacionada con la pregunta NO significa
   automáticamente que sea evidencia suficiente.

6. Debes distinguir entre:
   - información del sistema;
   - información de un formulario;
   - instrucciones de uso;
   - requisitos;
   - requisitos legales;
   - normas;
   - obligaciones;
   - sanciones;
   - costos;
   - tiempos;
   - datos de contacto.

7. Si la pregunta pide "requisitos legales", "requisitos jurídicos",
   "leyes", "normas", "sanciones" u obligaciones legales, el contexto
   debe mencionarlos explícitamente.

8. Que el contexto muestre campos de un formulario NO significa
   que esos campos sean requisitos legales.

9. Que el contexto explique cómo realizar un registro NO significa
   que contenga requisitos legales para realizarlo.

10. Si la pregunta solicita un dato concreto y el contexto solamente
    contiene información relacionada pero no ese dato concreto,
    responde false.

11. Si existen varias evidencias relacionadas pero ninguna responde
    exactamente a la pregunta, responde false.

12. Si existe evidencia suficiente, debes copiarla EXACTAMENTE
    desde el contexto.

13. La evidencia NO puede ser inventada ni reformulada.

14. Si no existe evidencia suficiente:
    - answerable debe ser false
    - evidence debe ser "SIN_EVIDENCIA"

15. Si answerable es true:
    - evidence debe contener texto que aparezca literalmente
      en el contexto.
    - supports_question debe ser true.

16. Si answerable es false:
    - evidence debe ser "SIN_EVIDENCIA".
    - supports_question debe ser false.

17. NO respondas la pregunta.
    Solamente evalúa la evidencia.

============================================================
FORMATO DE SALIDA
============================================================

Responde ÚNICAMENTE con JSON válido.

El formato debe ser exactamente:

{{
  "answerable": true,
  "evidence": "texto exacto del contexto",
  "supports_question": true,
  "reason": "explicación breve"
}}

o:

{{
  "answerable": false,
  "evidence": "SIN_EVIDENCIA",
  "supports_question": false,
  "reason": "explicación breve"
}}

============================================================
PREGUNTA
============================================================

""" + "{pregunta}" + """

============================================================
CONTEXTO
============================================================

""" + "{contexto}" + """
"""


# ============================================================
# NORMALIZACIÓN DE TEXTO
# ============================================================

def normalizar_texto(texto: str) -> str:
    """
    Normaliza espacios para poder comprobar si la evidencia
    proporcionada por Qwen realmente aparece en el contexto.

    No cambia el contenido semántico.
    """

    texto = texto.replace("\r\n", "\n")
    texto = texto.replace("\r", "\n")

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


# ============================================================
# VALIDAR EVIDENCIA
# ============================================================

def evidencia_pertenece_al_contexto(
    evidencia: str,
    contexto: str,
) -> bool:
    """
    Comprueba que la evidencia devuelta por Qwen
    aparezca realmente dentro del contexto recuperado.
    """

    if evidencia == "SIN_EVIDENCIA":
        return True

    evidencia_normalizada = normalizar_texto(evidencia)
    contexto_normalizado = normalizar_texto(contexto)

    if not evidencia_normalizada:
        return False

    return evidencia_normalizada in contexto_normalizado


# ============================================================
# CONSTRUIR PROMPT
# ============================================================

def construir_prompt(
    pregunta: str,
    contexto: str,
) -> str:
    """
    Construye el prompt sin utilizar str.format(),
    evitando conflictos con las llaves del JSON.
    """

    return (
        EVIDENCE_GATE_PROMPT
        .replace("{pregunta}", pregunta)
        .replace("{contexto}", contexto)
    )


# ============================================================
# LLAMAR A OLLAMA
# ============================================================

def evaluar_evidencia(
    pregunta: str,
    contexto: str,
):
    """
    Ejecuta una evaluación del Evidence Gate mediante Qwen.

    Devuelve:
        contenido textual generado por el modelo.
    """

    prompt = construir_prompt(
        pregunta,
        contexto,
    )

    respuesta = httpx.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "options": OLLAMA_OPTIONS,
        },
        timeout=OLLAMA_TIMEOUT,
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    return datos["message"]["content"].strip()


# ============================================================
# EXTRAER JSON DE QWEN
# ============================================================

def extraer_json(contenido: str):
    """
    Convierte la respuesta de Qwen en un diccionario Python.

    Soporta respuestas normales y respuestas encerradas
    en bloques Markdown ```json.
    """

    contenido = contenido.strip()

    # Eliminar bloque Markdown inicial.
    if contenido.startswith("```json"):
        contenido = contenido[len("```json"):]

    elif contenido.startswith("```"):
        contenido = contenido[len("```"):]

    # Eliminar bloque Markdown final.
    if contenido.endswith("```"):
        contenido = contenido[:-3]

    contenido = contenido.strip()

    # Intento directo.
    try:
        return json.loads(contenido)
    except json.JSONDecodeError:
        pass

    # Intento de recuperación:
    #
    # Busca desde el primer { hasta el último }.
    inicio = contenido.find("{")
    final = contenido.rfind("}")

    if inicio == -1 or final == -1:
        raise ValueError(
            "Qwen no devolvió un objeto JSON reconocible."
        )

    contenido_json = contenido[inicio:final + 1]

    return json.loads(contenido_json)


# ============================================================
# GUARDAR RESULTADOS
# ============================================================

def guardar_resultados(resultados):
    """
    Guarda todos los resultados en JSON para poder analizarlos
    posteriormente sin tener que ejecutar nuevamente el modelo.
    """

    datos = {
        "modelo": MODEL_NAME,
        "top_k": TOP_K,
        "timeout_por_pregunta": OLLAMA_TIMEOUT,
        "opciones_ollama": OLLAMA_OPTIONS,
        "total_casos": len(resultados),
        "resultados": resultados,
    }

    RESULTS_FILE.write_text(
        json.dumps(
            datos,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# ============================================================
# MOSTRAR RESULTADO DE UNA PREGUNTA
# ============================================================

def imprimir_resultado(
    caso,
    evaluacion,
    evidencia_valida,
    tiempo,
):
    """
    Imprime el resultado de un caso individual.
    """

    print("\n")
    print("-" * 100)
    print(f"ID:          {caso['id']}")
    print(f"CATEGORÍA:   {caso['categoria']}")
    print(f"PREGUNTA:    {caso['pregunta']}")
    print("-" * 100)

    print(f"Esperado:            {caso['esperado']}")

    if evaluacion is None:
        print("Qwen:                ERROR")
        print("Evidencia válida:    False")
        print("Resultado:           ERROR")
        print(f"Tiempo:              {tiempo:.2f}s")
        return

    print(
        f"Qwen answerable:     "
        f"{evaluacion.get('answerable')}"
    )

    print(
        f"Supports question:   "
        f"{evaluacion.get('supports_question')}"
    )

    print(
        f"Evidencia válida:    "
        f"{evidencia_valida}"
    )

    print(
        f"Evidencia:           "
        f"{evaluacion.get('evidence')}"
    )

    print(
        f"Razón:               "
        f"{evaluacion.get('reason')}"
    )

    print(f"Tiempo:              {tiempo:.2f}s")


# ============================================================
# TEST PRINCIPAL
# ============================================================

def test_evidence_gate_complete():
    """
    Ejecuta la batería completa de pruebas del Evidence Gate.

    IMPORTANTE:
    Este test es DIAGNÓSTICO.

    No modifica código productivo.
    No altera la base de datos.
    No modifica los documentos.
    """

    print("\n")
    print("#" * 100)
    print("# PRUEBA DIAGNÓSTICA COMPLETA — EVIDENCE GATE")
    print("#" * 100)

    print()
    print(f"Total de preguntas: {len(CASOS)}")
    print(f"Top-K:              {TOP_K}")
    print(f"Modelo:             {MODEL_NAME}")
    print(f"Timeout/pregunta:   {OLLAMA_TIMEOUT}s")

    resultados = []

    tiempo_total_inicio = time.perf_counter()

    for indice, caso in enumerate(CASOS, start=1):

        print("\n")
        print("=" * 100)
        print(
            f"CASO {indice}/{len(CASOS)}"
        )
        print(
            f"[{caso['categoria']}] "
            f"{caso['pregunta']}"
        )
        print("=" * 100)

        inicio_caso = time.perf_counter()

        # ----------------------------------------------------
        # 1. RETRIEVAL
        # ----------------------------------------------------

        try:

            resultados_retrieval = recuperar_contexto(
                caso["pregunta"],
                top_k=TOP_K,
            )

            contexto = construir_contexto(
                resultados_retrieval
            )

        except Exception as error:

            tiempo_caso = (
                time.perf_counter()
                - inicio_caso
            )

            print("\nERROR DURANTE RETRIEVAL")
            print(str(error))

            resultado = {
                "id": caso["id"],
                "categoria": caso["categoria"],
                "pregunta": caso["pregunta"],
                "esperado": caso["esperado"],
                "answerable": None,
                "supports_question": None,
                "evidencia": None,
                "evidencia_valida": False,
                "resultado": "ERROR_RETRIEVAL",
                "error": str(error),
                "tiempo_segundos": round(
                    tiempo_caso,
                    2,
                ),
            }

            resultados.append(resultado)

            guardar_resultados(resultados)

            continue

        # ----------------------------------------------------
        # MOSTRAR RETRIEVAL
        # ----------------------------------------------------

        print("\nRETRIEVAL")
        print("-" * 100)

        for posicion, resultado in enumerate(
            resultados_retrieval,
            start=1,
        ):

            distancia = float(
                resultado["distance"]
            )

            similitud = (
                1 - distancia
            ) * 100

            print(
                f"Top-{posicion}: "
                f"distance={distancia:.6f} | "
                f"similarity={similitud:.2f}% | "
                f"chunk={resultado['chunk_index']}"
            )

        # ----------------------------------------------------
        # 2. EVIDENCE GATE
        # ----------------------------------------------------

        print("\nEVIDENCE GATE")
        print("-" * 100)

        evaluacion = None
        error_modelo = None

        try:

            contenido = evaluar_evidencia(
                caso["pregunta"],
                contexto,
            )

            print("\nRESPUESTA RAW DE QWEN")
            print("-" * 100)
            print(contenido)

            evaluacion = extraer_json(
                contenido
            )

        except httpx.TimeoutException as error:

            error_modelo = (
                f"Timeout de Ollama: {error}"
            )

        except httpx.HTTPError as error:

            error_modelo = (
                f"Error HTTP de Ollama: {error}"
            )

        except Exception as error:

            error_modelo = (
                f"Error procesando respuesta: {error}"
            )

        # ----------------------------------------------------
        # 3. VALIDACIÓN
        # ----------------------------------------------------

        tiempo_caso = (
            time.perf_counter()
            - inicio_caso
        )

        if evaluacion is None:

            imprimir_resultado(
                caso,
                None,
                False,
                tiempo_caso,
            )

            resultado = {
                "id": caso["id"],
                "categoria": caso["categoria"],
                "pregunta": caso["pregunta"],
                "esperado": caso["esperado"],
                "answerable": None,
                "supports_question": None,
                "evidencia": None,
                "evidencia_valida": False,
                "resultado": "ERROR_MODELO",
                "error": error_modelo,
                "tiempo_segundos": round(
                    tiempo_caso,
                    2,
                ),
            }

            resultados.append(resultado)

            # Guardar inmediatamente.
            guardar_resultados(resultados)

            continue

        answerable = evaluacion.get(
            "answerable"
        )

        supports_question = evaluacion.get(
            "supports_question"
        )

        evidencia = evaluacion.get(
            "evidence",
            "",
        )

        razon = evaluacion.get(
            "reason",
            "",
        )

        evidencia_valida = (
            evidencia_pertenece_al_contexto(
                evidencia,
                contexto,
            )
        )

        # ----------------------------------------------------
        # CRITERIO DEL TEST
        # ----------------------------------------------------
        #
        # Para considerar un caso CORRECTO:
        #
        # 1. answerable coincide con lo esperado.
        #
        # 2. supports_question coincide con answerable.
        #
        # 3. Si answerable=True:
        #       la evidencia debe existir realmente
        #       dentro del contexto.
        #
        # 4. Si answerable=False:
        #       la evidencia debe ser SIN_EVIDENCIA.
        #
        # ----------------------------------------------------

        criterio_answerable = (
            answerable == caso["esperado"]
        )

        criterio_supports = (
            supports_question == answerable
        )

        if answerable is True:

            criterio_evidencia = (
                evidencia_valida
            )

        else:

            criterio_evidencia = (
                evidencia == "SIN_EVIDENCIA"
            )

        correcto = (
            criterio_answerable
            and criterio_supports
            and criterio_evidencia
        )

        resultado_texto = (
            "OK"
            if correcto
            else "ERROR"
        )

        imprimir_resultado(
            caso,
            evaluacion,
            evidencia_valida,
            tiempo_caso,
        )

        print(
            f"\nRESULTADO FINAL DEL CASO: "
            f"{resultado_texto}"
        )

        # ----------------------------------------------------
        # GUARDAR RESULTADO
        # ----------------------------------------------------

        resultado = {
            "id": caso["id"],
            "categoria": caso["categoria"],
            "pregunta": caso["pregunta"],
            "esperado": caso["esperado"],
            "answerable": answerable,
            "supports_question": supports_question,
            "evidencia": evidencia,
            "evidencia_valida": evidencia_valida,
            "reason": razon,
            "criterio_answerable": (
                criterio_answerable
            ),
            "criterio_supports": (
                criterio_supports
            ),
            "criterio_evidencia": (
                criterio_evidencia
            ),
            "resultado": resultado_texto,
            "tiempo_segundos": round(
                tiempo_caso,
                2,
            ),
        }

        resultados.append(resultado)

        # Guardado incremental.
        #
        # Si la prueba se interrumpe, los casos anteriores
        # quedan almacenados.
        guardar_resultados(resultados)

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    tiempo_total = (
        time.perf_counter()
        - tiempo_total_inicio
    )

    total = len(resultados)

    correctos = sum(
        1
        for resultado in resultados
        if resultado["resultado"] == "OK"
    )

    errores = sum(
        1
        for resultado in resultados
        if resultado["resultado"] == "ERROR"
    )

    errores_tecnicos = sum(
        1
        for resultado in resultados
        if resultado["resultado"]
        in (
            "ERROR_MODELO",
            "ERROR_RETRIEVAL",
        )
    )

    # ========================================================
    # RESUMEN GENERAL
    # ========================================================

    print("\n")
    print("#" * 100)
    print("# RESUMEN GENERAL")
    print("#" * 100)

    print()
    print(f"Casos ejecutados:       {total}")
    print(f"Correctos:              {correctos}")
    print(f"Errores lógicos:        {errores}")
    print(f"Errores técnicos:       {errores_tecnicos}")

    if total > 0:

        precision = (
            correctos / total
        ) * 100

        print(
            f"Precisión global:       "
            f"{precision:.2f}%"
        )

    print(
        f"Tiempo total:           "
        f"{tiempo_total / 60:.2f} minutos"
    )

    # ========================================================
    # RESULTADOS POR CATEGORÍA
    # ========================================================

    print("\n")
    print("#" * 100)
    print("# RESULTADOS POR CATEGORÍA")
    print("#" * 100)

    categorias = {}

    for resultado in resultados:

        categoria = resultado["categoria"]

        if categoria not in categorias:
            categorias[categoria] = {
                "total": 0,
                "correctos": 0,
                "errores": 0,
            }

        categorias[categoria]["total"] += 1

        if resultado["resultado"] == "OK":
            categorias[categoria]["correctos"] += 1
        else:
            categorias[categoria]["errores"] += 1

    for categoria, datos in categorias.items():

        total_categoria = datos["total"]

        precision_categoria = (
            datos["correctos"]
            / total_categoria
        ) * 100

        print(
            f"\n{categoria}"
        )

        print(
            f"  Total:       "
            f"{total_categoria}"
        )

        print(
            f"  Correctos:   "
            f"{datos['correctos']}"
        )

        print(
            f"  Errores:     "
            f"{datos['errores']}"
        )

        print(
            f"  Precisión:   "
            f"{precision_categoria:.2f}%"
        )

    # ========================================================
    # ERRORES
    # ========================================================

    print("\n")
    print("#" * 100)
    print("# CASOS CON ERROR")
    print("#" * 100)

    errores_encontrados = [
        resultado
        for resultado in resultados
        if resultado["resultado"] != "OK"
    ]

    if not errores_encontrados:

        print("\nNo se encontraron errores.")

    else:

        for resultado in errores_encontrados:

            print("\n")
            print(
                f"ID {resultado['id']} "
                f"[{resultado['categoria']}]"
            )

            print(
                f"Pregunta: "
                f"{resultado['pregunta']}"
            )

            print(
                f"Esperado: "
                f"{resultado['esperado']}"
            )

            print(
                f"Qwen: "
                f"{resultado['answerable']}"
            )

            print(
                f"Supports question: "
                f"{resultado['supports_question']}"
            )

            print(
                f"Evidencia válida: "
                f"{resultado['evidencia_valida']}"
            )

            print(
                f"Evidencia: "
                f"{resultado['evidencia']}"
            )

            print(
                f"Razón: "
                f"{resultado.get('reason', '')}"
            )

            print(
                f"Resultado: "
                f"{resultado['resultado']}"
            )

    # ========================================================
    # UBICACIÓN DEL ARCHIVO
    # ========================================================

    print("\n")
    print("#" * 100)
    print("# ARCHIVO DE RESULTADOS")
    print("#" * 100)

    print()
    print(
        f"Resultados guardados en:"
    )

    print(
        str(RESULTS_FILE)
    )

    print("\n")

    # ========================================================
    # ESTE TEST ES DIAGNÓSTICO
    # ========================================================
    #
    # No usamos assert sobre los resultados de Qwen.
    #
    # Aunque Qwen se equivoque en varios casos, queremos que
    # TODA la batería termine y que podamos analizar el resultado.
    #
    # Solo verificamos que el propio test haya podido ejecutar
    # la batería sin un fallo estructural.
    # ========================================================

    assert total == len(CASOS)