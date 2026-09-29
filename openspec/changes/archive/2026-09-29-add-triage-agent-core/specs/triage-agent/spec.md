# Delta for triage-agent

## ADDED Requirements

### Requirement: Health-first investigation
The agent SHALL check service health via `query_service_health` before searching runbooks when diagnosing an incident.

#### Scenario: Inspect health before runbooks
- GIVEN a reported incident for the auth service
- WHEN the agent executes its investigation
- THEN the first tool called is `query_service_health` for "auth"

### Requirement: Runbook retrieval
The agent SHALL retrieve the top 2 relevant runbooks using `search_remediation_runbooks` or return a "No relevant runbooks found" message when none match.

#### Scenario: Matching runbooks found
- GIVEN an active incident and service query
- WHEN `search_remediation_runbooks` is executed
- THEN at most 2 top-scoring runbook summaries are returned

#### Scenario: No matching runbooks
- GIVEN a query with no semantic overlap in the database
- WHEN `search_remediation_runbooks` is executed
- THEN a clear not-found message is returned without raising an exception

### Requirement: Unknown service handling
The `query_service_health` tool SHALL return a status message rather than raising an exception when queried for an unknown service.

#### Scenario: Unknown service queried
- GIVEN a query for service "billing"
- WHEN `query_service_health("billing")` is called
- THEN it returns a status indicating unknown or not found without error

### Requirement: State persistence
Given a `thread_id`, the agent conversation state SHALL persist and be reloadable across invocations.

#### Scenario: Conversation resumes for thread
- GIVEN a completed turn on `thread_id` "thread-123"
- WHEN a subsequent invocation runs with the same `thread_id`
- THEN previous message history is preserved in graph state

### Requirement: Content normalisation
The agent SHALL normalize list-structured or dictionary-structured model responses to clean string content.

#### Scenario: List structured content normalized
- GIVEN a model output containing structured text parts in a list
- WHEN `extract_text` processes the message
- THEN it returns a single concatenated plain text string
