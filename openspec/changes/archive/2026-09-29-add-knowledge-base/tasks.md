# Tasks: Add Knowledge Base

- [x] 1. Create SQL migration `db/migrations/001_incident_docs.sql`
  - Enable `vector` extension
  - Create `incident_docs` table with `vector(768)`
  - Add unique constraint for idempotency
  - Create `match_incident_docs` function
- [x] 2. Create `seed_rag.py`
  - Implement Gemini embedding generation with `RETRIEVAL_DOCUMENT` and 768 dims
  - Define runbooks for Auth 504 timeouts, Database high latency, Payment gateway failures
  - Implement idempotent seeding into Supabase pgvector
- [x] 3. Create unit tests in `tests/test_knowledge_base.py`
  - Mock embeddings client and database connection
  - Test seed idempotency logic and SQL function call structure
