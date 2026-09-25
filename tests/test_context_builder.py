from app.rag.context_builder import construir_contexto


# Comprueba que los resultados recuperados se convierten
# correctamente en un único contexto textual.
def test_construir_contexto():

    resultados = [
        {
            "id": 36,
            "chunk_index": 1,
            "text": "Información sobre el registro de artistas.",
            "distance": 0.34
        },
        {
            "id": 31,
            "chunk_index": 9,
            "text": "Información sobre el proceso de registro.",
            "distance": 0.37
        }
    ]

    contexto = construir_contexto(resultados)

    assert "[Fragmento 1]" in contexto
    assert "[Fragmento 2]" in contexto

    assert "Información sobre el registro de artistas." in contexto
    assert "Información sobre el proceso de registro." in contexto