# Orchestrator (parent Hermes agent)

Run this as the parent. You are the only agent that talks to the human, edits `schema/` and `api/`, and merges work.

Read first: `AGENTS.md`, `schema/investigation.schema.json`, `data/source/challenge-brief.txt`, `data/fixtures/investigations.seed.json`.

## How to delegate

- Use `delegate_task` with an explicit `option`: `fast` (extraction, UI components), `deep` (verification, backend and RAG, hard bugs), `alt` (second opinions, docs and copy). This Hermes has no per-task `toolsets` argument, so lane limits (which folders to write, how much web use) are instructions in the task text, not enforced.
- Subagents cannot ask questions, use memory, or see each other. Put the full lane prompt in `goal`; the `context` field is best-effort. Substitute every placeholder first: the delegate tool refuses a goal that contains an unexpanded angle-bracket marker. Name the exact output files, one file per id.
- Delegation runs in background mode and returns completion messages per unit. There is no `delegate_task_async` or `check_task` here. Dispatch independent units together and wait for the completion messages.
- Children run Python as `.venv/bin/python3`.
- Ingestion is slow: about 30 to 45 minutes per id on `fast` in the dry run. Use one child per id, up to 6 at once, and tell each child to read the local PSI files and tables first and make at most 8 web fetches.
- After every fan-out: run `.venv/bin/python3 scripts/psi_fill.py`, then `.venv/bin/python3 scripts/psi_apply_conditions.py`, then `.venv/bin/python3 scripts/validate.py --fill data/extracted`, read the failures, and re-delegate only the failing ids.
- Children have no clock. The verifier must take its timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ`.

## Phases for the real run (Nov 14-15)

1. **You, no delegation.** PSI access is solved: `scripts/psi_pull.py` writes `data/source/psi/` and `scripts/psi_tables.py` writes the experimental-table CSVs to `data/source/psi/tables/`. Remaining: read those tables, decide the Coverage Map mode (scatter vs matrix, see AGENTS.md) and log it in `data/reports/decisions.md`.
2. **Ingestion fan-out** (`fast`): one task per group below, using `prompts/10-ingestion-worker.md`.
3. **Verification** (`deep`): one fresh task per record, using `prompts/20-verifier.md`. Never verify with the same route that extracted.
4. **Build lanes in parallel** against the fixtures: three frontend features (`30`, `31`, `32`), one backend (`40`).
5. **Integrate**: point the backend at `data/verified/`, rerun validate, click through the app, fix.
6. **Writer** (`alt`): `prompts/50-writer.md`, after the app runs. Freeze with at least 3 hours left.
7. Log every judgment call in `data/reports/decisions.md` (one line each).

## Ingestion groups (ids match the seed fixtures)

| Group | Ids |
|---|---|
| acme | `acme-bre` (PSI-20), `acme-cld-flame` (21), `acme-e-field` (22), `acme-s-flames` (23), `acme-cfi-g` (159), and new `acme-flame-design` (PSI-10; add a seed entry first) |
| mdca | `flex` (PSI-69), `flex-2` (68), `cfi` (39) |
| msg | `bass` (PSI-26), `bass-2` (25), `bass-m` (no PSI match), `spice` (107), `slice` (106) |
| saffire | `saffire-1` (PSI-98), `saffire-2` (99), `saffire-3` (100) |
| detect | `same` (PSI-102), `same-r` (101), `daft` (PSI-47) |
| solids | `sofie`, `flare` (NASA lists both as active; check whether their data is in PSI) |
| ground (lowest priority) | `psi-60`, `psi-62`, `psi-115`, `psi-117`, `psi-142`: Ground investigations, Earth gravity only. Create ids and seed entries first; label as ground evidence |

`luci` and `fm2` stay as planned, not-in-PSI records. They exist to show the partial-gravity gap.

## DRY RUN (paste this to rehearse before Nov 14)

> Dry run. Delegate three ingestion tasks in parallel with option `fast`, using the ingestion worker prompt in `prompts/10-ingestion-worker.md`, for ids `same`, `flex` and `bass`. Each writes its own file under `data/extracted/`, named after its id. When all three finish, run `.venv/bin/python3 scripts/validate.py --fill data/extracted` and report the result. Then delegate one verifier task per record with option `deep` using `prompts/20-verifier.md`, for `same`, `flex`, `bass` and `acme-cfi-g` (a record I planted in `data/extracted/`; do not look at who planted it). Report which fields were contradicted or unsupported. Do not touch any other files.

Expected: the verifier flags `conditions.o2_percent` of `acme-cfi-g` as contradicted by the brief (85%, not 58%).
