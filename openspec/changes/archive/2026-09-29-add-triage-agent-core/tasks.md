# Tasks: Add Core Triage Agent

- [x] 1. Implement `agent.py`
  - Define `AgentState`, system prompt, and `extract_text`
  - Implement `query_service_health` and `search_remediation_runbooks`
  - Construct LangGraph state graph with `safe_tools` and PostgresSaver/MemorySaver checkpointer
  - Export `get_agent_app()`
- [x] 2. Implement unit tests in `tests/test_agent_core.py`
  - Mock LLM tool calls and responses
  - Test health-first routing and runbook retrieval
  - Test `extract_text` normalisation
  - Test thread state persistence across calls
