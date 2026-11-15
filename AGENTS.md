# Project Counter-Torch: rules for every agent

Project Counter-Torch (use this exact name in the UI header, docs and submission; the repo folder is still `flame-atlas`): a web dashboard for NASA Space Apps "Flame in Freefall" that ranks, compares and interprets microgravity combustion investigations from NASA's PSI database for fire safety in crewed habitats.
Authoritative local source: `data/source/challenge-brief.txt`. Read this file and `schema/investigation.schema.json` before doing anything.

## Non-negotiable rules

1. **Never invent a number, material, test condition or citation.** If you did not read it in a source this session, the field is `value: null`, `confidence: "unknown"`, `sources: []`. Add a `note` saying what you looked for.
2. **Every non-null field needs at least one source** `{kind, url, note}`. `note` is a short paraphrase (max 400 chars), never a long quote.
3. **Confidence meanings.** `high`: a source states it directly. `medium`: stated for a group of investigations or combined from two statements. `low`: weak or indirect source. `inferred`: your own deduction (say so in `note`). `unknown`: no support.
4. **You cannot ask questions.** If something is ambiguous, pick `unknown` and record the ambiguity in `note` or `review.notes`.
5. **Stay in your lane's folder** (table below). Never edit `schema/`, `api/` or this file. If you need a schema change, append a request to `data/reports/schema-requests.md` and say so in your final message.
6. **Validate before you report done:** `.venv/bin/python3 scripts/validate.py YOUR_FILES` must print `OK` (system python3 has no jsonschema; always use the venv python). Fix and rerun until it does.
11. **PSI fields are set by script.** `psi_accession`, `in_psi`, `psi_url` and `project_type` are written by `scripts/psi_fill.py`, not by agents. Leave them as they are. Likewise `conditions.o2_percent`, `conditions.pressure_psi` and `conditions.airflow` are overwritten by `scripts/psi_apply_conditions.py` from the PSI experimental tables (`data/source/psi/tables/conditions.json`) when a table has those columns. Never hand-edit a field whose source is a PSI table.
12. **No clock.** You do not know the time. If a field needs a timestamp, run `date -u +%Y-%m-%dT%H:%M:%SZ` in the terminal and use its output.
7. **Units.** O2 in `%`, pressure in `psi`, gravity in `g` (microgravity = 0), airflow keeps the source unit in `unit`. If you convert, say so in `note`.
8. **Partial gravity.** The brief says PSI currently has no true partial-gravity combustion data. Never imply otherwise. E-FIELD Flames only *mimics* partial gravity electrically.
9. **Do not mix evidence.** Do not present Earth-gravity or ground-test numbers as microgravity PSI data. Mark such values with a note.
10. **Final message format:** one line per file written plus the validate result. No long recaps.

## Lanes and ownership

| Lane | Writes only to |
|---|---|
| orchestrator (parent) | `schema/`, `api/`, `AGENTS.md`, integration, `data/reports/decisions.md` |
| ingestion workers | `data/extracted/<id>.json` |
| verifier | `data/verified/<id>.json`, `data/reports/<id>.verify.json` |
| frontend workers | `web/src/features/<feature>/` (one feature per worker) |
| backend worker | `backend/` |
| writer | `docs/` |

## Ranking contract (frontend and backend must agree)

`score = 0.35*conditions + 0.25*function + 0.20*fuel + 0.20*evidence`, each part in 0..1. Computed deterministically in the backend; the LLM only phrases the explanation.

- **conditions**: mean of the per-dimension scores for O2, pressure, gravity, and airflow (airflow only if the scenario gives it). Per dimension: `1.0` if the investigation range overlaps the scenario range; `0.5` if the gap is at most 25% of the scenario span (for a point scenario, within 5% of the axis: 5 points of O2, 0.75 psi of pressure); otherwise `0.0`; unknown range: `0.3` and the dimension is added to `unknown_dims`. Special case: a scenario with partial gravity (0 < g < 1) against microgravity data scores `0.5` and is labelled "bounding" (the brief says micro-g and 1 g results could bound intermediate gravity).
- **function** (prevention / detection / suppression / any): `1.0` if the record's `safety_functions` contains the requested one or the request is "any"; `0.3` if the record is `fundamental` or unknown; else `0.0`.
- **fuel** (solid / gas / liquid_droplet / any): `1.0` match or "any"; `0.5` for `mixed`; `0.3` unknown; else `0.0`.
- **evidence**: `base * (0.5 + 0.5 * share_of_sourced_fields)` where base is `verified 1.0`, `extracted 0.6`, `seed 0.4`, `disputed 0.1`.

## Coverage contract

`/coverage` returns each record's ranges plus deterministic `gaps` per habitat (for example "no investigation has gravity overlapping 0.166 g", "no investigation with O2 >= 30% and pressure <= 10.2 psi") and `facts` taken from the brief (for example "no partial-gravity combustion data in PSI yet"). Gap text is computed in code, never invented by the LLM.

## Data reality (updated Nov 14, 07:30, from the PSI JSON API)

- PSI search returns 26 hits for "combustion". 24 have Research Area "Combustion Science" (matches the video). PSI-108 (Fluid Physics) and PSI-181 (Materials Science) are out of scope.
- Project Type matters: PSI-60, 62, 115, 117 and 142 are **Ground** investigations (Earth gravity). Never present their numbers as microgravity data (rule 9). Set `project_type` on every record.
- **Local PSI records are your first source.** `data/source/psi/<ACC>.json` (full detail: objective, approach, hypothesis, experimentHardware, projectType, flightProgram, researchImpacts, publications, file list `added`, `experimentalTable`) and `<ACC>.search.json` (NASA's search fields). Read them with the file tool. The seed id to accession map is `data/source/psi-map.json`. Rule 11 covers the PSI fields.
- `experimentalTable` and `factors` can be empty (all five Ground records). When empty, say so in `note` and leave conditions unknown unless another source states them.
- Data files are huge (ACME Flame Design and ACME CFI-G are about 2 TB each). Never download them. Record only file names, counts and sizes from the `added` list. Several records list 0 or 1 files (FLEX, FLEX-2, SAFFIRE-II, ACME E-FIELD, ACME BRE, ACME CLD, SLICE): do not claim data is available for them.
- PSI detail pages (`psi.nasa.gov/physci/repo/data/investigations/PSI-N`) are JavaScript pages: curl gets an empty shell, but the web extract tool can render them (seen in the dry run). Prefer the local JSON, which is the same data and reproducible. Never claim to have read a page you could not load.
- `experimentalTable` in each record points to a small CSV of per-test conditions. After `scripts/psi_tables.py` runs, it is at `data/source/psi/tables/ACC.csv` (ACC is the accession). Read it for oxygen, pressure and flow ranges before searching the web, and cite it as kind `psi` with the file name.
- The public S3 bucket `nasa-psi` holds no combustion data (`data/source/psi-notes.md`).
- Readable on the web: NASA investigation pages and PDFs, the ISS combustion Researcher's Guide, NTRS, journal DOIs (`data/source/resources.md`). Overview PDFs often omit test conditions (BASS states no O2 or pressure, airflow 5 to 50 cm/s only). Leave such fields unknown.
- `sofie`, `flare`, `bass-m`, `luci`, `fm2` have no PSI match yet. `daft` is PSI-47. FM2 has a lunar gravity value (about 1/6 g, from NASA's page) but no PSI data.

## Contingency for the Coverage Map

If fewer than 8 investigations end up with BOTH an oxygen range and a pressure range, switch the headline view from the O2 x pressure scatter to a **coverage matrix**: rows are investigations, columns are O2, pressure, gravity, airflow, fuel phase and safety function, and each cell is known (with source) or unknown. Keep the habitat comparison as a row of target values above the matrix, and keep computed gaps. The matrix is just as honest as the scatter and still answers "where does the evidence run out?". The orchestrator decides after reading `data/source/psi-notes.md` and records the choice in `data/reports/decisions.md`.
