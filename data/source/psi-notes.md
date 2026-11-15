# PSI recon notes (the human fills this in; agents read it)

Fill in what you actually saw. Leave a line as "not checked" rather than guessing. Agents are told to trust this file over their own assumptions about PSI.

Date and time of recon:

## 1. S3 bucket (python3 scripts/psi_recon.py)
- Reachable from my machine? yes / no
- Combustion folders found (names):
- Folder pattern (investigation / sample / files):
- File types seen (csv, hdf5, mp4, png, pdf, ...):
- Approximate size of one sample folder:

## 2. PSI website (browser)
- Investigation page layout (objectives, approach, data folders, publications): as described in the challenge video
- Per-sample metadata with test conditions (O2 %, pressure, flow)? yes / no / only in some
- Which investigations have conditions as tabular data:
- Network tab check (DevTools, filter Fetch/XHR while loading the search page): JSON endpoint URL if any:

## 3. Decision
- Investigations with BOTH O2 % and pressure available: N of M
- Coverage Map mode: scatter (N >= 8) / matrix fallback (N < 8), see AGENTS.md
- Investigations I will ingest first (id list):

## Result (Nov 14, 06:47 local)
S3 bucket nasa-psi top level: DSI/, OASIS/, pk4/, index.html. No combustion folders. Combustion data is not in this bucket.
