from app.rag.retriever import recuperar_contexto


def test_retrieval_external():
    pregunta = "¿Cuál es la capital de Colombia?"

    resultados = recuperar_contexto(
        pregunta,
        top_k=3
    )

    print("\n")
    print("=" * 100)
    print("PREGUNTA EXTERNA")
    print("=" * 100)
    print(pregunta)

    for posicion, resultado in enumerate(resultados, start=1):
        distancia = resultado["distance"]
        similitud = 1 - distancia

        print("\n" + "-" * 100)
        print(f"TOP-{posicion}")
        print(f"ID: {resultado['id']}")
        print(f"Chunk: {resultado['chunk_index']}")
        print(f"Distancia: {distancia:.6f}")
        print(f"Similitud: {similitud:.2%}")

        print("\nTEXTO:")
        print(resultado["text"])