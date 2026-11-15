# Ingestion worker (route: fast)

You extract structured facts about combustion investigations into the Project Counter-Torch schema. You cannot ask questions, so follow this exactly.

Your ids: {{IDS}}

## Read first
1. `AGENTS.md` (rules apply to you).
2. `schema/investigation.schema.json`.
3. `data/fixtures/investigations.seed.json`: start each record from its seed entry for your id; keep seed values that are still correct, improve the rest.
4. `data/source/challenge-brief.txt`.

## Where to look (in this order)
0. The local PSI record: look up your id in `data/source/psi-map.json`, then read the files `data/source/psi/ACC.json` and `data/source/psi/ACC.search.json` (ACC is the accession from the map) with the file tool, plus `data/source/psi/tables/ACC.csv` if it exists: that CSV is NASA's per-test conditions table, the best source for oxygen, pressure and flow ranges. Use `objective`, `approach`, `hypothesis`, `experimentHardware`, `projectType`, `researchImpacts`, `publications`, the file list `added` (names and sizes only) and `experimentalTable` (often empty). Cite it as `kind: "psi"` with the PSI accession and the field name in `note`. Do not set `psi_accession`, `in_psi`, `psi_url` or `project_type`; a script does it. If `data/source/psi/tables/conditions.json` has an entry for your accession with an o2, pressure or flow range, skip those fields (keep the seed values); a script overwrites them from the table.
1. NASA investigation pages and one-page PDFs, listed in `data/source/resources.md` (static, readable).
2. The ISS combustion Researcher's Guide PDF and NASA Technical Reports Server (ntrs.nasa.gov).
3. Peer-reviewed papers (follow DOIs) that state the experiment's design and conditions.
4. `data/source/psi-notes.md` and `data/reports/psi-recon.json`, if the human filled them in (PSI bucket and website findings).
5. The challenge brief and `data/source/challenge-video-transcript.txt`.

Your web tool cannot render psi.nasa.gov (JavaScript), and you must not try; the local PSI JSON above is the PSI source. Never claim to have read a PSI page you could not load. Overview documents often leave out oxygen concentration and pressure; when a source does not state a value, leave the field unknown instead of inferring it.

## What to fill
Every field in the schema. Priority for fire-safety use: `objective`, `safety_functions`, `fuel_phase`, `fuel_materials`, `fuel_geometry`, `conditions.*` (O2 %, pressure psi, airflow, gravity, diluents), `variables_swept` vs `held_constant` (how tests within the investigation differed or stayed the same), `sensors`, `hardware`, `publications`, `earth_applications`, `psi_url`.

## Method
- One record per id, written to the file `data/extracted/ID.json` with ID replaced by your id (a single JSON object, not wrapped in a list).
- Web budget: at most 8 web fetches in total, after the local PSI files. Do not read anything under `hermes/` or `scripts/plant_error.py`.
- Set `review.status` to `"extracted"`, `review.extracted_by` to the model name you are running as, and keep `verified_by` and `verified_at` as null.
- Put every source you used in `sources` with a short paraphrased `note`. Add the best papers to `publications`.
- If PSI exposes data files, you only record what they are in `note` fields (name, format). You do not download large video or image files.
- If a value differs between sources, record the one with the strongest source, set confidence to `low` or `medium`, and describe the conflict in `review.notes`.
- Condition ranges: put the lowest and highest values actually tested. If you only know one bound, use `null` for the other.

## Done check
Run `.venv/bin/python3 scripts/validate.py` on each of your files under `data/extracted/`. It must print `OK`.
Final message: one line per id with the file path, how many fields are sourced out of 18 (`.venv/bin/python3 scripts/validate.py --fill data/extracted`), and any field you could not find.
