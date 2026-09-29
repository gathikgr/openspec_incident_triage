import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from agent import get_agent_app, approve_thread, reject_thread, extract_text

def test_mixed_tools_routing_interception():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    # LLM returns a safe call followed by a sensitive call in parallel
    mixed_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "query_service_health",
                "args": {"service": "auth"},
                "id": "call_safe_1"
            },
            {
                "name": "escalate_ticket",
                "args": {"ticket_title": "Auth Degradation", "severity": "P2"},
                "id": "call_sens_1"
            }
        ]
    )
    mock_llm.invoke.return_value = mixed_msg

    checkpointer = MemorySaver()
    app = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "mixed-thread-1"}}
    app.invoke({"messages": [HumanMessage(content="Auth latency spike")]}, config)

    # Must pause before sensitive_tools even though tool_calls[0] was safe!
    state = app.get_state(config)
    assert "sensitive_tools" in state.next

def test_mixed_tools_approved_execution():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    mixed_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "query_service_health",
                "args": {"service": "payments"},
                "id": "call_safe_2"
            },
            {
                "name": "escalate_ticket",
                "args": {"ticket_title": "Payments Down", "severity": "P1"},
                "id": "call_sens_2"
            }
        ]
    )
    final_msg = AIMessage(content="Both health check and ticket escalation processed.")
    mock_llm.invoke.side_effect = [mixed_msg, final_msg]

    checkpointer = MemorySaver()
    app = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "mixed-thread-2"}}
    app.invoke({"messages": [HumanMessage(content="Payments failure")]}, config)

    # Approve
    res = approve_thread(app, "mixed-thread-2")
    messages = res["messages"]

    # Both tools executed
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 2
    assert any("Service 'payments'" in str(m.content) for m in tool_messages)
    assert any("Incident Ticket Created" in str(m.content) for m in tool_messages)
    assert extract_text(res["messages"][-1].content) == "Both health check and ticket escalation processed."

def test_mixed_tools_rejected_emits_all_tool_messages():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    mixed_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "query_service_health",
                "args": {"service": "database"},
                "id": "call_safe_3"
            },
            {
                "name": "escalate_ticket",
                "args": {"ticket_title": "DB High Latency", "severity": "P2"},
                "id": "call_sens_3"
            }
        ]
    )
    resumed_msg = AIMessage(content="Understood rejection. Continuing without escalation.")
    mock_llm.invoke.side_effect = [mixed_msg, resumed_msg]

    checkpointer = MemorySaver()
    app = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "mixed-thread-3"}}
    app.invoke({"messages": [HumanMessage(content="DB latency")]}, config)

    # Reject
    res = reject_thread(app, "mixed-thread-3", reason="Temporary latency jitter")
    messages = res["messages"]

    # Both tool calls must have corresponding rejection ToolMessages
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 2
    assert tool_messages[0].tool_call_id == "call_safe_3"
    assert tool_messages[1].tool_call_id == "call_sens_3"
    assert "Rejected by engineer: Temporary latency jitter" in tool_messages[0].content
    assert "Rejected by engineer: Temporary latency jitter" in tool_messages[1].content
