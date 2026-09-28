import json
import httpx

from app.rag.retriever import recuperar_contexto


CASOS = [
    {
        "pregunta": "¿Cuántas fotografías puede subir un prestador turístico durante el registro?",
        "esperado": True,
    },
    {
        "pregunta": "¿Cómo se registra un nuevo prestador de servicios turísticos?",
        "esperado": True,
    },
    {
        "pregunta": "¿Cómo se recupera una contraseña?",
        "esperado": True,
    },
    {
        "pregunta": "¿Qué requisitos legales necesita un artista para registrarse?",
        "esperado": False,
    },
]


def evaluar_con_qwen(pregunta, contexto):
    prompt = f"""
Eres un evaluador estricto de evidencia documental.

Tu tarea es determinar si la pregunta del usuario puede responderse
ÚNICAMENTE utilizando la información proporcionada en el contexto.

REGLAS IMPORTANTES:

1. No determines que una pregunta es respondible únicamente porque
   exista una palabra o frase relacionada con ella.

2. Debes comprobar que el contexto contiene información suficiente
   para responder directamente la pregunta.

3. La evidencia debe contener el dato solicitado, el procedimiento
   solicitado o la explicación solicitada.

4. No completes información utilizando conocimiento general.

5. No hagas inferencias que no estén explícitamente respaldadas
   por el contexto.

6. Si la pregunta solicita requisitos legales, normativos o jurídicos,
   solamente considérala respondible si esos requisitos aparecen
   explícitamente en el contexto.

7. Si solamente existe información parcialmente relacionada,
   responde "respondible": false.

8. Si la evidencia permite responder directamente, responde
   "respondible": true.

9. La evidencia seleccionada debe ser realmente pertinente
   para la pregunta, no simplemente una frase relacionada.

Devuelve ÚNICAMENTE un JSON válido con esta estructura:

{{
    "respondible": true,
    "evidencia": "fragmento concreto del contexto que demuestra la respuesta",
    "respuesta": "respuesta que podría darse al usuario utilizando únicamente la evidencia"
}}

Si no existe evidencia suficiente:

{{
    "respondible": false,
    "evidencia": "",
    "respuesta": ""
}}

PREGUNTA:
{pregunta}

CONTEXTO:
{contexto}
"""

    with httpx.Client(timeout=300.0) as client:
        response = client.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": "qwen2.5-coder:3b-instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 1,
                    "seed": 42,
                    "num_predict": 300,
                    "num_ctx": 4096
                }
            }
        )

    response.raise_for_status()

    data = response.json()

    contenido = data["message"]["content"]

    return json.loads(contenido)


def test_evidence_gate():
    print("\n")
    print("=" * 100)
    print("PRUEBA DEFINITIVA — EVIDENCE GATE")
    print("=" * 100)

    resultados_finales = []

    for numero, caso in enumerate(CASOS, start=1):

        pregunta = caso["pregunta"]
        esperado = caso["esperado"]

        print("\n")
        print("#" * 100)
        print(f"CASO {numero}")
        print("#" * 100)

        print(f"\nPREGUNTA:")
        print(pregunta)

        # Recuperar evidencia real desde PostgreSQL + pgvector.
        resultados = recuperar_contexto(
            pregunta,
            top_k=3
        )

        contexto = "\n\n".join(
            resultado["text"]
            for resultado in resultados
        )

        print("\nTOP-3 RECUPERADO:")

        for posicion, resultado in enumerate(resultados, start=1):
            distancia = resultado["distance"]
            similitud = 1 - distancia

            print(
                f"TOP-{posicion} | "
                f"ID={resultado['id']} | "
                f"Chunk={resultado['chunk_index']} | "
                f"Distancia={distancia:.6f} | "
                f"Similitud={similitud:.2%}"
            )

        print("\nEvaluando evidencia con Qwen...")

        resultado_qwen = evaluar_con_qwen(
            pregunta,
            contexto
        )

        respondible = resultado_qwen.get(
            "respondible",
            False
        )

        evidencia = resultado_qwen.get(
            "evidencia",
            ""
        )

        respuesta = resultado_qwen.get(
            "respuesta",
            ""
        )

        correcto = respondible == esperado

        print("\nRESULTADO QWEN:")
        print(
            json.dumps(
                resultado_qwen,
                ensure_ascii=False,
                indent=4
            )
        )

        print("\nEVALUACIÓN:")

        print(
            f"Esperado:    {esperado}"
        )

        print(
            f"Obtenido:    {respondible}"
        )

        print(
            f"Resultado:   {'OK' if correcto else 'ERROR'}"
        )

        resultados_finales.append(correcto)

    correctos = sum(resultados_finales)
    total = len(resultados_finales)

    print("\n")
    print("=" * 100)
    print("RESULTADO FINAL")
    print("=" * 100)

    print(
        f"Casos correctos: {correctos}/{total}"
    )

    print(
        f"Precisión: {correctos / total:.2%}"
    )

    if correctos == total:
        print("\n✅ EVIDENCE GATE VALIDADO PARA ESTOS CASOS.")
    else:
        print("\n⚠️ EL EVIDENCE GATE TODAVÍA PRESENTA ERRORES.")

    print("=" * 100)