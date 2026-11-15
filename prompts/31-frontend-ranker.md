# Frontend worker: Scenario Ranker (route: fast)

Feature folder: `web/src/features/ranker/` (write only here). Stack: React + TypeScript + Vite.
Read first: `AGENTS.md` (ranking contract), `api/openapi.yaml`, `data/fixtures/habitats.json`.

## What it does
The user describes a scenario and gets investigations ranked by relevance, with the reasoning visible.

- **Inputs:** pick a habitat (prefills O2, pressure, gravity) or enter custom values; concern (prevention / detection / suppression / any); fuel (solid / gas / liquid droplet / any). Airflow optional.
- **Output:** ranked cards from `POST /rank`. Each card shows the total score, the four component bars (conditions, function, fuel, evidence) so the ranking is explainable, `unknown_dims` as chips ("airflow unknown"), the evidence badge (`verified` / `extracted` / `seed` / `disputed`), the `why` text, and source links.
- A "bounding" label appears when the API marks a partial-gravity scenario scored against microgravity data.
- Scenario state lives in the URL query string so a result can be shared.
- Show the API's `coverage_note` above results when present.

## Rules
Never recompute scores in the UI; display what the API returns. If a field the API returns is null, show "unknown", not a placeholder number.

## Data
`POST /rank`. Until the backend exists, use a mock adapter in `web/src/api/` that returns two or three hand-made items matching the OpenAPI response shape.

## Done check
`cd web && npm run build` exits 0 and `npx tsc --noEmit` prints nothing. Report both results.
