# Proposal: Add REST API and Gradio UI

## Why
Expose the autonomous triage agent via clean REST API endpoints for programmatic integrations and a Gradio web user interface for on-call engineers to inspect logs, view incident diagnosis, and approve or reject sensitive actions.

## What Changes
- Implement unified service layer for running conversations and handling HITL decisions.
- Implement FastAPI REST endpoints:
  - `POST /chat`: start/continue triage, returns `COMPLETED` or `AWAITING_APPROVAL`.
  - `POST /approve`: approve or reject pending action, returns `RESOLVED`, `REJECTED_AND_RESUMED`, or HTTP 400.
- Implement Gradio Blocks UI mounted onto FastAPI app at `/`.
- Export unified ASGI application as `app` in `app.py`.
- Add unit and integration tests in `tests/test_api_and_ui.py`.

## Capabilities Affected
- `triage-api` (ADDED)
- `triage-ui` (ADDED)

## Rollback Note
Remove `app.py` and `tests/test_api_and_ui.py`.
