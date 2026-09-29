import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

from agent import get_agent_app
from app import fastapi_app, set_service_agent_app, run_triage_service, handle_approval_service

client = TestClient(fastapi_app)

@pytest.fixture(autouse=True)
def reset_agent_fixture():
    # Setup test agent with MemorySaver and mock LLM
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    checkpointer = MemorySaver()
    app_instance = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)
    set_service_agent_app(app_instance)
    yield (app_instance, mock_llm)

def test_api_chat_safe_completed(reset_agent_fixture):
    app_instance, mock_llm = reset_agent_fixture
    mock_llm.invoke.return_value = AIMessage(content="Everything is operating normally.")

    response = client.post("/chat", json={"thread_id": "api-thread-1", "message": "Check system status"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert "Everything is operating normally." in data["response"]
    assert data["pending_action"] is None

def test_api_chat_awaiting_approval(reset_agent_fixture):
    app_instance, mock_llm = reset_agent_fixture
    escalate_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "escalate_ticket",
            "args": {"ticket_title": "Critical Auth Outage", "severity": "P1"},
            "id": "call_esc_1"
        }]
    )
    mock_llm.invoke.return_value = escalate_msg

    response = client.post("/chat", json={"thread_id": "api-thread-2", "message": "Auth down!"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AWAITING_APPROVAL"
    assert data["pending_action"]["name"] == "escalate_ticket"

def test_api_approve_resolution(reset_agent_fixture):
    app_instance, mock_llm = reset_agent_fixture
    escalate_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "escalate_ticket",
            "args": {"ticket_title": "Database Outage", "severity": "P1"},
            "id": "call_esc_2"
        }]
    )
    final_msg = AIMessage(content="P1 ticket created and paging alert dispatched.")
    mock_llm.invoke.side_effect = [escalate_msg, final_msg]

    # Initial trigger to pause
    client.post("/chat", json={"thread_id": "api-thread-3", "message": "DB down!"})

    # Approve
    response = client.post("/approve", json={"thread_id": "api-thread-3", "approved": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"
    assert "P1 ticket created" in data["response"]

def test_api_approve_rejection(reset_agent_fixture):
    app_instance, mock_llm = reset_agent_fixture
    escalate_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "escalate_ticket",
            "args": {"ticket_title": "Minor alert", "severity": "P3"},
            "id": "call_esc_3"
        }]
    )
    resumed_msg = AIMessage(content="Understood. Reverting escalation.")
    mock_llm.invoke.side_effect = [escalate_msg, resumed_msg]

    client.post("/chat", json={"thread_id": "api-thread-4", "message": "Alert!"})

    # Reject
    response = client.post("/approve", json={
        "thread_id": "api-thread-4",
        "approved": False,
        "rejection_reason": "False alarm"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED_AND_RESUMED"
    assert "Understood. Reverting escalation." in data["response"]

def test_api_approve_unpaused_returns_400(reset_agent_fixture):
    app_instance, mock_llm = reset_agent_fixture
    mock_llm.invoke.return_value = AIMessage(content="All healthy.")

    client.post("/chat", json={"thread_id": "api-thread-5", "message": "Health check"})

    # Thread 5 is completed, not paused
    response = client.post("/approve", json={"thread_id": "api-thread-5", "approved": True})
    assert response.status_code == 400
    assert "not awaiting approval" in response.json()["detail"]
