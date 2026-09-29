# Proposal: Add Render Deployment

## Why
Enable zero-cost hosting of the autonomous incident triage agent on Render's free tier with automated blueprint provisioning, lightweight health monitoring, and persistent state survivability across spin-downs.

## What Changes
- Add `render.yaml` Infrastructure as Code blueprint for Render Web Service.
- Add `GET /healthz` endpoint in `app.py` returning immediate 200 OK for platform health probes without invoking external LLMs or database queries.
- Add `README.md` with deployment instructions and cold-start documentation.
- Add unit tests verifying `GET /healthz` and confirming `.env` remains untracked.

## Capabilities Affected
- `deployment` (ADDED)

## Rollback Note
Remove `render.yaml` and `/healthz` route.
