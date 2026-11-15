# Frontend worker: Compare and Lineage (route: fast)

Feature folder: `web/src/features/compare/` (write only here). Stack: React + TypeScript + Vite.
Read first: `AGENTS.md`, `schema/investigation.schema.json`, `api/openapi.yaml`.

## What it does
1. **Compare matrix.** Pick 2 to 4 investigations. Rows are the schema fields (objective, fuel phase, materials, geometry, O2, pressure, airflow, gravity, diluents, sensors, variables swept, held constant). Each row is marked **same** or **different** across the selection; unknown values are shown as "unknown" and never counted as a match. Highlight differences by default, with a toggle to show everything.
2. **Hardware lineage graph.** Nodes are investigations, grouped by `hardware.facility` (CIR, MSG, others); edges come from `hardware.shared_with`. Clicking a node adds it to the compare selection.
3. Each cell links to its sources and shows its confidence badge.

## Data
`GET /investigations`. Until the backend exists, read the fixtures through the adapter in `web/src/api/`.

## Quality bar
Matrix scrolls horizontally on narrow screens with a sticky first column; graph is keyboard navigable (list view fallback).

## Done check
`cd web && npm run build` exits 0 and `npx tsc --noEmit` prints nothing. Report both results.
