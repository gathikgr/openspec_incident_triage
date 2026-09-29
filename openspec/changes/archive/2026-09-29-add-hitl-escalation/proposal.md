# Proposal: Add HITL Escalation

## Why
Critical incident remediation tools, such as creating emergency escalation tickets and alerting on-call engineers, must not be executed autonomously without explicit human verification and approval.

## What Changes
- Add sensitive tool `escalate_ticket(ticket_title: str, severity: str)` to `agent.py`.
- Add `sensitive_tools` ToolNode to the LangGraph graph with `interrupt_before=["sensitive_tools"]`.
- Update `route_tools` to route calls targeting `escalate_ticket` to `sensitive_tools`.
- Support resume upon approval (`app.invoke(None, config)`) and rejection handling (injecting `ToolMessage` via `app.update_state` as `sensitive_tools`).
- Add comprehensive unit tests in `tests/test_hitl_escalation.py` covering pause, approve, reject, and persistence.

## Capabilities Affected
- `hitl-approval` (ADDED)

## Rollback Note
Remove `sensitive_tools` node and `escalate_ticket` tool from `agent.py`.
