# MailMind

MailMind is an early-stage Python prototype exploring an email and calendar productivity assistant. The repository currently contains a FastAPI local demo, fixture-backed Gmail and Calendar managers, and initial LangGraph/RAG/memory scaffolding. It is **not** a production-ready agent: there is no frontend, OAuth flow, persistent database integration, live Google API wiring, or working approval/resume flow.

## What works today

- FastAPI health, chat-stream, and memory endpoints.
- A Server-Sent Events (SSE) chat response with explicitly labeled sample citations.
- Local fixture data for Gmail and Calendar so the API can be explored without credentials.
- A fail-closed approval endpoint: it returns `501 Not Implemented` and does not claim that an action was executed.
- Unit tests for the current API behavior and validation boundaries.

The chat response is a demo placeholder; it does not interpret the request with an LLM. Fixture records are not real user data. Memory reads return no preferences until persistence is implemented.

## Run locally

Requirements: Python 3.11+ and pip. Docker is optional; the API demo does not connect to PostgreSQL or Redis.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
uvicorn backend.api.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for the interactive API docs or `http://localhost:8000/health` for the health check. No API keys are needed for the local demo. The `.env.example` file is a configuration sketch; the current app does not load it.

To try the streaming endpoint:

```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Show me my recent mail and upcoming events"}'
```

The stream ends with `data: [DONE]`. The response identifies all citations as sample data.

## Tests

```bash
pytest -q
```

## Optional infrastructure

`docker compose up -d` starts PostgreSQL with pgvector and Redis. They are currently standalone development services: the API has no database schema, migrations, connection lifecycle, or Redis integration. Set `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in the environment before starting the services if you need non-default local credentials. Do not use the example credentials outside a local development environment.

## Repository map

```text
.
├── backend/
│   ├── agents/       # Initial LangGraph state, planner, and graph scaffold
│   ├── api/          # FastAPI local demo API
│   ├── memory/       # Memory model and extraction scaffold
│   ├── rag/          # Email chunking and RAG scaffold
│   └── tools/        # Gmail and Calendar wrappers with local fixtures
├── docker-compose.yml
├── PRD.md            # Product requirements / target-state proposal
└── ARCHITECTURE.md   # Target architecture proposal
```

## Current limitations and next steps

The documents in `PRD.md` and `ARCHITECTURE.md` describe the intended target system, not completed functionality. The most important implementation work remaining is:

1. Add Google OAuth and per-user credential handling; wire live Gmail and Calendar clients.
2. Replace the placeholder chat response with a configured, tested agent graph and make SSE stream actual graph events.
3. Implement persistent memory and email ingestion/search with database migrations and user isolation.
4. Add LangGraph checkpointing and a verified approval/resume flow before enabling external actions.
5. Build the frontend, then add integration tests and deployment configuration.

Until those safeguards are implemented, this prototype must not be used with real mailboxes or for real-world actions.
