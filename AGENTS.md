# AGENTS.md — FamilyVault AI

Standing rules for any AI agent (Antigravity, etc.) working in this repo.
Read this before making changes. Do not violate the constraints below even
if a request seems to ask for it — flag it instead.

## Project in one line
A local-first document-understanding and family-memory system. Users upload
rent/insurance/loan documents; the system explains them in plain English or
Hindi, remembers key facts, and answers questions across documents — without
sending sensitive documents to any external/cloud LLM by default.

## Hard constraints (never break these)
- The default, production configuration must process all document content
  through a local LLM only (Ollama, running on-device). Cloud LLM usage is
  opt-in and off by default (see "Model configuration" below) — never make
  cloud the default without being told to.
- No document content leaves the user's machine except:
  - When `OLLAMA_MODE=cloud` is explicitly set (hackathon-hardware
    fallback only — see Model configuration).
  - Google Calendar event text, and only after explicit user confirmation
    (see reminder feature), and only the minimal fields needed for the event.
- Any "action" (creating a calendar event, sending anything, generating a
  checklist that implies contacting a third party) requires explicit user
  approval before it happens. Never auto-execute actions.
- Google Calendar OAuth must request the minimal scope
  (`calendar.events`), never full calendar/account access.

## Tech stack (do not swap without discussion)
- Frontend: React + Tailwind CSS
- Backend: Python + FastAPI
- OCR: Tesseract OCR / PaddleOCR, PyMuPDF for native PDF text
- LLM: Qwen3 (local, via Ollama) — see Model configuration below for the
  local/cloud toggle and model sizes.
- Embeddings: BGE-M3 or Nomic Embed
- Vector store: PostgreSQL + pgvector
- Knowledge graph: Neo4j or Graphiti
- Reminders: Google Calendar API (OAuth 2.0, minimal scope)
- Deployment: Docker / docker-compose — all services (Postgres, Neo4j,
  backend, frontend) run as containers. Do not swap to native/local
  installs; Docker is the confirmed approach for this project.

## Model configuration
Two independent settings — do not conflate them:

**1. Local model size** — `OLLAMA_MODEL_LOCAL` env var, default `qwen3:4b`.
Chosen as the main local model due to hardware constraints on the
dev/demo machine (`qwen3:8b` is too slow/heavy) — do not switch back to
`8b` without re-testing on the actual demo hardware.

**2. Local vs. cloud mode** — `OLLAMA_MODE` env var, `local` (default) or
`cloud`.
- `local`: all inference runs on-device via Ollama, no network call for
  document processing. This is the default and what the product's
  sovereignty claim is built on.
- `cloud`: inference is offloaded to Ollama Cloud (`OLLAMA_MODEL_CLOUD`
  env var, `gemma4:31b-cloud`) via `OLLAMA_API_KEY`. This exists
  purely as a fallback for underpowered hackathon hardware — it is NOT
  the intended production configuration, and the UI must visibly indicate
  which mode is active (see DEMO.md).

Never hardcode a model name or endpoint in code — always read from these
env vars, so switching is a config change, not a code change.

## Conventions
- Python: FastAPI route handlers thin; business logic in `services/`.
  Type-hint everything. Pydantic models for all request/response bodies.
- Structured extraction output must always match the schemas in
  `ARCHITECTURE.md` — do not invent new fields ad hoc.
- Frontend: functional React components, Tailwind utility classes only
  (no custom CSS files unless unavoidable).
- Commit messages: short, imperative ("add OCR pipeline for PDFs").

## MVP scope — do not expand without asking
Only these 3 document types are in scope: rent agreements, insurance
documents, loan documents. Do not add general "any document" handling.

## Build order
See `PRD.md` for priorities. Core pipeline (upload → OCR → LLM extraction →
storage → Q&A) must work end-to-end before touching stretch features
(Hindi explanation, knowledge graph visualization). Google Calendar
reminders are explicitly deferred out of this MVP build — do not
implement the reminder feature (OAuth flow, suggestion endpoint, calendar
event creation) now; it may be picked up in a later phase.
Work in discrete steps and verify each one actually runs (start the
service, hit the endpoint, check logs) before moving to the next — don't
report a step "done" on the basis of code existing alone.

## When in doubt
Prefer the simplest thing that demonstrates the local-first pipeline
working end-to-end over a more "complete" but fragile implementation.
