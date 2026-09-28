from app.rag.retriever import recuperar_contexto


# ============================================================
# PREGUNTAS DE EVALUACIÓN
# ============================================================

preguntas_buenas = [
    "¿Qué es GAIA?",
    "¿Cómo se registran los artistas?",
    "¿Cómo se registra un prestador turístico?",
    "¿Qué información se solicita durante el registro?",
    "¿Quién puede registrarse como artista?",
    "¿Qué datos personales debe proporcionar un artista?",
    "¿Cuántas fotografías puede subir un prestador turístico?",
    "¿Qué pasa después de enviar el registro de un artista?",
    "¿Cómo se recupera la contraseña de un usuario?",
    "¿Qué puede hacer un funcionario dentro de GAIA?",
    "¿Qué modalidades artísticas se pueden seleccionar durante el registro?",
    "¿Qué información se puede registrar en la sección de Info Adicional?",
    "¿Qué ocurre si un artista deja campos opcionales vacíos?",
    "¿Cómo se puede actualizar el perfil de un artista?",
    "¿Qué estados puede tener un registro?",
    "¿Qué información se solicita para registrar un sitio turístico?",
    "¿Qué puede hacer un usuario cuando su registro ya fue aprobado?",
    "¿Cómo puede un funcionario exportar información de artistas?",
    "¿Qué documentos necesita un artista para registrarse?",
    "¿Qué debe hacer un artista para crear su cuenta?",
    "¿Qué campos son obligatorios para el registro de un artista?",
    "¿Qué datos de contacto debe ingresar un artista?",
    "¿Qué información debe proporcionar sobre su actividad artística?",
    "¿Qué ocurre cuando un artista termina de diligenciar el formulario?",
    "¿Cómo sabe un artista si su registro fue aprobado?",
    "¿Qué sucede si el registro de un artista queda pendiente?",
    "¿Puede un artista modificar la información de su registro?",
    "¿Qué información puede consultar un artista en su perfil?",
    "¿Qué tipo de información adicional puede registrar un artista?",
    "¿Qué fotografías puede cargar un artista?",
]


preguntas_dudosas = [
    "¿Dónde puedo obtener información sobre los trámites de la Alcaldía?",
    "¿Cómo puedo comunicarme con la Alcaldía de Girón?",
    "¿Dónde se encuentra la Alcaldía de Girón?",
    "¿Cuál es el horario de atención de la Alcaldía?",
    "¿Qué requisitos legales necesita un artista para registrarse?",
    "¿Qué requisitos legales necesita un prestador turístico?",
    "¿Cuánto tiempo tarda en aprobarse un registro?",
    "¿Quién revisa la información enviada?",
    "¿Qué pasa si rechazo la solicitud de registro?",
    "¿Puedo registrar más de un establecimiento turístico?",
    "¿Cuántos artistas están registrados actualmente?",
    "¿Cuántos prestadores turísticos hay registrados?",
    "¿Qué beneficios obtiene un artista al registrarse?",
    "¿Qué beneficios obtiene un prestador turístico al registrarse?",
    "¿GAIA está disponible desde un teléfono celular?",
    "¿Se puede utilizar GAIA desde cualquier navegador?",
    "¿Qué pasa si pierdo el acceso a mi correo electrónico?",
    "¿La Alcaldía puede modificar los datos registrados por un usuario?",
    "¿Los datos registrados en GAIA son públicos?",
    "¿GAIA permite descargar certificados?",
]


preguntas_externas = [
    "¿Cuál es la capital de Alemania?",
    "¿Cuál es la población de Colombia?",
    "¿Quién escribió Cien años de soledad?",
    "¿Cuántos continentes existen?",
    "¿Cuál es el planeta más grande del sistema solar?",
    "¿Cómo funciona la fotosíntesis?",
    "¿Qué es la gravedad?",
    "¿Cuál es la fórmula del teorema de Pitágoras?",
    "¿Cómo se prepara un café colombiano?",
    "¿Cuál es la mejor forma de cocinar arroz?",
    "¿Cómo puedo aprender inglés?",
    "¿Cómo instalar Python en Windows?",
    "¿Cómo crear una página web con HTML?",
    "¿Cómo crear una API con FastAPI?",
    "¿Qué es Docker?",
    "¿Cómo funciona PostgreSQL?",
    "¿Qué es inteligencia artificial generativa?",
    "¿Cuál es el precio actual de un computador?",
    "¿Qué clima habrá mañana en Bogotá?",
    "¿Quién ganó el último Mundial de fútbol?",
]


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOP_K = 3


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def calcular_similitud(distance: float) -> float:
    """
    Convierte la distancia coseno en una similitud aproximada.

    No representa una probabilidad ni un porcentaje de confianza.
    Se utiliza únicamente para facilitar la interpretación de los
    resultados durante este experimento.
    """
    return (1 - distance) * 100


def obtener_distancias(pregunta: str):
    """
    Ejecuta el retrieval y obtiene las distancias Top-K.
    """
    resultados = recuperar_contexto(
        pregunta,
        top_k=TOP_K
    )

    distancias = [
        float(resultado["distance"])
        for resultado in resultados
    ]

    return resultados, distancias

def imprimir_resultado(
    numero: int,
    categoria: str,
    pregunta: str,
    resultados: list,
    distancias: list[float]
):
    """
    Imprime los resultados individuales de una pregunta.

    Muestra:
    - Top-1, Top-2 y Top-3 Distance.
    - Similaridad aproximada del Top-1.
    - Margen entre Top-1 y Top-2.
    - Fragmentos recuperados.
    """

    top1 = distancias[0] if len(distancias) >= 1 else None
    top2 = distancias[1] if len(distancias) >= 2 else None
    top3 = distancias[2] if len(distancias) >= 3 else None

    similitud_top1 = (
        calcular_similitud(top1)
        if top1 is not None
        else None
    )

    margen_top1_top2 = (
        top2 - top1
        if top1 is not None and top2 is not None
        else None
    )

    print("\n" + "-" * 80)

    print(f"[{categoria}] Pregunta #{numero}")
    print(f"Pregunta: {pregunta}")

    if top1 is not None:
        print(f"Top-1 Distance: {top1:.6f}")
        print(f"Top-1 Similarity: {similitud_top1:.2f}%")
    else:
        print("Top-1 Distance: N/A")

    if top2 is not None:
        print(f"Top-2 Distance: {top2:.6f}")
    else:
        print("Top-2 Distance: N/A")

    if top3 is not None:
        print(f"Top-3 Distance: {top3:.6f}")
    else:
        print("Top-3 Distance: N/A")

    if margen_top1_top2 is not None:
        print(
            f"Margen Top-1 → Top-2: "
            f"{margen_top1_top2:.6f}"
        )
    else:
        print("Margen Top-1 → Top-2: N/A")

    if resultados:
        print("\nFragmentos recuperados:")

        for posicion, resultado in enumerate(
            resultados[:TOP_K],
            start=1
        ):
            texto = resultado["text"].replace(
                "\n",
                " "
            )

            # Evitamos imprimir textos excesivamente largos.
            if len(texto) > 250:
                texto = texto[:250] + "..."

            print(
                f"  {posicion}. "
                f"Distance={resultado['distance']:.6f} | "
                f"Chunk={resultado['chunk_index']} | "
                f"{texto}"
            )

def calcular_estadisticas(distancias: list[float]):
    """
    Calcula las estadísticas principales de una categoría.
    """

    if not distancias:
        return None

    promedio = sum(distancias) / len(distancias)

    similitudes = [
        calcular_similitud(distance)
        for distance in distancias
    ]

    promedio_similitud = (
        sum(similitudes) / len(similitudes)
    )

    return {
        "cantidad": len(distancias),
        "avg_distance": promedio,
        "avg_similarity": promedio_similitud,
        "min_distance": min(distancias),
        "max_distance": max(distancias),
    }


def ejecutar_categoria(
    nombre: str,
    preguntas: list[str],
):
    """
    Ejecuta todas las preguntas de una categoría
    y devuelve sus distancias Top-1.
    """

    print("\n")
    print("=" * 80)
    print(f"CATEGORÍA: {nombre}")
    print("=" * 80)

    distancias_top1 = []

    for numero, pregunta in enumerate(
        preguntas,
        start=1
    ):
        resultados, distancias = obtener_distancias(
            pregunta
        )

        if distancias:
            distancias_top1.append(
                distancias[0]
            )

        imprimir_resultado(
            numero=numero,
            categoria=nombre,
            pregunta=pregunta,
            resultados=resultados,
            distancias=distancias,
        )

    return distancias_top1

# ============================================================
# TEST PRINCIPAL
# ============================================================

def test_retrieval_relevance():
    """
    Evalúa la separación del retrieval entre:

    🟢 BUENA
    Preguntas claramente relacionadas con los documentos.

    🟡 DUDOSA
    Preguntas relacionadas parcialmente con el dominio,
    pero cuya respuesta puede no estar documentada.

    🔴 EXTERNA
    Preguntas que no pertenecen al dominio de los documentos.

    El test NO aplica ningún threshold.
    Su objetivo es recopilar evidencia para definirlo posteriormente.
    """

    distancias_buenas = ejecutar_categoria(
        "BUENA",
        preguntas_buenas
    )

    distancias_dudosas = ejecutar_categoria(
        "DUDOSA",
        preguntas_dudosas
    )

    distancias_externas = ejecutar_categoria(
        "EXTERNA",
        preguntas_externas
    )

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    estadisticas = {
        "BUENA": calcular_estadisticas(
            distancias_buenas
        ),
        "DUDOSA": calcular_estadisticas(
            distancias_dudosas
        ),
        "EXTERNA": calcular_estadisticas(
            distancias_externas
        ),
    }

    print("\n\n")
    print("=" * 80)
    print("ESTADÍSTICAS FINALES")
    print("=" * 80)

    for categoria, datos in estadisticas.items():

        print(f"\nCATEGORÍA: {categoria}")

        if datos is None:
            print("Sin datos.")
            continue

        print(
            f"Cantidad de preguntas: "
            f"{datos['cantidad']}"
        )

        print(
            f"AVG Distance: "
            f"{datos['avg_distance']:.6f}"
        )

        print(
            f"AVG Similarity: "
            f"{datos['avg_similarity']:.2f}%"
        )

        print(
            f"MIN Distance: "
            f"{datos['min_distance']:.6f}"
        )

        print(
            f"MAX Distance: "
            f"{datos['max_distance']:.6f}"
        )

    # ========================================================
    # RESUMEN COMPARATIVO
    # ========================================================

    print("\n\n")
    print("=" * 80)
    print("RESUMEN COMPARATIVO")
    print("=" * 80)

    for categoria, datos in estadisticas.items():

        if datos is None:
            continue

        print(
            f"{categoria:<10} | "
            f"AVG Distance: "
            f"{datos['avg_distance']:.6f} | "
            f"AVG Similarity: "
            f"{datos['avg_similarity']:.2f}% | "
            f"MIN: {datos['min_distance']:.6f} | "
            f"MAX: {datos['max_distance']:.6f}"
        )

    # ========================================================
    # SEPARACIÓN ENTRE CATEGORÍAS
    # ========================================================

    if (
        distancias_buenas
        and distancias_dudosas
        and distancias_externas
    ):
        max_buena = max(distancias_buenas)
        min_dudosa = min(distancias_dudosas)

        max_dudosa = max(distancias_dudosas)
        min_externa = min(distancias_externas)

        print("\n\n")
        print("=" * 80)
        print("SEPARACIÓN ENTRE CATEGORÍAS")
        print("=" * 80)

        print(
            f"Máxima Distance BUENA: "
            f"{max_buena:.6f}"
        )

        print(
            f"Mínima Distance DUDOSA: "
            f"{min_dudosa:.6f}"
        )

        print(
            f"Máxima Distance DUDOSA: "
            f"{max_dudosa:.6f}"
        )

        print(
            f"Mínima Distance EXTERNA: "
            f"{min_externa:.6f}"
        )

        print(
            f"\nGap BUENA → DUDOSA: "
            f"{min_dudosa - max_buena:.6f}"
        )

        print(
            f"Gap DUDOSA → EXTERNA: "
            f"{min_externa - max_dudosa:.6f}"
        )

    # ========================================================
    # VALIDACIÓN BÁSICA
    # ========================================================

    assert distancias_buenas, (
        "No se obtuvieron resultados para "
        "la categoría BUENA."
    )

    assert distancias_dudosas, (
        "No se obtuvieron resultados para "
        "la categoría DUDOSA."
    )

    assert distancias_externas, (
        "No se obtuvieron resultados para "
        "la categoría EXTERNA."
    )