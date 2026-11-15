2026-11-14 16:20 Coverage Map: matrix headline (only 5 of 24 combustion investigations have both O2 and pressure in PSI tables, 4 with known units); scatter of real test points as second panel. Tables: data/source/psi/tables/.


2026-11-14 16:07 Verification fan-out: 22 ids, one deep child per id, 4 concurrent (fast route 429s at 6). No 429 or timeout hit; no id retried. All 22 wrote data/verified/<id>.json + data/reports/<id>.verify.json; validate.py --fill data/verified prints OK.

2026-11-14 16:07 review.verified_by: daft and flex carried 'deepseek-ai/deepseek-v4.1-flash' copied from the placeholder in their task text; corrected to nvidia/nemotron-3-ultra-550b-a55b (what the other 20 records and the delegation metadata report, and the model the entire deep route ran on). Recorded in review.notes of both; no field value touched.

2026-11-14 16:07 scripts/diff_verified.py did not exist in the repo; written for this step. It diffs every sourced node AND every plain field between data/extracted and data/verified, excluding review.* (the review block is reported separately). The first version looked only at sourced nodes and silently missed hardware.shared_with edits.

2026-11-14 16:07 Verifier status semantics: the prompt says status is verified 'if nothing contradicted remains', which children read two ways. saffire-1 and acme-cfi-g corrected their contradicted field yet set disputed; saffire-3 reset two fields and set disputed. Left exactly as each verifier wrote it. NOTE for the backend: status feeds the evidence term (disputed 0.1 vs verified 1.0), so this choice moves scores - needs a human ruling.

2026-11-14 16:07 Scope deviations left in place (flagged, not reverted): slice, spice and saffire-1 removed an unsupported id from hardware.shared_with (list edit rather than reset); sofie capitalised one publication title (same URL); bass-m and flare gained null psi_accession/project_type keys that the extractor had omitted.

2026-11-15 06:15 Status rule: corrected/reset contradiction = verified, disputed only if conflict remains. Applied to acme-cfi-g, saffire-1, saffire-3.
2026-11-15 06:15 Moon-base zone: 66 of 930 PSI-table tests (PSI-10: 18, PSI-159: 48) have O2>=30% and pressure<=10.2 psi. Story = thin data from 2 gaseous-flame experiments, not no data. Initial conditions only, outcomes unknown.
