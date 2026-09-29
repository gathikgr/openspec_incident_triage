# Design: Human-in-the-Loop Escalation

## Context & Key Decisions
1. **Tool Classification**:
   - `SAFE_TOOLS`: `query_service_health`, `search_remediation_runbooks`.
   - `SENSITIVE_TOOLS`: `escalate_ticket(ticket_title: str, severity: str)`.
2. **Graph Structure & Interrupts**:
   - Nodes: `agent`, `safe_tools`, `sensitive_tools`.
   - `interrupt_before=["sensitive_tools"]` on `workflow.compile()`.
   - `route_tools`: checks `tool_calls`. If any tool call is `escalate_ticket`, routes to `sensitive_tools`; otherwise `safe_tools`.
3. **Approval and Rejection Protocols**:
   - **Approve**: Invoking `app.invoke(None, config)` resumes the paused state directly into `sensitive_tools`, executing the tool call and returning control to `agent`.
   - **Reject**: When rejected, we do NOT execute `sensitive_tools`. Instead, we update the state with `app.update_state(config, {"messages": [ToolMessage(content=f"Rejected by engineer: {reason}", tool_call_id=tc_id)]}, as_node="sensitive_tools")` and invoke `app.invoke(None, config)` to continue reasoning.
