# VitalAI Backend: Phase One API

FastAPI backend for administrative intake, consent, triage, and routing.
Aligned with locked architecture decisions: async SQLAlchemy + Postgres, JWT auth + RBAC,
append-only audit log with DB-level enforcement, LLM provider abstraction for
Ollama (dev) / Bedrock (prod) swap.

## Quick start (Docker Compose — recommended)

```bash
cd backend
cp .env.example .env
# Generate a real secret — never leave the placeholder in production:
python -c "import secrets; print(secrets.token_urlsafe())"
# Paste the output as JWT_SECRET_KEY in .env, then:
docker compose up --build
docker compose exec api alembic upgrade head
```

API at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

Pull the dev model into Ollama once:

```bash
docker compose exec ollama ollama pull gemma2:9b
```

## Quick start (local)

Needs Python 3.13 and a running Postgres.

```bash
pip install -r requirements.txt
cp .env.example .env          # set JWT_SECRET_KEY and point DATABASE_URL at your local Postgres
# Generate a real secret: python -c "import secrets; print(secrets.token_urlsafe())"
alembic upgrade head
uvicorn app.main:app --reload
```

## Project structure

```
backend/
├── docker-compose.yml          FastAPI + Postgres + Ollama
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── .env.example
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py    initial schema + append-only trigger
└── app/
    ├── main.py                 FastAPI app
    ├── config.py               pydantic-settings, env-driven
    ├── database.py             async engine + session factory
    ├── models/                 SQLAlchemy ORM (users, case, consent, triage, routing, audit)
    ├── schemas/                Pydantic API contracts (request/response shapes)
    ├── auth/                   JWT + RBAC (security, dependencies)
    ├── llm/                    provider abstraction - get_llm() switches by env
    ├── routes/                 API handlers (health, auth, intake, consent, triage, routing)
    └── services/               Business logic (intake, consent, triage, routing, audit)
```

## API endpoints

Auth required on everything under `/api/v1/*` except `POST /api/v1/auth/register` and
`POST /api/v1/auth/login`.

| Method | Path                                | Auth | Roles                    | Description                       |
|--------|-------------------------------------|------|--------------------------|-----------------------------------|
| GET    | `/health`                           | —    | —                        | Health check                      |
| POST   | `/api/v1/auth/register`             | —    | —                        | Register user                     |
| POST   | `/api/v1/auth/login`                | —    | —                        | Get JWT                           |
| GET    | `/api/v1/auth/me`                   | ✓    | any                      | Current user                      |
| POST   | `/api/v1/intake`                    | ✓    | any                      | Create intake case                |
| GET    | `/api/v1/intake/{id}`               | ✓    | any                      | Get intake case                   |
| PATCH  | `/api/v1/intake/{id}/status`        | ✓    | ops_manager, admin       | Update intake status              |
| POST   | `/api/v1/consent`                   | ✓    | any                      | Create consent record             |
| GET    | `/api/v1/consent/by-case/{case_id}` | ✓    | any                      | Get consent for case              |
| POST   | `/api/v1/consent/{id}/capture`      | ✓    | any                      | Capture consent (pending → ✓)     |
| POST   | `/api/v1/consent/{id}/withdraw`     | ✓    | any                      | Withdraw consent                  |
| POST   | `/api/v1/triage`                    | ✓    | any                      | Classify case urgency             |
| POST   | `/api/v1/routing`                   | ✓    | any                      | Create routing decision           |
| GET    | `/api/v1/routing/by-case/{case_id}` | ✓    | any                      | Get latest routing decision       |

## LLM provider switch

Set `LLM_PROVIDER` in `.env`:

- `ollama`: dev. Uses `LLM_MODEL` (default `gemma2:9b`) via `OLLAMA_BASE_URL`.
- `bedrock`: staging/prod. Uses `BEDROCK_MODEL_ID` (default Claude Haiku) in `AWS_REGION`.

Nothing else in the codebase imports Ollama or Bedrock directly. Migration is a config change but not a code change.

## Append-only audit log

`audit_events` has database-level triggers that block `UPDATE` and `DELETE`. Any attempt
to modify a row raises `audit_events is append-only`. This is what backs the
"tamper-evident artefact" claim in the design doc — never described as blockchain.

## Constraints

- No clinical decision support, no diagnosis, no treatment recommendations.
- Every state changing operation writes to the audit log with the authenticated actor.
