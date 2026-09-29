# Proposal: Harden HITL Routing

## Why
If the LLM emits multiple tool calls in a single message (parallel tool calls containing both safe and sensitive calls), routing logic that only checks `tool_calls[0]` fails to detect sensitive tools placed after safe tools. We must harden routing to intercept if ANY tool call is sensitive.

## What Changes
- Update `route_tools` in `agent.py` to check if `any(tc["name"] == "escalate_ticket" for tc in last_message.tool_calls)`.
- Update `sensitive_tools` ToolNode to bind all tools or execute safely so mixed batches are supported.
- Update `app.py` to return all pending sensitive actions in `pending_actions`.
- Ensure `reject_thread` in `agent.py` emits a `ToolMessage` for EVERY pending tool call so LangGraph conversation state is valid.
- Add regression tests in `tests/test_harden_hitl.py`.

## Capabilities Affected
- `hitl-approval` (MODIFIED)

## Rollback Note
Revert routing logic changes in `agent.py`.
