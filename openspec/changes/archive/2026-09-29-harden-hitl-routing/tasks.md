# Tasks: Harden HITL Routing

- [x] 1. Update `agent.py`
  - Modify `route_tools` to check if ANY tool call is sensitive
  - Ensure `sensitive_tools` ToolNode includes `ALL_TOOLS` so mixed safe+sensitive batches execute properly upon approval
  - Ensure `reject_thread` emits a `ToolMessage` for each tool call in `last_message.tool_calls`
- [x] 2. Update `app.py`
  - Support `pending_actions` list in triage service response
- [x] 3. Implement regression tests in `tests/test_harden_hitl.py`
  - Test mixed `[query_service_health, escalate_ticket]` pauses before `sensitive_tools`
  - Test approve on mixed batch executes both tools
  - Test reject on mixed batch emits ToolMessages for all tool calls
