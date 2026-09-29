# Autonomous Incident Triage Agent

## Overview
An autonomous incident triage agent that investigates system incidents, retrieves remediation runbooks from a vector database (pgvector in Supabase), evaluates health status, and proposes or executes safe remediation actions while strictly gating sensitive actions (like ticket escalation or destructive interventions) behind a Human-in-the-Loop (HITL) approval process.

## Key Capabilities

1. **Knowledge Base (Runbook Storage & Semantic Search)**
   - Runbooks stored in PostgreSQL with `pgvector` in Supabase table `incident_docs`.
   - Embeddings generated via Google Gemini (`text-embedding-004` or `embedding-001`, 768 dimensions).
   - Cosine similarity matching via `match_incident_docs` database RPC function.
   - Idempotent runbook seeding (`seed_rag.py`) covering standard incident scenarios (Auth 504 timeouts, Database high latency, Payment gateway failures).

2. **Core Triage Agent**
   - Built on LangGraph state graph with PostgreSQL checkpointer (`PostgresSaver` over `psycopg_pool`).
   - Investigates health via `query_service_health` before searching runbooks with `search_remediation_runbooks`.
   - Robust content normalisation for Gemini structured responses.

3. **Human-in-the-Loop (HITL) Escalation**
   - Sensitive tool: `escalate_ticket(ticket_title, severity)`.
   - Graph interrupts before executing sensitive tools (`interrupt_before=["sensitive_tools"]`).
   - Approvals resume the tool call; rejections inject an engineer feedback tool message and continue reasoning without executing the sensitive action.
   - Hardened routing to ensure mixed or parallel sensitive tool calls can never bypass approval.

4. **REST API & Gradio UI**
   - Single ASGI application (`app.py`) combining FastAPI endpoints (`POST /chat`, `POST /approve`, `GET /healthz`) and Gradio Blocks UI mounted at `/`.
   - Unified service layer handling state resolution, checkpointer thread resumption, and log rendering.

5. **Cloud Deployment**
   - Blueprint `render.yaml` for zero-cost hosting on Render Free Tier.
   - Cold-start resilience via PostgresSaver persistence across process recycles.
