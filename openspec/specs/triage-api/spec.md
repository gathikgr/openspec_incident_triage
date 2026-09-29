# triage-api Specification

## Purpose
TBD - created by archiving change add-api-and-ui. Update Purpose after archive.

## Requirements

### Requirement: Triage Chat Endpoint
The API SHALL expose `POST /chat` taking `{thread_id, message}` and returning the updated triage status and agent output.

#### Scenario: Chat completes without sensitive action
- GIVEN a request to `POST /chat` where the agent resolves the inquiry using only safe tools
- WHEN the endpoint responds
- THEN status is `COMPLETED`
- AND the final agent message is returned

#### Scenario: Chat pauses awaiting approval
- GIVEN a request to `POST /chat` where the agent calls `escalate_ticket`
- WHEN the endpoint responds
- THEN status is `AWAITING_APPROVAL`
- AND `pending_action` contains the tool name and arguments

### Requirement: Triage Approval Endpoint
The API SHALL expose `POST /approve` taking `{thread_id, approved, rejection_reason}` to resume paused executions.

#### Scenario: Approval resumes and resolves
- GIVEN a thread with status `AWAITING_APPROVAL`
- WHEN `POST /approve` is called with `approved: true`
- THEN status is `RESOLVED`
- AND the final agent output following tool execution is returned

#### Scenario: Rejection resumes with feedback
- GIVEN a thread with status `AWAITING_APPROVAL`
- WHEN `POST /approve` is called with `approved: false` and `rejection_reason: "False alarm"`
- THEN status is `REJECTED_AND_RESUMED`
- AND the agent's acknowledgment and continued reasoning is returned

#### Scenario: Approve on unpaused thread returns 400
- GIVEN a thread with no pending approval
- WHEN `POST /approve` is called
- THEN the API returns HTTP status code 400 Bad Request
