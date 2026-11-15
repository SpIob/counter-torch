# Backend worker: API, ranking and cited Q&A (route: deep)

Folder: `backend/` (write only here). Stack: Python 3.12+, FastAPI, uvicorn, jsonschema. Keep dependencies minimal and avoid extra services.
Read first: `AGENTS.md` (ranking and coverage contracts), `api/openapi.yaml`, `schema/investigation.schema.json`.

## Requirements
1. **Data loading.** Load `data/verified/*.json`; for any id without a verified file, fall back to `data/extracted/ID.json`, then to the seed in `data/fixtures/`. Log which source each id came from. Validate on load and skip invalid records with a warning.
2. **Endpoints** exactly as in `api/openapi.yaml`: `/health`, `/investigations`, `/investigations/{id}`, `/coverage`, `/rank`, `/ask`.
3. **/rank** implements the ranking contract in `AGENTS.md` deterministically, returns `components` and `unknown_dims`, and a `why` string. The `why` may be written by an LLM, but only from fields of that record; if no LLM is configured, build it from a template.
4. **/coverage** computes `gaps` and `facts` in code per the coverage contract. Include the fact from the brief that PSI has no true partial-gravity combustion data yet.
5. **/ask** is retrieval-augmented: index record fields and chunks of `data/source/*.txt`; simple TF-IDF or BM25 is enough. Answers must cite record ids and source URLs. If retrieval finds no support, return `coverage_gap: true`, say the data does not cover it, and do not guess.
6. **LLM access** through an OpenAI-compatible client configured only by environment variables `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Never hard-code keys or model ids. `LLM_MODE=offline` must serve deterministic template answers so the demo works without network; the response `mode` field says `live` or `offline`.
7. **CORS** allowed for the Vite dev origin.

## Tests
`backend/tests/` with pytest: ranking components for at least three hand-computed scenarios, gap detection for the Moon-base habitat, and `/ask` refusing an unsupported question.

## Done check
```
cd backend && python3 -m pytest -q          # all pass
uvicorn app.main:app --port 8000 &          # then:
curl -s localhost:8000/health               # {"status":"ok"}
curl -s localhost:8000/coverage | head -c 300
```
Report the pytest summary line and the first 300 characters of `/coverage`.
