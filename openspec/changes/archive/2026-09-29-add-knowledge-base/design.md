# Design: Knowledge Base

## Context & Key Decisions
1. **Embedding Model & Dimensionality**:
   - Using Gemini embeddings (`text-embedding-004` or `models/text-embedding-004`) via `langchain-google-genai` / `google-genai` with `output_dimensionality=768` (or default 768) and `task_type="RETRIEVAL_DOCUMENT"` for seeding and `task_type="RETRIEVAL_QUERY"` for querying.
2. **Postgres & Vector Store**:
   - Supabase PostgreSQL with `pgvector` extension.
   - Table `incident_docs` stores `id` (bigserial/uuid), `title` (text), `service` (text), `content` (text), `metadata` (jsonb), and `embedding` (vector(768)).
   - Unique constraint or index on `(service, title)` or deterministic content hash to ensure idempotent inserts via `ON CONFLICT DO UPDATE` or `ON CONFLICT DO NOTHING`.
3. **RPC Function**:
   - `match_incident_docs` takes `query_embedding vector(768)`, `match_count int DEFAULT 5`, `filter jsonb DEFAULT '{}'` and returns matching rows with `similarity` (1 - cosine distance).
4. **Free-tier Limits & Pooler**:
   - Connects through Supabase transaction pooler (port 6543) using `psycopg_pool.ConnectionPool` with `prepare_threshold=None` to prevent prepared statement errors on poolers.
