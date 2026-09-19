from sentence_transformers import SentenceTransformer


# Carga el modelo BGE-M3 una sola vez para reutilizarlo durante toda la ejecución.
MODEL_NAME = "BAAI/bge-m3"

model = SentenceTransformer(MODEL_NAME)


# Genera el embedding de un texto y devuelve un vector de 1024 dimensiones.
def generar_embedding(texto: str):
    embedding = model.encode(
        texto,
        normalize_embeddings=True
    )

    return embedding