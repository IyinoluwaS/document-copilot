# Backend

FastAPI service for Document Copilot. Conventions live in [CLAUDE.md](CLAUDE.md); first-time setup in [../docs/guides/backend-setup.md](../docs/guides/backend-setup.md).

All commands run from `backend/`.

## Setup

```bash
uv sync                  # install deps into .venv
cp .env.example .env     # then fill in real values
```

The app refuses to start if a required variable is missing or `.env` contains an unknown one. Config is read only through `app/config.py`.

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- Health check: http://localhost:8000/health
- Interactive API docs: http://localhost:8000/docs

## Database migrations

Alembic owns the schema. Never change tables by hand in the Supabase dashboard.

```bash
uv run alembic revision --autogenerate -m "describe change"   # after editing app/database/models/
uv run alembic upgrade head --sql                             # print the SQL without running it
uv run alembic upgrade head                                   # apply pending migrations
uv run alembic current                                        # show the applied revision
uv run alembic check                                          # fail if models and DB have drifted
```

Always read a generated migration before applying it. Extensions, RLS policies, and FKs into Supabase's `auth` schema are written by hand (see the initial migration).

## Dependencies

```bash
uv add <package>         # runtime dep (justify it in the commit message, see ../CLAUDE.md)
uv add --dev <package>   # dev-only dep
```

Don't edit `uv.lock` by hand. Commit it alongside `pyproject.toml`.

## Lint and test

```bash
uv run ruff check .
uv run ruff format .
uv run pytest -m "not integration"
```
