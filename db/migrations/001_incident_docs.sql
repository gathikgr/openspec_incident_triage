-- Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for storing incident runbooks and documentation
CREATE TABLE IF NOT EXISTS incident_docs (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    service TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT unique_service_title UNIQUE (service, title)
);

-- Index for vector similarity search using ivfflat or hnsw (HNSW is preferred on modern pgvector)
CREATE INDEX IF NOT EXISTS incident_docs_embedding_idx 
ON incident_docs 
USING hnsw (embedding vector_cosine_ops);

-- Index for JSONB metadata filtering
CREATE INDEX IF NOT EXISTS incident_docs_metadata_idx 
ON incident_docs 
USING gin (metadata);

-- RPC function for semantic matching with optional JSONB metadata containment filter
CREATE OR REPLACE FUNCTION match_incident_docs (
    query_embedding VECTOR(768),
    match_count INT DEFAULT 5,
    filter JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id BIGINT,
    title TEXT,
    service TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        incident_docs.id,
        incident_docs.title,
        incident_docs.service,
        incident_docs.content,
        incident_docs.metadata,
        1 - (incident_docs.embedding <=> query_embedding) AS similarity
    FROM incident_docs
    WHERE 
        (filter = '{}'::jsonb OR incident_docs.metadata @> filter)
    ORDER BY incident_docs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
