# Proposal: Add Core Triage Agent

## Why
Implement the core LangGraph autonomous triage agent that performs health checks and searches incident runbooks to investigate system alerts before deciding on next steps.

## What Changes
- Implement `agent.py` with:
  - `query_service_health` and `search_remediation_runbooks` safe tools.
  - `extract_text` helper to normalise Gemini string/list responses.
  - LangGraph state graph with `agent` node and `safe_tools` ToolNode.
  - `PostgresSaver` checkpointer over `psycopg_pool.ConnectionPool` (or MemorySaver fallback for testing).
  - `get_agent_app()` factory function.
- Implement comprehensive unit tests in `tests/test_agent_core.py` mocking LLM tool calls and verifying graph flow and thread state persistence.

## Capabilities Affected
- `triage-agent` (ADDED)

## Rollback Note
Revert `agent.py` and `tests/test_agent_core.py`.
