import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from agent import (
    get_agent_app,
    approve_thread,
    reject_thread,
    extract_text,
    escalate_ticket
)

def test_escalate_ticket_tool():
    res = escalate_ticket.invoke({"ticket_title": "Auth 504 outage", "severity": "P1"})
    assert "Incident Ticket Created" in res
    assert "P1" in res

def test_hitl_pause_on_escalate():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    # LLM decides to escalate immediately
    escalate_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "escalate_ticket",
            "args": {"ticket_title": "Auth Outage", "severity": "P1"},
            "id": "esc_123"
        }]
    )
    mock_llm.invoke.return_value = escalate_msg

    checkpointer = MemorySaver()
    app = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "pause-thread-1"}}
    result = app.invoke({"messages": [HumanMessage(content="Auth is completely down, escalate!")]}, config)

    # Check that execution paused before sensitive_tools
    state = app.get_state(config)
    assert "sensitive_tools" in state.next
    assert len(state.values["messages"]) == 2  # Human + AI tool call

def test_hitl_approve_execution():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    escalate_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "escalate_ticket",
            "args": {"ticket_title": "Database Outage", "severity": "P1"},
            "id": "esc_456"
        }]
    )
    final_msg = AIMessage(content="Escalation approved. Ticket created and on-call team alerted.")
    mock_llm.invoke.side_effect = [escalate_msg, final_msg]

    checkpointer = MemorySaver()
    app = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "approve-thread-1"}}
    app.invoke({"messages": [HumanMessage(content="DB down")]}, config)

    # State is paused
    assert "sensitive_tools" in app.get_state(config).next

    # Engineer approves
    res = approve_thread(app, "approve-thread-1")
    assert extract_text(res["messages"][-1].content) == "Escalation approved. Ticket created and on-call team alerted."

    # Verify tool execution in message history
    messages = res["messages"]
    assert any(isinstance(m, ToolMessage) and "Incident Ticket Created" in m.content for m in messages)

def test_hitl_reject_execution():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    escalate_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "escalate_ticket",
            "args": {"ticket_title": "Minor warning", "severity": "P3"},
            "id": "esc_789"
        }]
    )
    resumed_msg = AIMessage(content="Acknowledged rejection. Continuing local investigation without ticket.")
    mock_llm.invoke.side_effect = [escalate_msg, resumed_msg]

    checkpointer = MemorySaver()
    app = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "reject-thread-1"}}
    app.invoke({"messages": [HumanMessage(content="Escalate this warning")]}, config)

    # Engineer rejects
    res = reject_thread(app, "reject-thread-1", reason="Not severe enough for paging")
    assert extract_text(res["messages"][-1].content) == "Acknowledged rejection. Continuing local investigation without ticket."

    # Verify tool execution was NOT run, but rejected ToolMessage was recorded
    messages = res["messages"]
    assert not any("Incident Ticket Created" in str(m.content) for m in messages)
    assert any(isinstance(m, ToolMessage) and "Rejected by engineer: Not severe enough for paging" in m.content for m in messages)
