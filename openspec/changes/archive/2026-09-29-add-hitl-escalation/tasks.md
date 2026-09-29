# Tasks: Add HITL Escalation

- [x] 1. Update `agent.py`
  - Add `escalate_ticket` tool
  - Add `sensitive_tools` ToolNode and configure `interrupt_before=["sensitive_tools"]`
  - Update `route_tools` to route sensitive tool calls to `sensitive_tools`
  - Add helper functions `approve_thread` and `reject_thread`
- [x] 2. Implement unit tests in `tests/test_hitl_escalation.py`
  - Test pause on escalation tool call
  - Test resume on approval
  - Test rejection with injected ToolMessage
  - Test state persistence while paused
