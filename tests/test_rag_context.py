from app.rag.retriever import recuperar_contexto
from app.rag.context_builder import construir_contexto


# Comprueba el flujo completo de recuperación semántica
# y construcción del contexto RAG.
def test_generar_contexto_rag():

    pregunta = "¿Cómo se registran los artistas?"

    resultados = recuperar_contexto(
        pregunta,
        top_k=5
    )

    contexto = construir_contexto(resultados)

    assert len(resultados) == 5
    assert contexto

    print("\n\n===== CONTEXTO RAG =====")
    print(contexto)