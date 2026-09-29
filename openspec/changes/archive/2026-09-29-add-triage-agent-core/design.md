# Design: Core Triage Agent

## Architecture & Graph Flow
1. **LangGraph State Graph**:
   - `AgentState`: `messages: Annotated[Sequence[BaseMessage], add_messages]`.
   - Nodes: `agent` (calls LLM with tools bound), `safe_tools` (ToolNode executing `query_service_health`, `search_remediation_runbooks`).
   - Conditional Edges: If `last_message.tool_calls` is non-empty -> `safe_tools`, else -> `END`.

2. **Database & Checkpointer**:
   - Primary: `PostgresSaver` backed by `psycopg_pool.ConnectionPool` (max_size=10, autocommit=True, connect_timeout=15, kwargs `prepare_threshold=None` for transaction poolers).
   - Test/Local fallback: `MemorySaver` when `DATABASE_URL` is unset or database connection fails during local testing.

3. **Content Normalisation (`extract_text`)**:
   - Handles `str`, `list` of dicts/strings (common in Gemini multi-part responses), and message objects, returning flat text.

4. **Safe Tools**:
   - `query_service_health`: In-memory service registry returning health metrics, error rates, and status.
   - `search_remediation_runbooks`: Calls Gemini embedding with `RETRIEVAL_QUERY` and executes `match_incident_docs` RPC or fallback matcher.
