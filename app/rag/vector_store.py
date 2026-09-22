import chromadb
from pathlib import Path


# Ruta donde ChromaDB almacenará permanentemente nuestra base vectorial.
VECTOR_STORE_DIR = Path("data/vector_store")


# Crea el cliente persistente de ChromaDB.
client = chromadb.PersistentClient(
    path=str(VECTOR_STORE_DIR)
)


# Obtiene la colección del RAG o la crea si todavía no existe.
def get_collection():
    return client.get_or_create_collection(
        name="rag_documents"
    )


# Guarda chunks, embeddings y metadatos en ChromaDB.
def add_chunks(ids, texts, embeddings, metadatas):
    collection = get_collection()

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )


# Busca los chunks más similares a un embedding.
def search(query_embedding, top_k=5):
    collection = get_collection()

    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )


# Devuelve la cantidad de chunks almacenados.
def get_collection_count():
    collection = get_collection()

    return collection.count()