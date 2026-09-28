# DEMO.md — FamilyVault AI Demo Script

This is the exact flow to rehearse and the minimum bar for "demo ready."
If something here doesn't work reliably, it doesn't go in the live demo.

## Pre-demo setup checklist
- [ ] Ollama running locally with Qwen3 4B loaded (test inference latency
      beforehand — 4B is the main model for this build due to hardware
      constraints; 8B is not used)
- [ ] Decide `OLLAMA_MODE` (local vs. cloud) in advance based on real
      testing on the demo machine — not decided live. Default to `local`
      unless hardware genuinely can't keep up.
- [ ] If `OLLAMA_MODE=cloud`: `OLLAMA_API_KEY` set, `ollama signin`
      already done, `gemma4:31b-cloud` pulled/confirmed reachable, and the
      frontend's mode indicator badge tested to confirm it shows "Cloud"
      correctly
- [ ] Postgres + pgvector running, schema migrated
- [ ] Knowledge graph store running (or hardcoded relationships loaded)
- [ ] 3 real sample documents ready: one rent agreement, one insurance
      policy, one loan document (scanned/photographed, not clean synthetic
      text — test OCR on realistic input beforehand)
- [ ] If running in local mode: confirm no network calls are made during
      document processing (screen-recordable proof for the "sovereign AI"
      claim)
- [ ] Calendar reminders are deferred out of this MVP build — no
      checklist item needed for this demo phase

## Pre-demo machine checklist (if demoing on a different laptop than dev)
Do this days before the hackathon, not the night before — Ollama model
downloads and first-time OCR installs are slow on venue wifi.
- [ ] Docker + docker-compose installed and `docker-compose up` tested
      end-to-end on the actual demo machine
- [ ] Ollama installed on the demo machine (separate from Docker — not
      auto-transferred by copying the repo)
- [ ] `qwen3:4b` pulled on the demo machine (`ollama pull qwen3:4b`) —
      this is the main local model for this build
- [ ] `OLLAMA_MODEL_LOCAL` env var set to `qwen3:4b`
- [ ] If cloud fallback might be needed: `OLLAMA_API_KEY` set and
      `OLLAMA_MODEL_CLOUD=gemma4:31b-cloud` confirmed reachable, tested
      once on this machine
- [ ] Tesseract OCR present (confirm it's in the Docker image, not just
      installed on the original dev machine)
- [ ] `.env` file copied over (it's gitignored, won't transfer via git)
- [ ] Full demo script (below) run at least once, start to finish, on
      this exact machine before judging

## Script

1. **Intro (30 sec)**
   "FamilyVault AI helps you understand and remember important family
   documents — rent, insurance, loans — without ever sending them to the
   cloud. Everything you're about to see runs locally."
   (If running in cloud mode for this demo, adjust: "Our default
   configuration runs entirely locally — for today's demo on this
   hardware we've enabled Ollama Cloud purely for inference speed. It's a
   single config flag, not an architecture change." Point to the mode
   indicator badge in the UI.)

2. **Upload & explain (rent agreement)**
   - Upload the sample rent agreement.
   - Show OCR extracting text, then the LLM explaining it in plain
     English: monthly rent, deposit, expiry, notice period.
   - If in local mode, point out: "This request never left the machine —
     it went to Qwen3 running locally via Ollama." Point to the mode
     indicator badge showing "Local."

3. **Auto-save (or review if uncertain)**
   - If every field was read confidently, show the "Saved automatically"
     summary — nothing for the user to fill in.
   - If a field couldn't be read, show the review form with just that
     field highlighted; the user fills it in and saves to local memory.

4. **Second document (insurance)**
   - Upload insurance policy for the same family's car.
   - Show extraction + save again.

5. **Cross-document Q&A**
   - Ask: "When does my father's car insurance expire?"
   - Show the answer with a source reference back to the uploaded
     document.
   - Ask a second question spanning both documents if the knowledge graph
     is working: "What documents are related to my car?"

6. **Knowledge graph (if working)**
   - Show the visual graph linking father → car → insurance → expiry.

7. **Close (20 sec)**
   "Local OCR, local LLM by default, local database, local knowledge
   graph — your family's most sensitive documents stay yours."

## Fallback plan
If live inference is too slow or flaky during judging, have a
pre-recorded screen capture of the exact flow above as backup, and
narrate live over static screenshots if necessary. Never let the demo
stall in silence.
