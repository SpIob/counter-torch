# Project Counter-Torch

On Earth, a flame rises because hot gas floats upward. Aboard a spacecraft nothing floats, and fire behaves differently. NASA has studied that difference in microgravity for years; the hard part is finding which of those experiments apply to the places crews will actually live.

Project Counter-Torch is a web dashboard built for the NASA Space Apps Challenge 2026 entry "Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data". It reads investigation records built from NASA's Physical Sciences Informatics (PSI) repository and shows where the evidence reaches, and where it stops, for habitats such as a Moon base. It does not say what is safe. It shows where the evidence ends.

> **AI disclosure.** This project was built with AI assistance. DeepSeek V4.1 Flash extracted the investigation records and NVIDIA Nemotron 3 Ultra 550B verified them, both through the Hermes agent framework. Claude wrote the backend and the web app in a Claude Code session and drafted the documents. I reviewed the verifier's changes, ruled on the disputed records and directed the design. The interface contains no AI-generated images, audio or video, and it uses no NASA logos or mission marks. Full details are in [ai-disclosure.md](ai-disclosure.md).

## What it does

The app has four views.

- **Coverage.** A scatter plot of 930 individual tests from four investigations (PSI-10, PSI-68, PSI-69 and PSI-159), plotted by oxygen and pressure using initial test conditions. The expected Moon-base atmosphere (30% oxygen or more at 10.2 psi or less) is drawn on top, and 66 of the 930 tests fall inside it. Scrolling reveals the gaps, written by code and not by a model, and a table of all 24 investigation records with a confidence level and a source for every value.
- **Ranker.** Scores every investigation for a chosen scenario, safety function and fuel type with a fixed formula: 35% conditions, 25% safety function, 20% fuel phase and 20% evidence quality. Each result expands to show its four parts and its sources. Partial-gravity scenarios are scored against microgravity data and labelled as bounding estimates.
- **Compare.** Shows only the fields where selected investigations differ, and suggests investigations that share hardware with the selection. An unknown value never counts as a match.
- **Ask.** Retrieves matching passages from the loaded records, shows them as cited cards, and refuses when too few passages match the question.

## Run it

You need Python 3 and Node. The commands below assume the repository root.

1. Create the Python environment and install the backend dependencies.

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r backend/requirements.txt
   ```

   Check: `.venv/bin/python3 -c "import fastapi, httpx, jsonschema"` prints nothing.

2. Build the test points, once, after the PSI tables are in `data/source/psi/tables/`.

   ```bash
   python3 scripts/psi_points.py
   ```

   Check: the script reports 930 points across 4 investigations.

3. Run the backend tests.

   ```bash
   cd backend && ../.venv/bin/python3 -m pytest -q
   ```

   Check: the last line reports 18 passed.

4. Start the backend. Offline mode needs no network and no key.

   ```bash
   LLM_MODE=offline ../.venv/bin/uvicorn app.main:app --port 8000
   ```

   Check: `curl http://localhost:8000/health` returns a JSON response.

5. In a second terminal, start the web app.

   ```bash
   cd web && npm install && npm run dev
   ```

   Check: http://localhost:5173 shows the Coverage view.

Live answers in the Ask view are optional. To enable them, set `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL` for any OpenAI-compatible endpoint. Without them, Ask returns the retrieved passages themselves. Only the Ask view can call a model; the ranking, the gaps and the zone counts never do. Never commit keys.

## How the data was built

1. **Script.** `scripts/psi_pull.py` reads PSI's public JSON API, and `scripts/psi_tables.py` downloads the small experimental-table CSVs. No PSI data files were downloaded, because they run to terabytes. `scripts/psi_table_summary.py` and `scripts/psi_apply_conditions.py` compute oxygen, pressure and airflow ranges from those tables and write them into 16 records, with no model involved.
2. **Extraction.** One DeepSeek V4.1 Flash agent per investigation read the local PSI records and wrote a structured record. Every non-null value carries a confidence level and at least one source; a value that no source supported stays null.
3. **Verification.** A different model, NVIDIA Nemotron 3 Ultra 550B, re-checked all 22 extracted records and changed 11 fields across 8 records. I ruled that a corrected or reset contradiction counts as verified, and that "disputed" applies only while a conflict remains.

The result is 24 records: 22 verified and 2 seed records (FM2 and LUCI) built from the challenge brief. Every record is validated against `schema/investigation.schema.json` with `scripts/validate.py`.

## Limits

- PSI holds no true partial-gravity combustion data. ACME E-FIELD Flames only mimics it with an electric field.
- The scatter shows initial test conditions for the four investigations whose tables list both oxygen and pressure. PSI-39 is left out because its pressure unit is missing.
- Five Ground investigations (PSI-60, 62, 115, 117 and 142) are not loaded, and some values remain unknown.
- The ranking measures how relevant and well sourced the evidence is. It is not a safety rating and does not predict flame spread.

The full list is in [data-limitations.md](data-limitations.md).

## Layout

```
AGENTS.md          rules every agent followed, plus the ranking and coverage contracts
schema/            investigation and habitat JSON schemas
api/openapi.yaml   API contract
backend/           FastAPI app (/investigations, /coverage, /points, /rank, /ask) and tests
web/               React, TypeScript and Vite app
data/              source files, seed fixtures, extracted and verified records, reports
scripts/           PSI pull, table summaries, point extraction, validation
prompts/           one brief per agent lane
hermes/            model routing and the staged rehearsal
docs/              submission text, AI disclosure, data limitations, form fields
```

## Models and agent lanes

| Lane | Model | Job |
|---|---|---|
| Ingestion | DeepSeek V4.1 Flash | Extract one record per investigation |
| Verification | NVIDIA Nemotron 3 Ultra 550B | Re-check each record against its sources |
| Backend, web app and documents | Claude | Written in a Claude Code session |

GLM 5.3 Flash was configured as a third route for documents and second opinions, but no work was assigned to it.

## Credits

The data comes from NASA's PSI repository (https://psi.nasa.gov) and NASA investigation pages; every record links to its sources. The web app uses React, Vite and TypeScript, and the backend uses FastAPI, httpx, jsonschema and pytest.

A tool that says where the evidence ends is more useful to a safety engineer than one that never admits it has.