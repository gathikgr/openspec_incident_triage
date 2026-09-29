# Design: REST API and Gradio UI

## Architecture & Integration
1. **Shared Service Layer**:
   - `run_triage_service(thread_id, message)`: Invokes agent graph. Returns dictionary with status (`COMPLETED` vs `AWAITING_APPROVAL`), response text, and pending action metadata.
   - `handle_approval_service(thread_id, approved, reason)`: Checks if thread is awaiting approval (raises 400 if not). Executes `approve_thread` or `reject_thread`.
2. **FastAPI Endpoints**:
   - `POST /chat` with Pydantic model `ChatRequest(thread_id, message)`.
   - `POST /approve` with Pydantic model `ApprovalRequest(thread_id, approved, rejection_reason=None)`.
3. **Gradio UI**:
   - Built using `gr.Blocks(title="Autonomous Incident Triage Agent")`.
   - Mounted onto FastAPI at path `"/"` via `gr.mount_gradio_app(app, blocks, path="/")`.
   - Single ASGI application exported as `app`.
4. **Port Configuration**:
   - Default port `int(os.getenv("PORT", "7860"))`.
