from app.rag.retriever import recuperar_contexto


# ============================================================
# CONFIGURACIÓN DE LA PRUEBA
# ============================================================

TOP_K = 3


# ============================================================
# PREGUNTAS RELEVANTES
# Deben poder responderse directamente utilizando los
# documentos de GAIA.
# ============================================================

PREGUNTAS_RELEVANTES = [
    "¿Qué funciones tiene GAIA?",
    "¿Qué información maneja GAIA?",
    "¿Cómo funciona el sistema de registro?",
    "¿Quién puede utilizar GAIA?",
    "¿Qué información se puede consultar en GAIA?",
    "¿Cómo se gestionan los registros en GAIA?",
    "¿Quién administra GAIA?",
    "¿Qué puede hacer un funcionario dentro de GAIA?",
    "¿Qué información debe registrar un artista?",
    "¿Qué información debe registrar un prestador turístico?",
]


# ============================================================
# PREGUNTAS AMBIGUAS / CERCANAS
# Están relacionadas con el contexto de GAIA, pero la respuesta
# puede no estar explícitamente documentada.
# ============================================================

PREGUNTAS_AMBIGUAS = [
    "¿Qué hace la Alcaldía con la información registrada?",
    "¿Dónde puedo consultar mi información?",
    "¿Dónde puedo registrarme?",
    "¿Quién revisa la información enviada?",
    "¿Los datos registrados en GAIA son públicos?",
    "¿Qué requisitos legales necesita un artista para registrarse?",
    "¿Puedo registrar más de un establecimiento turístico?",
    "¿GAIA permite descargar certificados?",
    "¿Cómo puedo comunicarme con la Alcaldía de Girón?",
    "¿Cuál es el horario de atención de la Alcaldía?",
]


# ============================================================
# PREGUNTAS EXTERNAS SEMÁNTICAMENTE CERCANAS
# Parecen relacionadas con el dominio, pero no deberían estar
# respaldadas por los documentos actuales.
# ============================================================

PREGUNTAS_EXTERNAS = [
    "¿Cómo registrar una empresa en Colombia?",
    "¿Cómo hacer un trámite en una alcaldía?",
    "¿Cómo registrar un negocio turístico?",
    "¿Qué requisitos necesita un artista en Colombia?",
    "¿Cómo funciona un sistema de gestión municipal?",
    "¿Cómo se administra una base de datos de artistas?",
    "¿Cómo crear un sistema de registro para una alcaldía?",
    "¿Qué requisitos legales debe cumplir un prestador turístico?",
    "¿Cómo se registran los establecimientos turísticos en Colombia?",
    "¿Cómo funciona una plataforma digital para municipios?",
]


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def calcular_similitud(distancia: float) -> float:
    """
    Convierte la distancia coseno en un porcentaje aproximado
    de similitud para facilitar la lectura de los resultados.

    IMPORTANTE:
    Este valor es solamente informativo.
    No representa una confianza real del modelo.
    """
    return (1 - distancia) * 100


def obtener_distancias(resultados: list):
    """
    Extrae las distancias de los resultados recuperados.
    """
    return [
        resultado["distance"]
        for resultado in resultados
    ]


def imprimir_resultado(
    numero: int,
    categoria: str,
    pregunta: str,
    resultados: list,
    distancias: list[float],
):
    """
    Muestra en consola el resultado completo de una pregunta.
    """

    print()
    print("=" * 80)
    print(f"{categoria} #{numero}")
    print("=" * 80)

    print(f"Pregunta:")
    print(pregunta)

    if not resultados:
        print()
        print("NO SE RECUPERARON RESULTADOS.")
        return

    distancia_top_1 = distancias[0]

    print()
    print(
        f"Top-1 Distance: {distancia_top_1:.6f}"
    )

    print(
        f"Top-1 Similarity: "
        f"{calcular_similitud(distancia_top_1):.2f}%"
    )

    if len(distancias) >= 2:
        margen = distancias[1] - distancias[0]

        print(
            f"Margen Top-1 -> Top-2: "
            f"{margen:.6f}"
        )

    print()
    print("RESULTADOS RECUPERADOS")
    print("-" * 80)

    for posicion, resultado in enumerate(
        resultados,
        start=1
    ):
        distancia = resultado["distance"]

        similitud = calcular_similitud(
            distancia
        )

        texto = resultado["text"]

        print()
        print(
            f"Top-{posicion}"
        )

        print(
            f"Distance: {distancia:.6f}"
        )

        print(
            f"Similarity: {similitud:.2f}%"
        )

        print(
            f"Chunk ID: {resultado['id']}"
        )

        print(
            f"Chunk Index: {resultado['chunk_index']}"
        )

        print()
        print("Texto recuperado:")

        print(
            texto[:300]
        )

        if len(texto) > 300:
            print("...")


def calcular_estadisticas(
    nombre: str,
    distancias: list[float]
):
    """
    Calcula estadísticas de una categoría.
    """

    if not distancias:
        print(
            f"{nombre}: sin resultados"
        )
        return

    promedio = (
        sum(distancias) /
        len(distancias)
    )

    minimo = min(distancias)
    maximo = max(distancias)

    promedio_similitud = (
        sum(
            calcular_similitud(d)
            for d in distancias
        )
        / len(distancias)
    )

    print()
    print("=" * 80)
    print(f"ESTADÍSTICAS - {nombre}")
    print("=" * 80)

    print(
        f"Cantidad: {len(distancias)}"
    )

    print(
        f"AVG Distance: {promedio:.6f}"
    )

    print(
        f"AVG Similarity: "
        f"{promedio_similitud:.2f}%"
    )

    print(
        f"MIN Distance: {minimo:.6f}"
    )

    print(
        f"MAX Distance: {maximo:.6f}"
    )


def ejecutar_categoria(
    nombre: str,
    preguntas: list[str]
):
    """
    Ejecuta todas las preguntas de una categoría.
    """

    distancias_top_1 = []

    print()
    print()
    print("#" * 80)
    print(f"CATEGORÍA: {nombre}")
    print("#" * 80)

    for numero, pregunta in enumerate(
        preguntas,
        start=1
    ):

        resultados = recuperar_contexto(
            pregunta,
            top_k=TOP_K
        )

        distancias = obtener_distancias(
            resultados
        )

        if distancias:
            distancias_top_1.append(
                distancias[0]
            )

        imprimir_resultado(
            numero=numero,
            categoria=nombre,
            pregunta=pregunta,
            resultados=resultados,
            distancias=distancias,
        )

    calcular_estadisticas(
        nombre,
        distancias_top_1
    )

    return distancias_top_1


# ============================================================
# PRUEBA PRINCIPAL
# ============================================================

def test_retrieval_boundary():

    print()
    print()
    print("#" * 80)
    print("# PRUEBA DE FRONTERA DE RELEVANCIA")
    print("#" * 80)

    print()
    print(
        "Esta prueba NO modifica retriever.py."
    )

    print(
        "Su objetivo es estudiar la separación "
        "entre preguntas relevantes y externas."
    )

    print()
    print(
        "Referencia visual: distancia cercana a 0 "
        "significa mayor similitud."
    )

    # --------------------------------------------------------
    # RELEVANTES
    # --------------------------------------------------------

    distancias_relevantes = ejecutar_categoria(
        "RELEVANTE",
        PREGUNTAS_RELEVANTES
    )

    # --------------------------------------------------------
    # AMBIGUAS
    # --------------------------------------------------------

    distancias_ambiguas = ejecutar_categoria(
        "AMBIGUA / CERCANA",
        PREGUNTAS_AMBIGUAS
    )

    # --------------------------------------------------------
    # EXTERNAS
    # --------------------------------------------------------

    distancias_externas = ejecutar_categoria(
        "EXTERNA CERCANA",
        PREGUNTAS_EXTERNAS
    )

    # ========================================================
    # RESUMEN GENERAL
    # ========================================================

    print()
    print()
    print("#" * 80)
    print("# RESUMEN GENERAL")
    print("#" * 80)

    calcular_estadisticas(
        "RELEVANTES",
        distancias_relevantes
    )

    calcular_estadisticas(
        "AMBIGUAS / CERCANAS",
        distancias_ambiguas
    )

    calcular_estadisticas(
        "EXTERNAS CERCANAS",
        distancias_externas
    )

    # ========================================================
    # RANGOS
    # ========================================================

    print()
    print()
    print("#" * 80)
    print("# ANÁLISIS DE RANGOS")
    print("#" * 80)

    if (
        distancias_relevantes
        and distancias_ambiguas
        and distancias_externas
    ):

        max_relevante = max(
            distancias_relevantes
        )

        min_relevante = min(
            distancias_relevantes
        )

        max_ambigua = max(
            distancias_ambiguas
        )

        min_ambigua = min(
            distancias_ambiguas
        )

        max_externa = max(
            distancias_externas
        )

        min_externa = min(
            distancias_externas
        )

        print()
        print(
            f"RELEVANTES:"
        )

        print(
            f"  mínimo = {min_relevante:.6f}"
        )

        print(
            f"  máximo = {max_relevante:.6f}"
        )

        print()
        print(
            f"AMBIGUAS / CERCANAS:"
        )

        print(
            f"  mínimo = {min_ambigua:.6f}"
        )

        print(
            f"  máximo = {max_ambigua:.6f}"
        )

        print()
        print(
            f"EXTERNAS CERCANAS:"
        )

        print(
            f"  mínimo = {min_externa:.6f}"
        )

        print(
            f"  máximo = {max_externa:.6f}"
        )

        # ----------------------------------------------------
        # SEPARACIÓN RELEVANTE / EXTERNA
        # ----------------------------------------------------

        separacion_relevante_externa = (
            min_externa -
            max_relevante
        )

        print()
        print(
            "SEPARACIÓN RELEVANTE -> EXTERNA:"
        )

        print(
            f"  {separacion_relevante_externa:.6f}"
        )

        # ----------------------------------------------------
        # SEPARACIÓN RELEVANTE / AMBIGUA
        # ----------------------------------------------------

        separacion_relevante_ambigua = (
            min_ambigua -
            max_relevante
        )

        print()
        print(
            "SEPARACIÓN RELEVANTE -> AMBIGUA:"
        )

        print(
            f"  {separacion_relevante_ambigua:.6f}"
        )

        # ----------------------------------------------------
        # SEPARACIÓN AMBIGUA / EXTERNA
        # ----------------------------------------------------

        separacion_ambigua_externa = (
            min_externa -
            max_ambigua
        )

        print()
        print(
            "SEPARACIÓN AMBIGUA -> EXTERNA:"
        )

        print(
            f"  {separacion_ambigua_externa:.6f}"
        )

    # ========================================================
    # PREGUNTAS CERCANAS AL UMBRAL
    # ========================================================

    todas_las_distancias = []

    for distancia in distancias_relevantes:
        todas_las_distancias.append(
            ("RELEVANTE", distancia)
        )

    for distancia in distancias_ambiguas:
        todas_las_distancias.append(
            ("AMBIGUA", distancia)
        )

    for distancia in distancias_externas:
        todas_las_distancias.append(
            ("EXTERNA", distancia)
        )

    todas_las_distancias.sort(
        key=lambda item: item[1]
    )

    print()
    print()
    print("#" * 80)
    print("# DISTANCIAS CERCANAS A LA ZONA 0.45 - 0.55")
    print("#" * 80)

    encontradas = False

    for categoria, distancia in todas_las_distancias:

        if 0.45 <= distancia <= 0.55:

            encontradas = True

            print(
                f"{categoria:10} | "
                f"distance={distancia:.6f} | "
                f"similarity="
                f"{calcular_similitud(distancia):.2f}%"
            )

    if not encontradas:

        print(
            "No hubo resultados dentro "
            "del rango 0.45 - 0.55."
        )

    # ========================================================
    # REFERENCIA DEL POSIBLE UMBRAL
    # ========================================================

    print()
    print()
    print("#" * 80)
    print("# REFERENCIA DEL UMBRAL 0.49")
    print("#" * 80)

    umbral_referencia = 0.49

    print()
    print(
        f"Umbral de referencia: "
        f"{umbral_referencia:.2f}"
    )

    print()
    print(
        "IMPORTANTE:"
    )

    print(
        "Este umbral todavía NO se aplica "
        "al sistema."
    )

    print(
        "Solamente se utiliza para observar "
        "cómo se comportarían los resultados."
    )

    # --------------------------------------------------------
    # RELEVANTES
    # --------------------------------------------------------

    relevantes_aprobadas = sum(
        1
        for distancia in distancias_relevantes
        if distancia <= umbral_referencia
    )

    # --------------------------------------------------------
    # AMBIGUAS
    # --------------------------------------------------------

    ambiguas_aprobadas = sum(
        1
        for distancia in distancias_ambiguas
        if distancia <= umbral_referencia
    )

    # --------------------------------------------------------
    # EXTERNAS
    # --------------------------------------------------------

    externas_aprobadas = sum(
        1
        for distancia in distancias_externas
        if distancia <= umbral_referencia
    )

    print()
    print(
        f"RELEVANTES <= {umbral_referencia}: "
        f"{relevantes_aprobadas}/"
        f"{len(distancias_relevantes)}"
    )

    print(
        f"AMBIGUAS <= {umbral_referencia}: "
        f"{ambiguas_aprobadas}/"
        f"{len(distancias_ambiguas)}"
    )

    print(
        f"EXTERNAS <= {umbral_referencia}: "
        f"{externas_aprobadas}/"
        f"{len(distancias_externas)}"
    )

    print()
    print("#" * 80)
    print("# FIN DE LA PRUEBA")
    print("#" * 80)

    assert True