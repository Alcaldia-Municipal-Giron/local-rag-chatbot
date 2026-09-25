from app.rag.retriever import recuperar_contexto


# Prueba la recuperación semántica utilizando una pregunta relacionada con GAIA.
def test_recuperar_contexto_gaia():

    pregunta = "¿Qué es GAIA?"

    resultados = recuperar_contexto(
        pregunta,
        top_k=5
    )

    assert len(resultados) == 5

    print("\n\n===== RESULTADOS: ¿QUÉ ES GAIA? =====")

    for resultado in resultados:
        print("\n-----------------------------")
        print(f"ID: {resultado['id']}")
        print(f"Chunk: {resultado['chunk_index']}")
        print(f"Distancia: {resultado['distance']}")
        print(f"Texto: {resultado['text']}")


# Prueba la recuperación semántica utilizando una pregunta relacionada
# con el registro de artistas.
def test_recuperar_contexto_registro_artista():

    pregunta = "¿Cómo se registran los artistas?"

    resultados = recuperar_contexto(
        pregunta,
        top_k=5
    )

    assert len(resultados) == 5

    print("\n\n===== RESULTADOS: REGISTRO DE ARTISTAS =====")

    for resultado in resultados:
        print("\n-----------------------------")
        print(f"ID: {resultado['id']}")
        print(f"Chunk: {resultado['chunk_index']}")
        print(f"Distancia: {resultado['distance']}")
        print(f"Texto: {resultado['text']}")