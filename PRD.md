# PRD — FamilyVault AI

## Problem
Families deal with important documents (rent agreements, insurance
policies, loans) that are hard to understand, easy to lose track of, and
often need to be shared with an LLM to get help — which means sending
sensitive personal data to the cloud. There's no private, local way to
understand documents, remember key facts across them, and get reminded
before something expires.

## Solution
FamilyVault AI is a local-first document-understanding and family-memory
app. By default, everything — OCR, explanation, extraction, storage, and
Q&A — runs on the user's own machine via a local LLM (Qwen3 4B via
Ollama).
Nothing sensitive leaves the device unless the user explicitly approves an
action (e.g. adding a calendar reminder), or the operator deliberately
enables cloud-inference mode as a hardware fallback (see
`ARCHITECTURE.md` — Model configuration).

## Target track
ASYNC'26 — Sovereign AI track.

## MVP scope
Three document types only:
1. Rent agreements
2. Insurance documents
3. Loan documents

## Core features (must-have for demo)
1. **Upload & explain** — user uploads a PDF/image, system OCRs it, local
   LLM explains it in plain English (Hindi optional/stretch), and extracts
   structured fields (see `ARCHITECTURE.md` for schemas).
2. **Family memory** — extracted facts are stored locally and persist
   across sessions. Saved automatically when every field is extracted with
   confidence; the user is only asked to review/edit when a field is missing
   or ambiguous. Documents can be deleted.
3. **Cross-document Q&A** — user asks natural-language questions ("when
   does my father's car insurance expire?") and gets an answer with a
   source reference to the originating document.

## Stretch features (only if time allows, in this order)
1. Knowledge graph linking related documents/entities (father → car →
   insurance → expiry) shown visually.
2. Hindi explanation toggle.
3. Renewal/document checklists ("what do I need to renew this?").

## Deferred (explicitly out of this MVP build, may return later)
- Google Calendar reminder automation for upcoming renewals
  (user-approved, minimal OAuth scope). Not part of this build phase —
  design is kept in `ARCHITECTURE.md` for a future pass.

## Non-goals (explicitly out of scope for MVP)
- Supporting arbitrary/unlimited document types.
- Any action taken without explicit user confirmation.
- Cloud LLM usage as the default/production path — cloud is an explicit,
  visibly-flagged fallback only (see Model configuration in
  `ARCHITECTURE.md`), never silent.
- Multi-user accounts / sharing across families.

## Success criteria for the demo
- Upload a real (not synthetic) sample of each of the 3 document types and
  get a correct plain-language explanation + correctly extracted fields.
- Ask at least one cross-document question and get a correct, sourced
  answer.
- Show the local-only data flow clearly when running in local mode (no
  network calls to any LLM provider during document processing) — this is
  the core judge-facing differentiator. If cloud mode is used during the
  live demo due to hardware constraints, this must be disclosed directly
  and shown via a visible UI indicator, not silently swapped in.

## Judging narrative (Sovereign AI angle)
"Your family's most sensitive documents — rental contracts, insurance,
loans — never have to leave your device to be understood." Emphasize:
local LLM by default, local vector DB, local knowledge graph, that the
only optional external calls are (a) Calendar, opt-in and minimally
scoped, and (b) cloud inference, an explicit, visibly-flagged, one-line
config toggle that exists purely as a hackathon-hardware fallback — not
a design compromise.
