import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import gradio as gr
import uvicorn
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agent import get_agent_app, approve_thread, reject_thread, extract_text

load_dotenv()

# Singleton or factory for the LangGraph agent
_agent_app = None

def get_service_agent_app():
    global _agent_app
    if _agent_app is None:
        _agent_app = get_agent_app()
    return _agent_app

def set_service_agent_app(app_instance):
    """Allow overriding agent instance for testing with mocks."""
    global _agent_app
    _agent_app = app_instance

# ----------------- Service Layer -----------------

def run_triage_service(thread_id: str, message: str) -> Dict[str, Any]:
    if not thread_id or not thread_id.strip():
        raise ValueError("Thread ID cannot be empty.")
    if not message or not message.strip():
        raise ValueError("Message cannot be empty.")

    agent = get_service_agent_app()
    config = {"configurable": {"thread_id": thread_id.strip()}}
    
    result = agent.invoke({"messages": [HumanMessage(content=message.strip())]}, config)
    state = agent.get_state(config)
    
    messages = state.values.get("messages", [])
    formatted_logs = []
    for m in messages:
        sender = m.__class__.__name__
        content = extract_text(m.content)
        if hasattr(m, "tool_calls") and m.tool_calls:
            calls_str = ", ".join(f"{tc['name']}({tc.get('args', {})})" for tc in m.tool_calls)
            content = f"{content}\n*[Tool Calls: {calls_str}]*"
        formatted_logs.append(f"**{sender}**: {content}")

    log_text = "\n\n".join(formatted_logs)

    if state.next and "sensitive_tools" in state.next:
        last_msg = messages[-1] if messages else None
        pending_action = None
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            pending_action = last_msg.tool_calls[0]
        
        return {
            "status": "AWAITING_APPROVAL",
            "thread_id": thread_id,
            "response": extract_text(messages[-1].content) if messages else "",
            "pending_action": pending_action,
            "log": log_text
        }
    
    final_text = extract_text(messages[-1].content) if messages else "No response generated."
    return {
        "status": "COMPLETED",
        "thread_id": thread_id,
        "response": final_text,
        "pending_action": None,
        "log": log_text
    }

def handle_approval_service(thread_id: str, approved: bool, reason: Optional[str] = None) -> Dict[str, Any]:
    if not thread_id or not thread_id.strip():
        raise ValueError("Thread ID cannot be empty.")
    
    agent = get_service_agent_app()
    config = {"configurable": {"thread_id": thread_id.strip()}}
    state = agent.get_state(config)

    if not state or not state.next or "sensitive_tools" not in state.next:
        raise HTTPException(status_code=400, detail=f"Thread '{thread_id}' is not awaiting approval.")

    if approved:
        result = approve_thread(agent, thread_id.strip())
        status = "RESOLVED"
    else:
        rejection_reason = reason or "Rejected by on-call engineer."
        result = reject_thread(agent, thread_id.strip(), reason=rejection_reason)
        status = "REJECTED_AND_RESUMED"

    updated_state = agent.get_state(config)
    messages = updated_state.values.get("messages", [])
    
    formatted_logs = []
    for m in messages:
        sender = m.__class__.__name__
        content = extract_text(m.content)
        if hasattr(m, "tool_calls") and m.tool_calls:
            calls_str = ", ".join(f"{tc['name']}({tc.get('args', {})})" for tc in m.tool_calls)
            content = f"{content}\n*[Tool Calls: {calls_str}]*"
        formatted_logs.append(f"**{sender}**: {content}")

    log_text = "\n\n".join(formatted_logs)
    final_text = extract_text(messages[-1].content) if messages else ""

    return {
        "status": status,
        "thread_id": thread_id,
        "response": final_text,
        "log": log_text
    }

# ----------------- FastAPI App -----------------

fastapi_app = FastAPI(
    title="Autonomous Incident Triage Agent API",
    version="1.0.0",
    description="API for automated cloud incident investigation, runbook retrieval, and HITL escalation."
)

class ChatRequest(BaseModel):
    thread_id: str = Field(..., description="Unique conversation session or incident identifier")
    message: str = Field(..., description="Incident description or engineer query")

class ApprovalRequest(BaseModel):
    thread_id: str = Field(..., description="Unique thread identifier")
    approved: bool = Field(..., description="True to approve execution, False to reject")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection when approved is False")

@fastapi_app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        return run_triage_service(req.thread_id, req.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@fastapi_app.post("/approve")
def approve_endpoint(req: ApprovalRequest):
    try:
        return handle_approval_service(req.thread_id, req.approved, req.rejection_reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- Gradio UI -----------------

def create_ui():
    with gr.Blocks(title="Autonomous Incident Triage Agent") as ui:
        gr.Markdown("# 🛡️ Autonomous Incident Triage Agent")
        gr.Markdown("Investigate live alerts, query runbooks, and gate sensitive escalations with Human-in-the-Loop.")

        with gr.Row():
            with gr.Column(scale=1):
                thread_id_input = gr.Textbox(
                    label="Thread ID",
                    value="incident-001",
                    placeholder="Enter unique thread or incident ID"
                )
                incident_input = gr.Textbox(
                    label="Incident Description",
                    lines=4,
                    value="Auth service is timing out on /auth/verify with 504 errors. Investigate and remediate.",
                    placeholder="Describe symptoms, alerts, or affected services..."
                )
                trigger_btn = gr.Button("🚀 Trigger Triage", variant="primary")
                
                gr.Markdown("### ⚠️ Human-in-the-Loop Actions")
                rejection_reason_input = gr.Textbox(
                    label="Rejection Reason (if rejecting)",
                    placeholder="e.g., False alarm, manual fix already applied"
                )
                with gr.Row():
                    approve_btn = gr.Button("✅ Approve Escalation", variant="primary")
                    reject_btn = gr.Button("❌ Reject Action", variant="stop")

            with gr.Column(scale=2):
                status_box = gr.Textbox(label="Workflow State", value="IDLE", interactive=False)
                output_log = gr.Markdown(label="Agent Log & Output", value="*Awaiting incident input...*")

        def ui_trigger_triage(thread_id, msg):
            if not thread_id or not thread_id.strip():
                return "ERROR: Thread ID is required.", "*Please provide a valid Thread ID.*"
            try:
                res = run_triage_service(thread_id, msg)
                state_label = f"STATE: {res['status']}"
                if res['pending_action']:
                    state_label += f" | Pending: {res['pending_action']['name']}"
                return state_label, res['log']
            except Exception as e:
                return f"ERROR: {str(e)}", f"**Error encountered:**\n{str(e)}"

        def ui_approve(thread_id):
            if not thread_id or not thread_id.strip():
                return "ERROR: Thread ID is required.", "*Please provide a valid Thread ID.*"
            try:
                res = handle_approval_service(thread_id, approved=True)
                return f"STATE: {res['status']}", res['log']
            except HTTPException as e:
                return f"ERROR: {e.detail}", f"**Error:** {e.detail}"
            except Exception as e:
                return f"ERROR: {str(e)}", f"**Error:** {str(e)}"

        def ui_reject(thread_id, reason):
            if not thread_id or not thread_id.strip():
                return "ERROR: Thread ID is required.", "*Please provide a valid Thread ID.*"
            try:
                res = handle_approval_service(thread_id, approved=False, reason=reason)
                return f"STATE: {res['status']}", res['log']
            except HTTPException as e:
                return f"ERROR: {e.detail}", f"**Error:** {e.detail}"
            except Exception as e:
                return f"ERROR: {str(e)}", f"**Error:** {str(e)}"

        trigger_btn.click(ui_trigger_triage, inputs=[thread_id_input, incident_input], outputs=[status_box, output_log])
        approve_btn.click(ui_approve, inputs=[thread_id_input], outputs=[status_box, output_log])
        reject_btn.click(ui_reject, inputs=[thread_id_input, rejection_reason_input], outputs=[status_box, output_log])

    return ui

# Mount Gradio Blocks at root "/"
ui_blocks = create_ui()
app = gr.mount_gradio_app(fastapi_app, ui_blocks, path="/")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
