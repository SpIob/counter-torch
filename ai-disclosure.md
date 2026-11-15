# Project Counter-Torch: AI disclosure

The NASA Space Apps submission guide asks teams to say where and how AI tools were used. This document does that, and it states only what the repository, the run logs and the verifier reports show. I worked alone; every AI contribution below was assigned and reviewed by me.

## Summary

| Lane | Model or tool | Job |
|---|---|---|
| Ingestion | DeepSeek V4.1 Flash (`deepseek-ai/deepseek-v4.1-flash`, route `fast`) through the Hermes agent framework | Read local PSI records and wrote one structured record per investigation |
| Verification | NVIDIA Nemotron 3 Ultra 550B (`nvidia/nemotron-3-ultra-550b-a55b`, route `deep`) through Hermes | Re-checked each extracted record against its sources |
| Backend and web app | Claude, in a Claude Code session | Wrote the FastAPI backend, the React app, the tests and the interface copy |
| Writing | Claude | Drafted the four documents in `docs/` from the repository, in the voice and style I specified |
| Not used | GLM 5.3 Flash (route `alt`) | Configured for docs and second opinions, but no work was assigned to it |

The exact version of Claude that wrote the app is not recorded in the repository. The Hermes routes are defined in `hermes/delegation.snippet.yaml`.

## Ingestion

Hermes started one child agent per investigation, working from the local PSI JSON records and the experimental-table files. Each agent wrote `data/extracted/<id>.json` under the schema in `schema/investigation.schema.json`. Three rules governed every agent. A value must be backed by a source, or it stays null with confidence "unknown". Confidence is one of high, medium, low, inferred or unknown. No agent may fill a field it could not read in a source.

At high concurrency the provider returned HTTP 429 errors, so I reduced concurrency to four.

## Work done by script, not by a model

Oxygen, pressure and airflow ranges for 16 records come from NASA's experimental tables. `scripts/psi_table_summary.py` computes the ranges and `scripts/psi_apply_conditions.py` writes them into the records, with the CSV file named as the source. The PSI accession number, the in-PSI flag and the project type are written by `scripts/psi_fill.py`. The 930 test points in the Coverage scatter come from `scripts/psi_points.py`. The ranking, the coverage gaps and the Moon-zone counts are computed in the backend; no language model produces them.

## Verification

A separate agent on a different model (Nemotron, not DeepSeek) checked each of the 22 extracted records against the same sources and wrote `data/verified/<id>.json` plus a report in `data/reports/`. All 22 records passed schema validation afterwards.

The verifier changed 11 fields across 8 records:

- ACME CFI-G: the fuel list was corrected from propane, n-butane and n-pentane to propane, butane and ethane.
- ACME CLD Flame: the airflow range was narrowed from 10 to 50 cm/s to 10 to 40 cm/s and marked inferred, and the confidence on the oxygen range was lowered from medium to inferred.
- ACME E-FIELD: the confidence on gravity was raised from medium to high.
- SAFFIRE-I, SLICE and SPICE: the `shared_with` hardware lists were trimmed.
- SAFFIRE-III: airflow and diluents were reset to unknown.
- SOFIE: the maximum pressure was corrected from 14.7 to 15.7 psi, and a publication title was capitalized.

In a rehearsal run before the build, the verifier also caught an oxygen error that I had planted on purpose in the BASS record.

The verifier marked three records (ACME CFI-G, SAFFIRE-I and SAFFIRE-III) as disputed. I ruled that a contradiction which was corrected or reset counts as verified, and that "disputed" applies only while a conflict remains. All three were set to verified under that rule.

Two problems appeared along the way. The first verification instructions named the extractor model as the verifier, and two records (DAFT and FLEX) copied it; I corrected both files to Nemotron. And I checked SOFIE's 15.7 psi figure myself: it has two real sources (an NTRS document and a university article), so it stands with low confidence.

## What a human reviewed

- I reviewed the verifier's diff for every changed field and ran validation on all records.
- I made the three status rulings above and checked the SOFIE pressure.
- I directed the interface design, and I rejected the first version of it. The current layout, the space background, the flame logo and the scroll transition on the Coverage tab follow my feedback.
- I asked for the Moon-zone check on the real test points and read its result before the figures went into the app and these documents.

I did not independently re-read every source for all 24 records. Verification of values rests on the verifier model plus the script-derived ranges.

## Preparation before the event

The repository began as a starter kit with the schema, seed records taken from the challenge brief and NASA's PSI list, the agent prompts and the Hermes routing. The dated patches in the README log are all from Nov 14 onward, and the application, the extraction, the verification and these documents were produced during the hackathon.

## Where AI use shows in the project

- Each record in `data/verified/` names the verifier model in its review block.
- The app reports in every Ask response whether it ran in live or offline mode. In offline mode no language model is called.
- Only the Ask view can call a model at runtime, and only to rephrase retrieved passages. The ranking, the gaps and the zone counts never call one.
- The interface has no AI-generated images. The flame logo is hand-built SVG, and the app uses no NASA logos or mission marks.
