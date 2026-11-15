# Frontend worker: Coverage Map (route: fast)

Feature folder: `web/src/features/coverage-map/` (write only here). Stack: React + TypeScript + Vite in `web/`. Use plain SVG or D3 for the chart; no heavy chart framework.
Read first: `AGENTS.md`, `api/openapi.yaml`, `data/fixtures/investigations.seed.json`, `data/fixtures/habitats.json`.

## What it shows
The headline view. Where the PSI data reaches, and where it does not, compared with the habitats crews will use.

- **Axes:** x = oxygen concentration (%), y = pressure (psi). Gravity as three facets/tabs: 0 g (microgravity), partial gravity (0 < g < 1), 1 g.
- **Investigations** are rectangles built from `conditions.o2_percent` and `conditions.pressure_psi`. A `null` bound extends to the axis edge and is drawn open-ended (gradient or dashed edge). Color by `family`, not by confidence.
- **Unplaced tray:** records with an unknown O2 or pressure range are listed under the chart with the missing dimension, never silently dropped or guessed.
- **Habitat zones** from `habitats.json` as shaded regions with labels (Earth air, spacesuit, Moon base, rover). A habitat with a null range is shown as a labelled band "not specified", not hidden.
- **Gap callouts:** render the strings from `/coverage` `gaps` and `facts` verbatim. Do not compute or reword gaps in the UI.
- **Detail drawer** on click or Enter: all fields with confidence badges, source links, and `review.status`.

## Data
Fetch `GET /coverage` and `GET /investigations/{id}`. Until the backend exists, read the fixtures through a small adapter in `web/src/api/` so swapping is one line.

## Quality bar
Keyboard operable; patterns or labels in addition to color; works at 360 px width; empty and error states.

## Done check
`cd web && npm run build` exits 0 and `npx tsc --noEmit` prints nothing. Report both results and a one-line description of what renders.
