# Delta for hitl-approval

## MODIFIED Requirements

### Requirement: Sensitive actions require human approval
The agent MUST pause before executing a model message if ANY of its tool calls is sensitive, and MUST NOT execute any sensitive tool without explicit approval for that thread.

#### Scenario: Escalation pauses
- GIVEN an incident where the model decides to call `escalate_ticket`
- WHEN the graph runs
- THEN execution stops before the `sensitive_tools` node
- AND no ticket is created

#### Scenario: Approved escalation executes
- GIVEN a thread paused before `sensitive_tools`
- WHEN an engineer approves
- THEN `escalate_ticket` runs once and the agent produces a final response

#### Scenario: Rejected escalation is not executed
- GIVEN a thread paused before `sensitive_tools`
- WHEN an engineer rejects with a reason
- THEN `escalate_ticket` is never executed
- AND the agent receives the rejection reason and continues reasoning

#### Scenario: Pause survives restart
- GIVEN a thread paused before `sensitive_tools`
- WHEN the process restarts
- THEN the thread is still awaiting approval

#### Scenario: Mixed safe and sensitive calls
- GIVEN the model returns [query_service_health, escalate_ticket] in one message
- WHEN the graph runs
- THEN execution pauses for approval
- AND the approval payload lists escalate_ticket

#### Scenario: Rejection answers every pending call
- GIVEN a paused message with two tool calls
- WHEN an engineer rejects
- THEN each tool call receives a ToolMessage and no sensitive tool executes
