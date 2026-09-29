# Design: Harden HITL Routing

## Architecture & Edge Cases
1. **Parallel / Mixed Tool Calls**:
   - `route_tools`:
     ```python
     if any(tc.get("name") in SENSITIVE_TOOL_NAMES for tc in last_message.tool_calls):
         return "sensitive_tools"
     return "safe_tools"
     ```
   - When routed to `sensitive_tools`, all tools (`ALL_TOOLS`) are available on the node so any accompanying safe tool calls also execute correctly once approved.
2. **Rejection across Multiple Tool Calls**:
   - `reject_thread` loops through every tool call in `last_message.tool_calls` and produces a separate `ToolMessage(content=..., tool_call_id=tc["id"])`.
   - This ensures LangGraph and LLM state requirements (every tool call ID must be matched by a ToolMessage) are strictly satisfied.
3. **Payload Reporting**:
   - `app.py` extracts all pending actions into `pending_actions` and surfaces them in API responses and UI labels.
