# Proposal: Add Knowledge Base

## Why
The Autonomous Incident Triage Agent needs a semantic search layer to look up relevant remediation runbooks when investigating system alerts and incidents.

## What Changes
- Add SQL migration (`db/migrations/001_incident_docs.sql`) to configure pgvector, create the `incident_docs` table (content, jsonb metadata, 768-dim embeddings), and create the `match_incident_docs` RPC function for cosine similarity search with metadata filtering.
- Add project dependencies in `requirements.txt`.
- Add `seed_rag.py` to embed and seed 3 sample incident runbooks (auth 504 timeouts, database high latency, payment gateway failures) using Gemini embeddings (`RETRIEVAL_DOCUMENT`, 768 dimensions) idempotently.
- Add unit tests with mock DB and embedding clients.

## Capabilities Affected
- `knowledge-base` (ADDED)

## Rollback Note
Drop `incident_docs` table and `match_incident_docs` function in the Supabase database.
