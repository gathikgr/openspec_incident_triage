# Tasks: Add REST API and Gradio UI

- [x] 1. Implement `app.py`
  - Create shared service layer (`run_triage_service`, `handle_approval_service`)
  - Create FastAPI application with `POST /chat` and `POST /approve`
  - Create Gradio Blocks UI and mount at `/`
  - Expose single ASGI `app` object
- [x] 2. Implement unit and integration tests in `tests/test_api_and_ui.py`
  - Test `POST /chat` with safe tools (`COMPLETED`)
  - Test `POST /chat` with sensitive escalation (`AWAITING_APPROVAL`)
  - Test `POST /approve` for approved and rejected flows
  - Test `POST /approve` HTTP 400 when nothing is pending
