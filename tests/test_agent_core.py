import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from agent import (
    extract_text,
    query_service_health,
    search_remediation_runbooks,
    get_agent_app,
    SERVICES_HEALTH_DB
)

def test_extract_text_variants():
    # Plain string
    assert extract_text("hello world") == "hello world"

    # List of strings
    assert extract_text(["hello", "world"]) == "hello\nworld"

    # List of dicts
    assert extract_text([{"text": "part 1"}, {"text": "part 2"}]) == "part 1\npart 2"

    # Dict with text
    assert extract_text({"text": "single dict"}) == "single dict"

def test_query_service_health():
    auth_res = query_service_health.invoke({"service": "auth"})
    assert "DEGRADED" in auth_res
    assert "504" in auth_res

    unknown_res = query_service_health.invoke({"service": "billing"})
    assert "HEALTHY" in unknown_res or "status" in unknown_res

def test_search_remediation_runbooks_fallback():
    res = search_remediation_runbooks.invoke({"query": "504 timeouts", "service": "auth"})
    assert "Auth Service 504 Timeouts" in res
    assert "Redis token cache" in res

def test_agent_graph_execution_mocked():
    # Mock LLM that emits a tool call then a final answer
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    tool_call_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "query_service_health",
            "args": {"service": "auth"},
            "id": "call_123"
        }]
    )
    final_msg = AIMessage(content="Auth service is degraded due to Redis exhaustion.")

    mock_llm.invoke.side_effect = [tool_call_msg, final_msg]

    checkpointer = MemorySaver()
    app = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "test-thread-1"}}
    result = app.invoke({"messages": [HumanMessage(content="Check auth service")]}, config)

    messages = result["messages"]
    assert len(messages) >= 3
    assert any(isinstance(m, ToolMessage) and "DEGRADED" in m.content for m in messages)
    assert extract_text(messages[-1].content) == "Auth service is degraded due to Redis exhaustion."

def test_thread_state_persistence():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    msg_1 = AIMessage(content="First turn response.")
    msg_2 = AIMessage(content="Second turn response.")
    mock_llm.invoke.side_effect = [msg_1, msg_2]

    checkpointer = MemorySaver()
    app = get_agent_app(llm_override=mock_llm, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "persist-thread-1"}}
    
    # First turn
    res1 = app.invoke({"messages": [HumanMessage(content="Hello")]}, config)
    assert len(res1["messages"]) == 2

    # Second turn on same thread
    res2 = app.invoke({"messages": [HumanMessage(content="Follow up question")]}, config)
    assert len(res2["messages"]) == 4
    assert res2["messages"][0].content == "Hello"
    assert res2["messages"][2].content == "Follow up question"
