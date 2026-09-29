# Design: Render Deployment

## Configuration & Architecture
1. **Render Blueprint (`render.yaml`)**:
   - `type: web`
   - `name: autonomous-incident-triage-agent`
   - `runtime: python`
   - `plan: free`
   - `buildCommand: pip install -r requirements.txt`
   - `startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT`
   - `envVars`:
     - `PYTHON_VERSION`: `3.11.9`
     - `GEMINI_API_KEY`: `sync: false`
     - `DATABASE_URL`: `sync: false`
2. **Health Check**:
   - `GET /healthz` added to `fastapi_app` returning `{"status": "ok", "service": "incident-triage-agent"}` with zero external API calls.
3. **Cold Starts on Free Tier**:
   - Free instances spin down after 15 minutes of inactivity.
   - 30-60s wake-up time on incoming request.
   - Conversational state and interrupted approval points are preserved in Supabase Postgres via `PostgresSaver`.
