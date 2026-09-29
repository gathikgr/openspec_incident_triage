# Delta for triage-ui

## ADDED Requirements

### Requirement: Interactive Gradio Interface
The web application SHALL render a Gradio interface allowing engineers to enter Thread IDs, incident descriptions, inspect logs, and approve or reject escalations.

#### Scenario: Empty thread ID validation
- GIVEN an empty Thread ID field in the UI
- WHEN the user clicks "Trigger Triage" or "Approve Escalation"
- THEN an error message is displayed prompting for a valid Thread ID

#### Scenario: Visual workflow state rendering
- GIVEN a triage session in progress
- WHEN the agent state transitions between active, awaiting approval, and completed
- THEN the Workflow State label in the UI reflects the current state
