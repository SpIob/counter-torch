# Project Counter-Torch

On Earth, a flame rises and flickers because hot gas floats upward. Aboard a spacecraft nothing floats, and the same fuel can burn as a rounded flame with its own behavior. NASA has spent decades studying that difference; the hard part now is finding what those studies actually cover.

Project Counter-Torch is a web dashboard for the NASA Space Apps challenge "Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data". It loads 24 investigation records built from NASA's Physical Sciences Informatics (PSI) repository, where Combustion Science lists 24 investigations, and from related NASA pages, and it shows where the evidence reaches, and where it stops, for the places crews will live.

## The problem

PSI holds microgravity combustion experiments, but the investigations are spread across many records, hardware programs and terabytes of files, so a fire-safety engineer cannot quickly tell which experiments apply to a given habitat. Planned Moon habitats are expected to use 30% oxygen or more at 10.2 psi or less, and lunar gravity is about 0.166 g, a condition PSI does not currently cover. The question this project answers is simple to state: for a given scenario, which investigations are relevant, how strong is the evidence, and what does nobody know yet?

## What it does

The app has four views. Each one exists in the repository and runs against the loaded records.

**Coverage.** The first screen shows three summary figures and a scatter plot of oxygen against pressure. The plot draws 930 individual tests from four investigations (PSI-10, PSI-68, PSI-69 and PSI-159), using the initial conditions listed in NASA's experimental tables. The Moon-base zone is drawn on top; 66 of the 930 tests fall inside it, all of them from the two ACME gaseous-flame experiments. Scrolling reveals the gaps, written by code and not by a model, and a table of all 24 investigations with oxygen, pressure, gravity, airflow, fuel and safety function. Each cell shows how confident the record is in that value, and selecting a row opens its sources.

**Ranker.** The user picks a scenario (the default is the Moon base), a safety function (prevention, detection or suppression) and a fuel type, or edits the values directly. The backend scores every investigation with a fixed formula: 35% conditions, 25% safety function, 20% fuel phase and 20% evidence quality. Each result expands to show the four parts and the sources behind them. Partial-gravity scenarios are scored against microgravity data and labelled as bounding estimates.

**Compare.** The user selects investigations and sees only the fields where they differ. An unknown value never counts as a match. The view also suggests investigations that share hardware with the current selection.

**Ask.** The user asks a question in plain language. The app retrieves matching passages from the loaded records, shows them as cited cards, and refuses to answer when the records do not cover the question.

## How it uses AI

AI did three separate jobs, and each one had a check.

- **Extraction.** One agent per investigation, running DeepSeek V4.1 Flash through the Hermes agent framework, read the local PSI records and wrote a structured record in which every value carries a confidence level and at least one source. A value that no source supported stays empty.
- **Verification.** A different model, NVIDIA Nemotron 3 Ultra 550B, re-checked all 22 extracted records against their sources. It changed 11 fields across 8 records and caught an error that I planted in a rehearsal run.
- **Building.** Claude wrote the backend and the web app in a Claude Code session under my direction.

At runtime the numbers are deterministic. Ranking, gaps and zone counts are computed in code. A language model is optional and used only in the Ask view, where it may rewrite retrieved passages into an answer; with no model configured, Ask returns the retrieved passages themselves. A full account is in `docs/ai-disclosure.md`.

## Who it is for

The tool is meant for people who plan for fire in crewed habitats: researchers choosing which microgravity results to trust, engineers sizing up a Moon or Mars atmosphere against existing data, and reviewers who need to see why a result was ranked where it was. It does not replace a safety analysis.

## What is verified and what is not

Of the 24 records, 22 were verified against their sources and 2 (FM2 and LUCI) remain seed records built from the challenge brief. Oxygen, pressure and airflow ranges for 16 records were written by script from NASA's experimental tables, with no model involved. Several values stay unknown, and the app shows them as unknown instead of guessing. Five Ground investigations (PSI-60, 62, 115, 117 and 142) were not loaded, and PSI-39 was left out of the scatter because its pressure unit is missing. The ranking measures how relevant and well sourced the evidence is. It does not predict whether a fire will spread, and it does not rate any material or design as safe. The full list is in `docs/data-limitations.md`.

A tool that says where the evidence ends is more useful to a safety engineer than one that never admits it has.
