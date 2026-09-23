-- =========================================================
-- EXTENSIÓN PGVECTOR
-- =========================================================

CREATE EXTENSION IF NOT EXISTS vector;


-- =========================================================
-- TABLA: documents
--
-- Representa cada documento cargado al sistema.
-- =========================================================

CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,

    filename TEXT NOT NULL,

    sha256 CHAR(64) NOT NULL UNIQUE,

    size_bytes BIGINT NOT NULL,

    content_type TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- TABLA: chunks
--
-- Representa cada fragmento generado a partir de un documento.
-- =========================================================

CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,

    document_id BIGINT NOT NULL,

    chunk_index INTEGER NOT NULL,

    text TEXT NOT NULL,

    embedding VECTOR(1024) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chunks_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_document_chunk_index
        UNIQUE (document_id, chunk_index)
);


-- =========================================================
-- ÍNDICE PARA RELACIONAR RÁPIDAMENTE LOS CHUNKS
-- CON SU DOCUMENTO
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_chunks_document_id
    ON chunks(document_id);