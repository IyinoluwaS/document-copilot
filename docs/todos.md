# Build checklist

Order is backend-first, data-first. The risky part of this product is **trust**: can we extract filings with page numbers, retrieve the right passages, and force every claim to cite one? The frontend is a chat box and a citation panel. Work on the risky parts first and keep the UI thin until they work.

Each phase ends with a **Done when** line. Don't start the next phase until it's true.

---

## Phase 0: Accounts and local tooling

- [X] Install Python 3.12+, uv, Node 20+, pnpm (see README prerequisites)
- [X] Create Supabase project ([guides/supabase-setup.md](guides/supabase-setup.md)), enable `vector` extension availability, email auth only
- [X] Disable "Confirm email" for local dev (re-enable before pilot)
- [X] Create OpenAI API key, set a monthly spend limit
- [X] Run `uv run data/download.py`, confirm all 25 filings (5 tickers × 5 years) + `manifest.json`
- [X] Fix stale `AGENTS.md` references in README and `backend/` / `frontend/` CLAUDE.md files (renamed to `CLAUDE.md`)

**Done when:** you have Supabase URL/keys/direct DB URL, an OpenAI key, and the full corpus on disk.

## Phase 1: Backend skeleton + schema

- [X] `uv add` runtime + dev deps per [guides/backend-setup.md](guides/backend-setup.md)
- [X] `app/config.py`: pydantic-settings, fails fast on missing vars; fill `backend/.env` from `.env.example`
- [X] `app/main.py`: FastAPI app, CORS from `ALLOWED_ORIGINS`, `GET /health`
- [X] structlog setup
- [X] `app/database/models/` (one file per model): `users`, `chat_threads`, `chat_messages`, `message_citations`, `source_documents`, `document_chunks`
- [ ] Alembic init; `env.py` reads `settings.database_url` (direct/session connection, not the pooler)
- [ ] Initial migration, reviewed by hand, plus explicit ops: `create extension vector`, `vector(1536)` column, generated `tsvector` column, HNSW index, GIN indexes, RLS on user-owned tables
- [ ] `uv run alembic upgrade head` against Supabase; verify tables in dashboard
- [ ] pytest + ruff wired up; `pytest -m "not integration"` runs green (even if near-empty)

**Done when:** `uvicorn` serves `/health` and the full schema exists in Supabase, created only by Alembic.

## Phase 2: Ingestion (highest-risk phase)

- [ ] **Spike first:** open 2–3 filings and decide how to recover page numbers from EDGAR HTML (page-break CSS / page-number footers). The brief requires "filing + page" citations, so this blocks everything after it
- [ ] HTML → normalized Markdown extractor (keep tables readable; financial questions depend on them)
- [ ] Section detection (Item 1, 1A Risk Factors, 7 MD&A, 8 Financial Statements, …)
- [ ] Chunker: section-aware, records page, section, char offsets, token count
- [ ] Metadata from `manifest.json`: ticker, company, filing type, filing date, fiscal year, accession number, source URL
- [ ] Batch embeddings via OpenAI
- [ ] Idempotent writes to `source_documents` + `document_chunks` (re-running doesn't duplicate)
- [ ] Unit tests: extraction, page mapping, chunking (fixtures from small HTML snippets, no network)
- [ ] Run full ingest of all 25 filings; spot-check chunks against the original HTML pages

**Done when:** every chunk in the DB has correct ticker/year/section/page, and 10 random chunks match their source page.

## Phase 3: Retrieval + eval set

- [ ] Write an eval file from the 10 brief questions: for each, the expected filings/sections and a few must-retrieve passages
- [ ] `retrieval/queries.py`: pgvector similarity query, full-text query, with metadata filters (ticker, year)
- [ ] `retrieval/fusion.py`: Reciprocal Rank Fusion in Python
- [ ] `retrieval/retriever.py`: query → fused, deduped passages + neighbor-chunk lookup
- [ ] Unit tests for RRF and retriever (mocked queries)
- [ ] Eval script: recall@k per question; tune chunk size / k / filters until multi-year, multi-company questions (Q1, Q2, Q6, Q8) pull from every relevant filing

**Done when:** the eval script shows the right filings retrieved for all 10 questions.

## Phase 4: Agent + grounding

- [ ] `assistant/outputs.py`: `GroundedAnswer`, `Citation`, `SourcePassage`
- [ ] `assistant/instructions.md`: answer only from passages, cite every claim, say "not in the corpus" when unsupported, no investment advice
- [ ] `assistant/agent.py`: PydanticAI agent with tools `search_filings`, `read_chunk`, `read_surrounding_chunks`
- [ ] `grounding/validator.py`: every citation maps to a passage retrieved this turn; uncited answers are rejected unless it's an explicit "not enough evidence" reply
- [ ] Controlled failure path when validation fails (no polished unsupported answer)
- [ ] Unit tests: grounding contract (fabricated citation, missing citation, refusal allowed)
- [ ] Run the 10 questions end-to-end from a script; check Q10 refuses to infer beyond the filings; add one or two out-of-corpus questions (e.g. a non-covered company) that must refuse

**Done when:** a CLI script answers the 10 questions with valid citations, and out-of-corpus questions get refused.

## Phase 5: Auth + chat API

- [ ] `auth/dependencies.py`: verify bearer token via Supabase Auth, `get_current_user`
- [ ] Restrict sign-in to the Driftwood email domain (Supabase auth hook or backend check)
- [ ] Upsert `users` row on first authenticated request
- [ ] Thread endpoints: list, create, get messages (403 on other users' threads)
- [ ] `POST /chat/stream`: AI SDK-compatible streaming (text deltas, then citation/source parts, error events)
- [ ] `chat/orchestrator.py`: one turn end-to-end; persist user msg, assistant msg, citations, usage after success
- [ ] Error mapping: 401/403/404/422/502 per architecture doc
- [ ] Tests: auth dependency, thread ownership, message conversion

**Done when:** you can sign in with curl, open a thread, stream a cited answer, and see it persisted.

## Phase 6: Frontend

- [ ] Scaffold per [guides/frontend-setup.md](guides/frontend-setup.md): Vite + TS strict, Tailwind, shadcn, React Router, `@/*` alias
- [ ] `lib/env.ts`, `lib/supabase.ts`, `lib/http.ts`, `lib/api.ts` (bearer injection, typed `ApiError`, `isNetworkError`)
- [ ] Login page (email), auth guard, sign out
- [ ] Thread sidebar: past conversations, new chat
- [ ] Chat page with AI SDK `useChat` pointed at `/chat/stream`
- [ ] Inline citation markers → click opens source passage panel (company, filing, date, page, section, excerpt, link to EDGAR)
- [ ] Empty state with sample questions, streaming status, friendly error states (network vs HTTP)
- [ ] `pnpm tsc --noEmit` + `pnpm lint` clean; manual browser pass through all 10 questions

**Done when:** an analyst can sign in, ask a question, click a citation, verify the passage, and return to the thread later.

## Phase 7: Deploy (Railway)

- [ ] Backend service: Uvicorn start command, env vars, health check
- [ ] Frontend service: static Vite build, `VITE_*` vars at build time
- [ ] `ALLOWED_ORIGINS` set to the frontend URL; Supabase auth redirect URLs updated
- [ ] Re-enable email confirmation; confirm domain restriction works in prod
- [ ] Run migrations against prod DB; run ingest against prod DB
- [ ] Smoke test the 10 questions on the deployed app

**Done when:** the deployed app passes the same manual pass as local.

## Phase 8: Pilot readiness

- [ ] Log per-turn latency, token usage, retrieval hits, grounding failures (structlog)
- [ ] Feedback control on answers (thumbs up/down + note) to collect pilot evidence
- [ ] Short analyst guide: what's in the corpus, how to verify citations, what it won't do
- [ ] Decide on corpus expansion (brief says 10-Ks **and 10-Qs**, S&P 500, 2020–2025; sample is 10-Ks for 5 companies) and confirm ingest scales to it
- [ ] Onboard the 5 pilot analysts; plan how to measure the "≥3 hours saved per week" bar

**Done when:** the pilot group is live and you have a way to measure the definition of done.
