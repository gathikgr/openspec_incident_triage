# Delta for deployment

## ADDED Requirements

### Requirement: Dynamic Port Binding
The service SHALL bind to the port provided in the `$PORT` environment variable with a default fallback.

#### Scenario: Port from environment
- GIVEN `$PORT` is set to 10000
- WHEN the service starts
- THEN the web server binds to 0.0.0.0:10000

### Requirement: Secrets Isolation
Secrets SHALL come exclusively from environment variables, and the `.env` file SHALL NOT be tracked or committed to git.

#### Scenario: Verify git does not track .env
- GIVEN the repository git index
- WHEN checked for `.env`
- THEN `.env` is absent from tracked files

### Requirement: Lightweight Health Check
The application SHALL expose `GET /healthz` returning HTTP 200 OK without calling Gemini or database services.

#### Scenario: Health probe succeeds quickly
- GIVEN the web service is running
- WHEN `GET /healthz` is requested
- THEN it responds with status code 200 and `{"status": "ok"}` without external latency

### Requirement: Cold Start Resiliency
A paused HITL approval state SHALL survive a process restart or cold-start spin-down when backed by persistent storage.

#### Scenario: Resume across process recycles
- GIVEN a thread awaiting approval
- WHEN the application process restarts and loads state from the checkpointer
- THEN the thread can be approved and executed normally
