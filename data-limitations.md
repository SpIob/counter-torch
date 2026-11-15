# Project Counter-Torch: data limitations

Project Counter-Torch reports on what NASA's PSI repository contains today, and PSI has gaps. This document lists the ones that affect how far the app can be trusted. Each statement matches the loaded data.

## No true partial-gravity data

The challenge brief states that PSI currently holds no true partial-gravity combustion data. Lunar gravity is about 0.166 g and Mars gravity is about 0.38 g, so neither habitat has a matching experiment. The app reflects this in three ways. The Coverage gaps say so. The Ranker scores a partial-gravity scenario against microgravity data and labels the result a bounding estimate, because microgravity and normal-gravity results could bound what happens in between. And ACME E-FIELD Flames, which used an electric field on flame ions to mimic partial gravity, is treated as a mimic and not as partial-gravity data.

FM2 is the only record that lists lunar gravity, and it has no data in PSI.

## Records: verified, extracted and seed

| Status | Records | Meaning |
|---|---|---|
| Verified | 22 | A second model checked the record against its sources, and corrections were applied |
| Extracted | 0 | Written by the extraction model and not yet verified |
| Seed | 2 (FM2 and LUCI) | Built from the challenge brief and NASA's PSI list; not extracted or verified |

The verifier changed 11 fields across 8 records; the details are in `docs/ai-disclosure.md`. Verified means the record was checked by a model and reviewed by me. It does not mean a NASA scientist has confirmed it.

## Test points in the scatter

The Coverage scatter draws 930 tests from four investigations: PSI-10 (316), PSI-159 (333), PSI-69 (273) and PSI-68 (8). Several limits apply.

- Only investigations whose experimental tables list both oxygen and pressure can appear. Twenty-five tables were downloaded, and five investigations had both columns.
- PSI-39 has both columns, but its pressure unit is not stated, so it is left out rather than guessed.
- The points are initial conditions only. Conditions that change during a test are not plotted.
- Values that are impossible, such as data-entry errors, were dropped. This affected PSI-20.
- Sixty-six of the 930 tests fall in the Moon-base zone (30% oxygen or more, 10.2 psi or less): 18 from PSI-10 and 48 from PSI-159. PSI-68 and PSI-69 contribute none. All 66 come from two gaseous-flame experiments, and none come from the droplet experiments FLEX and FLEX-2.

## Unknown values

An unknown value is left empty, with confidence "unknown", and the app shows it as unknown.

- Oxygen, pressure and airflow ranges for 16 records come from NASA's tables. The other records rely on documents, and many of those state no test conditions. BASS, for example, states an airflow of 5 to 50 cm/s and no oxygen or pressure.
- The oxygen range for PSI-23 is approximate.
- SAFFIRE-III's airflow and diluents were reset to unknown by the verifier.
- Several records list zero or one files in PSI (FLEX, FLEX-2, SAFFIRE-II, ACME E-FIELD, ACME BRE, ACME CLD and SLICE). The app does not claim that data is available for them.
- Five records (SOFIE, FLARE, BASS-M, LUCI and FM2) had no PSI match when the records were built. The app marks records by whether they have PSI data.
- Five Ground investigations (PSI-60, 62, 115, 117 and 142) are not loaded. They are Earth-gravity tests and would need to be labelled as such.
- The ranges in the table view are ranges across a whole investigation. A range that overlaps a habitat does not mean any single test matched it; that is why the app also counts individual tests.

## What the ranking does not claim

The Ranker answers one question: which loaded investigations are most relevant to this scenario, and how well sourced are they? Its score combines the overlap of conditions (35%), the safety function (25%), the fuel phase (20%) and the quality of the evidence (20%). It does not do any of the following.

- It does not predict flame spread, ignition or extinguishment in any habitat.
- It does not rate a material, design or atmosphere as safe.
- It does not combine results from different investigations into a new finding.
- It does not treat a bounding estimate as a measurement.
- It does not use a language model. The score and its explanation come from fixed rules in the backend.

A high score means the evidence is close to the scenario and well documented. It says nothing about how dangerous the scenario is.

## Ask view limits

Ask retrieves passages from the loaded records and the challenge brief. It refuses when too few passages match the question, but a question that shares common words with the records may still return loosely related passages. Each answer lists its citations so that the reader can check them. When a language model is configured, it may rephrase the retrieved passages; it is instructed to use only those passages, and I have not measured how well it follows that instruction.

## Where PSI itself may differ

The loaded data is a snapshot of PSI as read on Nov 14, 2026. No data files were downloaded; the app uses record fields, file lists and the small experimental tables only. Changes made to PSI after that date will not appear until the data is refreshed.
