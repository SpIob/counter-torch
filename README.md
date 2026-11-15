# Project Counter-Torch starter kit

Solo-builder kit for the NASA Space Apps challenge "Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data". It is the contract and the agent briefs, not the app: schema, seed data, API contract, one prompt per agent lane, and Hermes routing for three NVIDIA-hosted models.

## Concept
A dashboard built around one idea: scenario-first, evidence-linked. Core features: a **Coverage Map** (where PSI data reaches vs the habitats crews will use, with computed gaps), a **Scenario Ranker** (explainable relevance scores), and **cited Q&A** that refuses when the data does not cover a question. Compare mode and a hardware lineage graph come next.

## Layout
```
AGENTS.md                      rules every agent follows, ranking + coverage contracts
schema/                        investigation.schema.json, habitats.schema.json (v0.1.0)
data/source/challenge-brief.txt   the brief, used as a local authoritative source
data/fixtures/                 investigations.seed.json (20 records), habitats.json (6)
data/extracted|verified|reports/  agent outputs (empty at start)
api/openapi.yaml               /investigations /coverage /rank /ask contract
prompts/                       00 orchestrator, 10 ingestion, 20 verifier, 30-32 frontend, 40 backend, 50 writer
hermes/                        delegation.snippet.yaml (routes), DRYRUN.md (staged rehearsal)
scripts/                       validate.py, plant_error.py
web/ backend/                  empty; agents build here
```

## Model routing (via the Hermes advanced-delegation plugin)
| Route | Model | Used for |
|---|---|---|
| `fast` | deepseek-v4.1-flash | ingestion extraction, routine UI components |
| `deep` | nemotron-3-ultra-550b-a55b | verification, backend and RAG, hard bugs |
| `alt` | glm-5-3-flash | second opinions, docs and copy |

The verifier always runs on a different route from the extractor.

## Do this before Nov 13
1. Run `hermes/DRYRUN.md` end to end (about an hour). It rehearses fan-out, validation and the independent verifier on 3 investigations plus a planted error.
2. Scaffold the app shells so Nov 14 starts with building, not setup:
   ```bash
   npm create vite@latest web -- --template react-ts && (cd web && npm install && npm run build)
   python3 -m venv .venv && . .venv/bin/activate && pip install fastapi uvicorn jsonschema pytest
   npx openapi-typescript api/openapi.yaml -o web/src/api/types.ts
   git init && git add -A && git commit -m "starter kit"
   ```
   Check: `npm run build` exits 0 and `web/src/api/types.ts` exists.
3. Read the official Space Apps rules on pre-built code and on disclosing AI use, and adjust what you commit before the event if needed.

## Known unknowns (not verified here)
- The exact Hermes provider name and model ids for your NVIDIA key; the snippet marks them to confirm.
- PSI's real file formats and access method for combustion data (Nov 13 and day-1 triage).
- Your API rate limits under 6 parallel workers (the dry run tests this).
- The seed records contain only facts from the brief and NASA's PSI list; everything else is `unknown` until extraction.

## Update log
- Nov 14 (patch 1): project renamed Project Counter-Torch. Added `data/source/resources.md`, the video transcript, and `psi-notes.md`. Added `scripts/psi_recon.py` (checks NASA's public S3 bucket). Seed grew to 23 records (`sofie`, `flare`, `bass-m`). Schema allows `status: active` and `in_psi: null`. AGENTS.md has the PSI facts and a Coverage Map fallback. If you generated `web/src/api/types.ts` already, regenerate it: `npx openapi-typescript api/openapi.yaml -o web/src/api/types.ts`.
- Nov 14 patch 2: PSI JSON API found. Added `scripts/psi_pull.py`, `data/source/psi-map.json`, optional schema fields `psi_accession` and `project_type`; ingestion and verifier prompts now read the local PSI records (`data/source/psi/`); AGENTS.md data reality rewritten; Hermes snippet uses the confirmed model ids.
- Nov 14 patch 3 (from the dry run): `scripts/psi_tables.py` (experimental-table CSVs) and `scripts/psi_fill.py` (PSI fields set by script); verifier scope tightened (no filling nulls, real timestamps); orchestrator and prompts match this Hermes (no `toolsets` argument, background delegation, no angle-bracket markers, venv python); DAFT mapped to PSI-47.
- Nov 14 patch 4: PSI table download via the site's download endpoint (`psi_tables.py`), `psi_table_summary.py` (O2, pressure, flow ranges from NASA's tables, drops impossible values, separates initial from final columns), `psi_apply_conditions.py` (writes them into records with the CSV as source). Coverage Map decision: matrix headline, scatter of real test points as second panel (only 5 investigations have both O2 and pressure).
- Nov 14 build 1: backend (FastAPI: /investigations, /coverage, /points, /rank, /ask; deterministic ranking and gaps, BM25 Q&A that refuses without support; `LLM_MODE=offline` works without network) and web app (Coverage matrix + test-point scatter, Scenario ranker, Compare + lineage, Ask). `scripts/psi_points.py` extracts per-test O2/pressure points.

## Run the app
```bash
python3 scripts/psi_points.py                       # once, after psi_tables.py
.venv/bin/pip install -r backend/requirements.txt
cd backend && .venv/bin/python3 -m pytest -q        # or: ../.venv/bin/python3 -m pytest -q
LLM_MODE=offline ../.venv/bin/uvicorn app.main:app --port 8000
# second terminal
cd web && npm install && npm run dev                # http://localhost:5173
```
Optional live answers: set `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (any OpenAI-compatible endpoint). Never commit keys.

