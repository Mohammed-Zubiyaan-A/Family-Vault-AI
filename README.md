<p align="center"><img src="docs/logo.png" alt="FamilyVault AI — Understand · Remember · Protect" width="320" /></p>

# FamilyVault AI

A private, local-first document-understanding and family-memory system.
Upload rent agreements, insurance documents, or loan documents — get plain
-language explanations, persistent memory of key facts, and cross-document
Q&A, without sending sensitive data to the cloud by default.

Built for ASYNC'26 — Sovereign AI track.

## Docs
- `PRD.md` — what we're building and why, MVP scope, success criteria
- `ARCHITECTURE.md` — tech stack, pipeline, RAG/memory/knowledge-graph
  design, data schemas, model configuration, frontend screens + API
- `AGENTS.md` — rules for AI coding agents (Antigravity) working in this
  repo
- `DEMO.md` — the exact demo script + pre-demo checklists

## Quick start
```bash
# 1. Start Ollama and pull the local model
ollama pull qwen3:4b   # main local model for this build (hardware-constrained)

# 2. Start the full stack (Postgres+pgvector, Neo4j, backend, frontend)
docker-compose up -d

# 3. Backend (if running outside Docker for local dev)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 4. Frontend
cd frontend
npm install
npm run dev
```

## Environment variables
```
# Local model
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_LOCAL=qwen3:4b     # main model — chosen for this build's hardware constraints

# Local vs. cloud toggle (see ARCHITECTURE.md — Model configuration)
OLLAMA_MODE=local               # "local" (default) or "cloud"
OLLAMA_MODEL_CLOUD=gemma4:31b-cloud   # only used when OLLAMA_MODE=cloud
OLLAMA_API_KEY=                 # only needed when OLLAMA_MODE=cloud

# NOTE: after changing this file (e.g. switching OLLAMA_MODE), a plain
# `docker-compose up -d` doesn't reliably pick up the change. Force it:
#   docker-compose stop backend && docker-compose rm -f backend && docker-compose up -d backend

# Data stores
DATABASE_URL=postgresql://user:pass@localhost:5432/familyvault
GRAPH_DB_URL=bolt://localhost:7687

# Calendar reminders (deferred — not used in this MVP build)
GOOGLE_CALENDAR_CLIENT_ID=
GOOGLE_CALENDAR_CLIENT_SECRET=
```

## Transferring to another machine
Code/infra (this repo + Docker) is fully portable via Git or a zipped
folder. The one thing that does NOT transfer with the repo is Ollama and
the model weights — set these up independently on any machine that will
run the demo, ideally days beforehand:
```bash
# On the new machine:
1. Install Ollama: https://ollama.com/download
2. ollama pull qwen3:4b
3. git clone <this-repo> && cd familyvault-ai
4. cp .env.example .env        # .env is gitignored — copy/recreate it
5. docker-compose up -d
```
If venue wifi is a concern, the model weights can instead be copied via
USB from `~/.ollama/models` (Mac/Linux) or `%USERPROFILE%\.ollama\models`
(Windows) rather than re-pulled — test this once beforehand, paths can be
OS-dependent. See `DEMO.md` for the full pre-demo-machine checklist.

## Key decisions
- **Qwen3 4B via local Ollama by default, not a cloud LLM** — core to the
  Sovereign AI pitch; no document content is sent to an external API in
  the default configuration. 4B was chosen (over 8B) due to hardware
  constraints on the dev/demo machine.
- **Ollama Cloud (`OLLAMA_MODE=cloud`) exists only as an explicit,
  visibly-flagged hardware fallback** — never the silent default. See
  `ARCHITECTURE.md` — Model configuration.
- **3 document types only for MVP** (rent, insurance, loan) — kept scope
  tight for a 24-hour build instead of general document support.
- **All services run in Docker** — Postgres+pgvector, Neo4j, backend, and
  frontend are containerized for consistent setup across team laptops.
- **Hardcoded knowledge-graph relationship types for the demo** — a full
  general-purpose graph schema wasn't worth the build time given the
  timeline; can generalize post-hackathon.
- **Calendar reminders are opt-in and minimally scoped** (`calendar.events`
  only) — keeps the "your data stays yours" story consistent even for the
  one feature that talks to an external API.
- **Auto-save when confident, ask only when uncertain** — if every schema
  field is extracted, the document is saved without interrupting the user;
  the review form appears only for missing/ambiguous fields.
- **Every generated answer must cite its source document** — trust and
  verifiability matter as much as correctness for this use case.
- **Google Calendar reminders are deferred out of this MVP build** — not
  necessary for the working demo; the design stays in `ARCHITECTURE.md`
  to pick up in a later phase.

## Status
MVP in progress for ASYNC'26 build phase (Sept 30 – Oct 1).
