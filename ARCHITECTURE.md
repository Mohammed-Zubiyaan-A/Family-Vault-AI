# ARCHITECTURE — FamilyVault AI

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React.js + Tailwind CSS | Upload UI, chat UI |
| Backend | Python + FastAPI | API, orchestration |
| OCR | Tesseract OCR / PaddleOCR | Extract text from scans/images |
| PDF parsing | PyMuPDF | Extract text from digital PDFs |
| LLM | Qwen3 4B (local, default), Ollama Cloud gemma4:31b-cloud (fallback) | Explanation, extraction, Q&A reasoning |
| LLM runtime | Ollama | Run the LLM locally, or proxy to Ollama Cloud |
| Embeddings | BGE-M3 / Nomic Embed | Chunk vectors for semantic search |
| Vector DB | PostgreSQL + pgvector | Semantic retrieval (RAG) |
| Knowledge graph | Neo4j / Graphiti | Entity relationships |
| Reminders | Google Calendar API | Deferred — not in MVP build (see PRD.md) |
| Deployment | Docker / docker-compose | All services run as containers |

## End-to-end pipeline

```
Upload rent, insurance, or loan document
              ↓
      OCR / PDF text extraction
              ↓
         Text preprocessing (clean + chunk)
              ↓
          Local LLM analysis (Qwen3 via Ollama, or Ollama Cloud if enabled)
              ↓
   Simple English or Hindi explanation
              ↓
  Extract people, dates, amounts, clauses → structured JSON
              ↓
   Auto-save if every field was extracted; otherwise the user
   reviews/edits only the uncertain fields
              ↓
    Save to local DB (facts) + pgvector (chunks)
              ↓
   Link related entities in knowledge graph
              ↓
      Ask questions across documents (RAG + graph)
              ↓
  Generate alerts / checklists / reminder suggestions
              ↓
        User approval before any action
```

## Model configuration

Two independent settings, both read from environment variables — never
hardcode a model name or endpoint in code.

**1. Local model size** — `OLLAMA_MODEL_LOCAL`, default `qwen3:4b`.
Chosen as the main local model due to hardware constraints on the
dev/demo machine — `qwen3:8b` is too heavy/slow for reliable end-to-end
inference on this hardware. Re-test on the actual demo machine if this
assumption changes.

**2. Local vs. cloud mode** — `OLLAMA_MODE`, `local` (default) or `cloud`.
- `local`: requests go to the local Ollama instance (`OLLAMA_HOST`,
  default `http://localhost:11434`). No network call for document
  content. This is the default and the configuration the product's
  sovereignty claim is built on.
- `cloud`: requests are routed to Ollama Cloud
  (`host=https://ollama.com`, `OLLAMA_API_KEY` required) using
  `OLLAMA_MODEL_CLOUD` (`gemma4:31b-cloud`). This exists ONLY as a
  fallback for hackathon hardware that can't run local inference fast
  enough. It is opt-in, must be a deliberate config change, and the
  frontend must show a visible indicator of which mode is active (see
  `DEMO.md`).

```python
# services/llm_client.py — conceptual shape, not literal code
if settings.OLLAMA_MODE == "cloud":
    client = Client(host="https://ollama.com",
                     headers={"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"})
    model = settings.OLLAMA_MODEL_CLOUD
else:
    client = Client(host=settings.OLLAMA_HOST)
    model = settings.OLLAMA_MODEL_LOCAL
```

## RAG (retrieval)
- Document text is chunked (target ~300–500 tokens/chunk) after cleaning.
- Each chunk is embedded (BGE-M3 or Nomic) and stored in pgvector with
  metadata: `document_id`, `document_type`, `chunk_index`.
- On a question, embed the query, retrieve top-k chunks by cosine
  similarity, pass them + the question to the configured LLM to generate
  the answer.
- Every answer must include a reference to the source document
  (`document_id` / filename) so the user can verify it.

## Memory (persistent facts)
Separate from RAG chunks: a structured "facts" table holds confirmed
extracted fields per document (see schemas below). A document is saved
automatically when every schema field was extracted; if any field is
missing or ambiguous, it is held for the user to review first. This is
what powers fast lookups like "what's expiring soon" without needing to
re-run retrieval over raw text.

## Knowledge graph
Connects entities across documents so the system can answer relational
questions instead of treating every document as isolated.

Example — insurance:
```
Father
  │
  └── owns → Hyundai i20
                  │
                  └── protected by → Insurance Policy
                                           │
                                           └── expires on → 15 Nov 2026
```

Example — rent:
```
Tenant
  │
  └── rents → House
                │
                └── covered by → Rent Agreement
                                      │
                                      ├── expires on → 30 Jun 2027
                                      └── requires → 2-month notice
```

For the hackathon MVP: hardcode the relationship types (owns, protected
by, expires on, rents, covered by, requires) rather than building a
general-purpose graph schema. Extend only if time allows.

## Structured extraction schemas

### Rent agreement
```json
{
  "document_type": "rent_agreement",
  "tenant": "string",
  "owner": "string",
  "monthly_rent": "number",
  "security_deposit": "number",
  "agreement_expiry": "YYYY-MM-DD",
  "notice_period_months": "number"
}
```

### Insurance document
```json
{
  "document_type": "insurance",
  "policy_holder": "string",
  "insured_asset": "string",
  "provider": "string",
  "coverage_amount": "number",
  "expiry_date": "YYYY-MM-DD"
}
```

### Loan document
```json
{
  "document_type": "loan_agreement",
  "borrower": "string",
  "loan_amount": "number",
  "interest_rate_pct": "number",
  "repayment_period_months": "number",
  "next_important_date": "YYYY-MM-DD"
}
```

## Reminder automation (deferred — not in MVP build)
Not part of the current MVP build. Kept here as the design for a later
phase; do not implement the OAuth flow, suggestion endpoint, or event
creation as part of this build.
```
Extracted expiry date
        ↓
Reminder offset rule (e.g. remind 15–30 days before)
        ↓
User approval ("Add reminder to Google Calendar?")
        ↓
Google Calendar API creates event
  (title, date, description from structured fields)
```
OAuth scope: `calendar.events` only. Token stored locally, not on any
server.

## Frontend

Derived directly from the flow in `DEMO.md` — build only these screens.

### Screens
1. **Upload** — drag/drop or file picker for PDF/image; shows OCR + LLM
   processing status; displays the plain-language explanation once ready.
2. **Confirm extraction** — shown ONLY when extraction was incomplete or
   ambiguous (a schema field came back empty). Highlights the uncertain
   fields in an editable form; user confirms/edits before saving. If every
   field was extracted, the document is auto-saved and the user just sees a
   "Saved automatically" summary (with an optional Edit action).
3. **Document list** — shows all documents (by type, with key dates and
   a status badge: failed / processing / needs review) so the user can see
   what's stored. Each card expands to the full explanation and fields, lets
   the user review an unconfirmed document later, and **delete** a document
   (removes its facts, embeddings and uploaded file).
4. **Chat / Q&A** — simple chat interface; user asks a question, gets an
   answer with a clickable source reference back to the originating
   document.
5. **Knowledge graph view** (stretch) — visual graph of linked entities
   (person → asset → document → date), e.g. via a lightweight graph
   library (react-flow or vis.js) rather than building custom rendering.
6. **Reminder confirmation modal** (deferred — not in MVP build) — shown
   when a suggested action (e.g. "add Calendar reminder") appears;
   requires explicit Approve/Dismiss before anything is created. Not
   built in this phase.
7. **Mode indicator** — small persistent badge showing "Running: Local"
   or "Running: Cloud" based on `OLLAMA_MODE`. Not optional if cloud mode
   is ever used in a demo — see `DEMO.md`.

### API contract (backend exposes, frontend consumes)
```
POST   /documents/upload
  → multipart file upload
  → returns { document_id, status: "processing" }

GET    /documents/{document_id}/status
  → returns { status: "processing" | "ready" | "error", stage?, explanation?,
              extracted_fields?, confirmed: bool, error_message? }
  → confirmed=true means every field was extracted and saved automatically

POST   /documents/{document_id}/confirm
  → body: confirmed/edited structured fields (upsert — also used to edit an
    auto-saved document)
  → returns { document_id, saved: true }

GET    /documents
  → returns list of documents (id, type, status, confirmed, key dates, summary)

GET    /documents/{document_id}
  → returns full detail: explanation, fields, confirmed, status, error_message?

DELETE /documents/{document_id}
  → removes the document, its facts, its embeddings and the uploaded file
  → returns { document_id, deleted: true }

POST   /qa/ask
  → body: { question: string }
  → returns { answer: string, sources: [{ document_id, filename }] }

GET    /graph/{document_id}          (stretch)
  → returns linked entities/edges for visualization

POST   /reminders/suggest/{document_id}   (deferred — not in MVP build)
  → returns { suggestion: string, proposed_event: {...} }

POST   /reminders/confirm/{document_id}   (deferred — not in MVP build)
  → body: { approved: true }
  → returns { calendar_event_id }

GET    /system/mode
  → returns { ollama_mode: "local" | "cloud", model: string }
  (powers the frontend mode indicator badge)
```

State management: keep it simple — React Query (or plain `fetch` + local
state) for server state, no global store needed for MVP scope.

## Audit trail
Every stored fact, generated answer, and suggested action logs: which
document was used, what was extracted, what was generated, whether the
user approved it, and which `OLLAMA_MODE` was active for that request.
Auto-saved extractions are logged with `auto: true` and `user_approved:
false`; deletions are logged as `delete_document`.
Minimal table is fine for MVP (append-only log).
