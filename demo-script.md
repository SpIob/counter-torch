# Project Counter-Torch: 2-minute demo script

Screen recording, one take, about 2:00 at a calm speaking pace. The narration is written to be read aloud in the first person. Nothing in it depends on which investigation ranks first; read what the screen shows.

## Before recording

Run these checks, because the script assumes them.

1. Start the backend and the web app, then open the Coverage tab. The first screen must show three figures and the scatter plot, with the amber Moon-base zone and its label pill.
2. Scroll once to confirm that the gap list and the table appear, then scroll back to the top.
3. In the Ask tab, type the two questions below and confirm what each returns. If the second question does not refuse, replace it with another question the records cannot answer, and keep the refusal on screen.
4. Note whether Ask runs in live or offline mode (the response carries a `mode` field) and say the correct one in the 1:35 segment.
5. Use a 1280 by 720 or larger window, and reload the page so the chart animation plays on camera.

## Script

| Time | On screen | Narration |
|---|---|---|
| 0:00 | Coverage tab, chart animating in | "On Earth a flame rises. In microgravity it does not, and NASA has run experiments on what that does to fire. My question was a practical one: for the places crews will actually live, where does that evidence run out?" |
| 0:15 | Hover a few dots; point to the amber Moon-base zone | "Each dot is one test from NASA's experimental tables, 930 in all from four investigations. The amber zone is the Moon-base atmosphere, 30% oxygen or more at 10.2 psi or less. Sixty-six tests land inside it, and every one comes from the two ACME gaseous-flame experiments." |
| 0:35 | Scroll down to the gap list | "Scrolling shows the gaps. Code computes these from the records; no model writes them. This one says that no PSI investigation covers lunar gravity, 0.166 g. Only a seed record lists it, and it has no data in PSI yet." |
| 0:50 | Scroll to the table, open one row so the drawer slides in | "Every row has sources, and every value carries a confidence level. An unknown stays unknown." |
| 1:00 | Ranker tab, Moon base preset selected, results shown | "In the Ranker I choose the Moon base and a safety function. The score is fixed: 35% conditions, 25% function, 20% fuel and 20% evidence quality. Partial gravity is scored against microgravity data and labelled as a bounding estimate, so the tool never pretends it has lunar-gravity results." Expand the top result's breakdown while speaking. |
| 1:25 | Ask tab, type: "What fuels does ACME CFI-G use?" | "Ask answers from the loaded records only, and each answer cites its source." |
| 1:35 | Ask tab, type the second question | "When the records do not cover a question, it says so and stops." |
| 1:45 | Compare tab, SAFFIRE I, II and III already selected | "Last, Compare. These three SAFFIRE experiments share hardware, and the view shows only the fields where they differ. An unknown value never counts as a match." |
| 1:55 | Return to the top of Coverage | "Project Counter-Torch does not say what is safe. It shows where the evidence ends." |

## Questions for the Ask segment

- Answerable: "What fuels does ACME CFI-G use?" The verified record lists propane, butane and ethane.
- Refusal: "What is the flame spread rate of cotton fabric at lunar gravity?" Confirm in rehearsal that it refuses.

## 30-second cut

Use this version if the submission form asks for a video of 30 seconds or less.

| Time | On screen | Narration |
|---|---|---|
| 0:00 | Coverage chart animating | "Project Counter-Torch shows where NASA's microgravity fire data runs out." |
| 0:07 | Moon-base zone on the chart | "Of 930 tests, 66 match a Moon-base atmosphere, and none were run at lunar gravity." |
| 0:15 | Ranker result with breakdown | "Every ranking shows its score, its sources and its confidence." |
| 0:22 | Ask refusal | "When the records are silent, the app says so." |
