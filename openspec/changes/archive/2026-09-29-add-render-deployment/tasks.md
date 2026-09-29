# Tasks: Add Render Deployment

- [x] 1. Create `render.yaml`
  - Define free web service blueprint
  - Set Python 3.11.9 runtime, build and start commands
  - Declare environment variable placeholders (`GEMINI_API_KEY`, `DATABASE_URL`) with `sync: false`
- [x] 2. Update `app.py`
  - Add `GET /healthz` endpoint returning HTTP 200 without external calls
- [x] 3. Create `README.md`
  - Add quickstart, architecture, and Render deployment guide
  - Document cold start mitigation and PostgreSQL checkpointer state persistence
- [x] 4. Implement tests in `tests/test_deployment.py`
  - Test `GET /healthz` endpoint
  - Test that `.env` is not tracked by git
