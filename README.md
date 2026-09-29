# 🛡️ Autonomous Incident Triage Agent

An autonomous incident triage and remediation agent powered by LangGraph, Google Gemini, and Supabase PostgreSQL (pgvector), built with OpenSpec spec-driven development.

## Features
- **Semantic Runbook Retrieval**: Embeds and searches incident runbooks with Gemini embeddings (768 dimensions) stored in pgvector.
- **Health-First Triage**: Checks service health metrics before diagnosing incidents.
- **Human-in-the-Loop (HITL) Guardrails**: Critical escalation actions (`escalate_ticket`) are interrupted and paused until explicitly approved or rejected by an on-call engineer.
- **Unified Interface**: Single ASGI app serving both REST API endpoints (`/chat`, `/approve`, `/healthz`) and a real-time Gradio Blocks UI mounted at `/`.
- **Zero-Cost Deployment**: Ready for free hosting on Render and Supabase with state persistence across spin-downs.

## Project Structure
```
├── agent.py                 # LangGraph triage graph, tools, checkpointer, and HITL logic
├── app.py                   # FastAPI + Gradio unified web application
├── seed_rag.py              # Idempotent runbook vector database seeding
├── render.yaml              # Render blueprint for cloud deployment
├── db/
│   └── migrations/
│       └── 001_incident_docs.sql # pgvector migration & match_incident_docs RPC function
├── openspec/                # Living specs, changes, and configuration
└── tests/                   # Pytest test suite mocking LLM and DB
```

## Quickstart

### 1. Prerequisites & Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file (never committed to git):
```env
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:6543/postgres
PORT=7860
```

### 3. Database Migration & Seeding
1. Execute `db/migrations/001_incident_docs.sql` in your Supabase SQL Editor.
2. Seed the runbooks:
```bash
python seed_rag.py
```

### 4. Run Locally
```bash
python app.py
```
- Gradio UI: `http://localhost:7860`
- API Docs: `http://localhost:7860/docs`
- Health check: `http://localhost:7860/healthz`

### 5. Running Tests
```bash
pytest -q
```

## Deploying to Render
1. Push your repository to GitHub.
2. In the Render Dashboard, create a **New Blueprint** and connect your repo (or create a **New Web Service** using `render.yaml`).
3. Under Environment Variables, set `GEMINI_API_KEY` and `DATABASE_URL`.
4. *Free Tier Note*: Render free web services spin down after 15 minutes of inactivity. First wake-up requests take ~30-60s. Conversation state and interrupted approvals survive cold starts seamlessly via PostgreSQL checkpointing.
